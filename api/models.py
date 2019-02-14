import datetime
import uuid

from api import app

import peewee

db = peewee.SqliteDatabase(None)


# The base model the other models extend, used to force all other models to use the same database
class BaseModel(peewee.Model):
    class Meta:
        database = db


class Tracker(BaseModel):
    ip = peewee.CharField()
    name = peewee.CharField()

    def to_dict(self):
        output_dict = {
            "ip": self.ip,
            "name": self.name,
        }

        return output_dict


class Peer(BaseModel):
    ip = peewee.CharField()
    uuid = peewee.UUIDField()
    keep_alive_timestamp = peewee.DateTimeField(default=datetime.datetime.now)

    def to_dict_simple(self):
        output_dict = {
            "ip": self.ip,
        }

        return output_dict


class File(BaseModel):
    name = peewee.CharField()
    full_hash = peewee.CharField()

    def to_dict_simple(self):
        output_dict = {
            "id": self.id,
            "name": self.name,
            "full_hash": self.full_hash,
        }

        return output_dict


class Chunk(BaseModel):
    chunk_id = peewee.IntegerField()
    chunk_hash = peewee.CharField()
    name = peewee.CharField()
    parent_file = peewee.ForeignKeyField(File, backref="chunks", on_delete='cascade', on_update='cascade')

    def to_dict(self):
        output_dict = {
            "id": self.chunk_id,
            "chunk_hash": self.chunk_hash,
            "name": self.name,
        }

        return output_dict


class Hosts(BaseModel):
    hosted_file = peewee.ForeignKeyField(File, backref='hosted_file', on_delete='cascade', on_update='cascade')
    hosting_peer = peewee.ForeignKeyField(Peer, backref='hosting_peer', on_delete='cascade', on_update='cascade')

    class Meta:
        indexes = (
            # Specify a unique multi-column index on hosted_file/hosting_peer
            (('hosted_file', 'hosting_peer'), True),
        )


def load_database(db_path):
    db.init(db_path)

    if(not db_path.is_file()):
        create_tables()


def create_tables():
    with db:
        db.create_tables([Tracker, Peer, File, Chunk, Hosts])


# returns the tracker table from the database as a dict in the specified output format
def get_tracker_list():
    success = True
    tracker_list_response = {
        "success": success,
        "trackers": [],
    }

    try:
        tracker_list_query = Tracker.select()
        if(not tracker_list_query.exists()):
            raise Tracker.DoesNotExist

        for tracker in Tracker.select():
            tracker_list_response["trackers"].append(tracker.to_dict())
    except Tracker.DoesNotExist:
        error = "No other trackers known to this one"
        success = False
    except Exception as e:
        error = str(e)
        success = False

    if(not success):
        tracker_list_response = {
            "success": success,
            "error": error,
        }

    return tracker_list_response


# returns the file list on the tracker as a dict in the specified output format
# TODO: only return files that have a recent timestamped peer
def get_file_list():
    success = True
    file_list_response = {
        "success": success,
        "files": [],
    }

    try:
        file_list_query = File.select()
        if(not file_list_query.exists()):
            raise File.DoesNotExist

        for file in file_list_query:
            file_list_response["files"].append(file.to_dict_simple())
    except File.DoesNotExist:
        error = "No files listed on tracker"
        success = False
    except Exception as e:
        error = str(e)
        success = False

    if(not success):
        file_list_response = {
            "success": success,
            "error": error,
        }

    return file_list_response


# returns the data for a specific file
def get_file(file_id):
    success = True
    get_file_response = {
        "success": success,
        "name": None,
        "full_hash": None,
        "chunks": [],
        "peers": [],
    }

    try:
        file_query = File.select(File.name, File.full_hash).where(File.id == file_id).get()
        get_file_response["name"] = file_query.name
        get_file_response["full_hash"] = file_query.full_hash

        chunk_query = Chunk.select(Chunk.chunk_id, Chunk.chunk_hash, Chunk.name)\
            .join(File, on=(File.id == Chunk.parent_file))\
            .where(File.id == file_id)

        peer_query = Peer.select(Peer.ip)\
            .join(Hosts, on=(Peer.id == Hosts.hosting_peer))\
            .join(File, on=(File.id == Hosts.hosted_file))\
            .where(File.id == file_id)

        for chunk in chunk_query:
            get_file_response["chunks"].append(chunk.to_dict())

        for peer in peer_query:
            get_file_response["peers"].append(peer.to_dict_simple())

    except File.DoesNotExist:
        error = "File with id {} does not exist".format(file_id)
        success = False
    except Chunk.DoesNotExist:
        error = "File is invalid, has no chunks"
        success = False
    except Peer.DoesNotExist:
        error = "File has no hosting peers"
        success = False
    except Exception as e:
        error = str(e)
        success = False

    if(not success):
        get_file_response = {
            "success": success,
            "error": error,
        }

    return get_file_response


# TODO: need to check if chunk hashes match if the file already exists
#       shouldnt be adding chunks to existing files
def add_file(add_file_data, peer_ip):
    success = True
    add_file_response = {
        "success": success,
        "file_id": None,
        "guid": None,
    }

    try:
        # if client has no guid, add them as a peer and generate a guid
        # else get the peer
        if(add_file_data["guid"] is None):
            peer = add_peer(peer_ip)
        else:
            peer = Peer.get(Peer.uuid == add_file_data["guid"])
            if(peer.ip != peer_ip):
                peer.ip = peer_ip
                peer.save()

        # add the file to the db (or create new one if it didn't exist)
        new_file, file_created = File().get_or_create(
            full_hash=add_file_data["full_hash"],
            defaults={"name": add_file_data["name"]},
        )

        # if the file doesn't exist, add the chunks to the db and associate them with the file
        if(file_created):
            for chunk_data in add_file_data["chunks"]:
                Chunk().create(
                    chunk_id=chunk_data["id"],
                    name=chunk_data["name"],
                    chunk_hash=chunk_data["hash"],
                    parent_file=new_file,
                )

        # TODO: if the file does exist, check that the submitted chunks match the existing chunks

        # add relationship for the file and client (if a relationship does not already exist)
        Hosts().get_or_create(
            hosted_file=new_file,
            hosting_peer=peer,
        )

        add_file_response["file_id"] = new_file.id
        add_file_response["guid"] = peer.uuid

    except Peer.DoesNotExist:
        error = "Peer with guid {} does not exist".format(add_file_data["guid"])
        success = False
    except Exception as e:
        error = str(e)
        success = False

    if(not success):
        add_file_response = {
            "success": success,
            "error": error,
        }

    return add_file_response


# creates a new peer with a random guid
def add_peer(peer_ip):
    peer_uuid = uuid.uuid4()

    new_peer = Peer.create(
        ip=peer_ip,
        uuid=peer_uuid,
    )

    return new_peer


# updates the timestamp and ip for the peer
def keep_alive(keep_alive_data, peer_ip):
    success = True
    keep_alive_response = {
        "success": success,
    }

    try:
        peer = Peer.get(Peer.uuid == keep_alive_data["guid"])
        if(peer.ip != peer_ip):
            peer.ip = peer_ip
        peer.keep_alive_timestamp = datetime.datetime.now()
        peer.save()
    except Peer.DoesNotExist:
        error = "Peer with guid {} does not exist".format(keep_alive_data["guid"])
        success = False
    except Exception as e:
        error = str(e)
        success = False

    if(not success):
        keep_alive_response = {
            "success": success,
            "error": error,
        }

    return keep_alive_response


# removes a peer from the hosts list of a file
# if the file has no hosts remaining, removes it
def deregister_file(deregister_file_data):
    success = True
    deregister_file_response = {
        "success": success,
    }

    try:
        host_relationship = Hosts.select()\
            .join(File, on=(File.id == Hosts.hosted_file))\
            .join(Peer, on=(Peer.id == Hosts.hosting_peer))\
            .where(Peer.uuid == deregister_file_data["guid"] and File.id == deregister_file_data["file_id"]).get()
        host_relationship.delete_instance()

        try:
            Hosts.get(Hosts.hosted_file == deregister_file_data["file_id"])
        except Hosts.DoesNotExist:
            File.get(File.id == deregister_file_data["file_id"]).delete_instance()

    except Hosts.DoesNotExist:
        error = "No peer with guid {} is currently hosting file with id {}"\
            .format(deregister_file_data["guid"], deregister_file_data["file_id"])
        success = False
    except Exception as e:
        error = str(e)
        success = False

    if(not success):
        deregister_file_response = {
            "success": success,
            "error": error,
        }

    return deregister_file_response


# Decorators to explicitly manage connections
# These functions should maybe not be in this file? I'm not sure
@app.before_request
def before_request():
    db.connect()


@app.after_request
def after_request(response):
    db.close()
    return response
