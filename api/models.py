import datetime
from io import StringIO
from operator import itemgetter
import uuid

from api import app, constants
import peewee
from peewee import DoesNotExist, fn, SqliteDatabase

db = SqliteDatabase(None)


# The base model the other models extend, used to force all other models to use the same database
class BaseModel(peewee.Model):
    class Meta:
        database = db


class Tracker(BaseModel):
    ip = peewee.CharField(unique=True)


class Peer(BaseModel):
    ip = peewee.CharField()
    uuid = peewee.UUIDField()
    keep_alive_timestamp = peewee.DateTimeField(default=datetime.datetime.min)
    expected_seq_number = peewee.IntegerField(default=0)
    ka_expected_seq_number = peewee.IntegerField(default=0)

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

    def to_dict_full(self, peer_count):
        output_dict = {
            "id": self.id,
            "name": self.name,
            "full_hash": self.full_hash,
            "active_peers": peer_count,
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
    db.init(str(db_path))

    if(not db_path.is_file()):
        create_tables()


def create_tables():
    with db:
        db.create_tables([Tracker, Peer, File, Chunk, Hosts])


# returns the tracker table from the database as a list of dicts
def get_tracker_list():
    trackers = Tracker.select()
    if not trackers.exists():
        raise Tracker.DoesNotExist

    return list(trackers.dicts())


# returns the file list on the tracker as a dict in the specified output format
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

        timeout_time = datetime.datetime.now() - constants.KEEP_ALIVE_TIMEOUT
        for file in file_list_query:
            try:
                peer_query = Peer.select(fn.COUNT(Peer.id).alias("peer_count"))\
                    .join(Hosts, on=(Peer.id == Hosts.hosting_peer))\
                    .join(File, on=(File.id == Hosts.hosted_file))\
                    .where((File.full_hash == file.full_hash) &
                           (Peer.keep_alive_timestamp >= timeout_time))\
                    .get()

                file_list_response["files"].append(file.to_dict_full(peer_query.peer_count))
            except Exception:
                pass

        if(len(file_list_response["files"]) <= 0):
            raise Exception("No peers listed for any file on tracker")

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

        timeout_time = datetime.datetime.now() - constants.KEEP_ALIVE_TIMEOUT
        peer_query = Peer.select(Peer.ip)\
            .join(Hosts, on=(Peer.id == Hosts.hosting_peer))\
            .join(File, on=(File.id == Hosts.hosted_file))\
            .where((File.id == file_id) &
                   (Peer.keep_alive_timestamp >= timeout_time))

        if(len(peer_query) == 0):
            raise Exception("File has no hosting peers currently online")

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


# returns the data for a specific file hash
def get_file_by_hash(file_full_hash):
    success = True
    get_file_by_hash_response = {
        "success": success,
        "name": None,
        "full_hash": None,
        "chunks": [],
        "peers": [],
    }

    try:
        file_query = File.select(File.name, File.full_hash).where(File.full_hash == file_full_hash).get()
        get_file_by_hash_response["name"] = file_query.name
        get_file_by_hash_response["full_hash"] = file_query.full_hash

        chunk_query = Chunk.select(Chunk.chunk_id, Chunk.chunk_hash, Chunk.name)\
            .join(File, on=(File.id == Chunk.parent_file))\
            .where(File.full_hash == file_full_hash)

        timeout_time = datetime.datetime.now() - constants.KEEP_ALIVE_TIMEOUT
        peer_query = Peer.select(Peer.ip)\
            .join(Hosts, on=(Peer.id == Hosts.hosting_peer))\
            .join(File, on=(File.id == Hosts.hosted_file))\
            .where((File.full_hash == file_full_hash) &
                   (Peer.keep_alive_timestamp >= timeout_time))

        if(len(peer_query) == 0):
            raise Exception("File has no hosting peers currently online")

        for chunk in chunk_query:
            get_file_by_hash_response["chunks"].append(chunk.to_dict())

        for peer in peer_query:
            get_file_by_hash_response["peers"].append(peer.to_dict_simple())

    except File.DoesNotExist:
        error = "File with hash {} does not exist".format(file_full_hash)
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
        get_file_by_hash_response = {
            "success": success,
            "error": error,
        }

    return get_file_by_hash_response


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
        if(len(add_file_data["chunks"]) <= 0):
            raise Exception("File is invalid, has no chunks")

        # if client has no guid, add them as a peer, generate a guid, and set their sequence number
        # else get the peer
        if(add_file_data["guid"] is None):
            peer = add_peer(peer_ip)
            peer.expected_seq_number = add_file_data["seq_number"]
        else:
            peer = Peer.get(Peer.uuid == add_file_data["guid"])
            if(peer.ip != peer_ip):
                peer.ip = peer_ip
                peer.save()

        if(peer.expected_seq_number != add_file_data["seq_number"]):
            raise Exception("Tracker is expecting sequence number {} (sequence number {} was sent)"
                            .format(peer.expected_seq_number, add_file_data["seq_number"]))

        # add the file to the db (or create new one if it didn't exist)
        new_file, file_created = File().get_or_create(
            full_hash=add_file_data["full_hash"],
            defaults={"name": add_file_data["name"]},
        )

        # if the file doesn't exist, add the chunks to the db and associate them with the file
        if(file_created):
            for chunk_data in sorted(add_file_data["chunks"], key=itemgetter('id')):
                Chunk().create(
                    chunk_id=chunk_data["id"],
                    name=chunk_data["name"],
                    chunk_hash=chunk_data["hash"],
                    parent_file=new_file,
                )

            # add relationship for the file and client
            Hosts().create(
                hosted_file=new_file,
                hosting_peer=peer,
            )
        else:
            # if the file does exist, check that the submitted chunks match the existing chunks
            chunk_query = Chunk.select(Chunk.chunk_id, Chunk.chunk_hash, Chunk.name)\
                            .join(File, on=(File.id == Chunk.parent_file))\
                            .where(File.full_hash == add_file_data["full_hash"])

            if(len(chunk_query) != len(add_file_data["chunks"])):
                raise Exception("File invalid, chunks do not match tracker version")

            for chunk_data, chunk_query_data in\
                    zip(sorted(add_file_data["chunks"], key=itemgetter('id')), chunk_query):
                if((chunk_data["id"] != chunk_query_data.chunk_id) or
                   (chunk_data["name"] != chunk_query_data.name) or
                   (chunk_data["hash"] != chunk_query_data.chunk_hash)):
                    raise Exception("File invalid, chunks do not match tracker version")

            # add relationship for the file and client (if a relationship does not already exist)
            # else error
            _, host_created = Hosts().get_or_create(
                hosted_file=new_file,
                hosting_peer=peer,
            )

            if(not host_created):
                raise Exception("Peer with guid {} (you) is already hosting this file".format(add_file_data["guid"]))

        # increment the peer's expected seq number
        peer.expected_seq_number += 1
        peer.save()

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

        if(peer.ka_expected_seq_number != keep_alive_data["ka_seq_number"]):
            raise Exception("Tracker is expecting keep_alive sequence number {} (sequence number {} was sent)"
                            .format(peer.ka_expected_seq_number, keep_alive_data["ka_seq_number"]))

        # update ip, increment the peer's expected keep_alive seq number
        if(peer.ip != peer_ip):
            peer.ip = peer_ip
        peer.keep_alive_timestamp = datetime.datetime.now()
        peer.ka_expected_seq_number += 1
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
def deregister_file(deregister_file_data, peer_ip):
    success = True
    deregister_file_response = {
        "success": success,
    }

    try:
        # check if peer with guid exists, if so updates the peer's ip and timestamp
        peer = Peer.get(Peer.uuid == deregister_file_data["guid"])
        if(peer.ip != peer_ip):
            peer.ip = peer_ip
        peer.keep_alive_timestamp = datetime.datetime.now()
        peer.save()

        if(peer.expected_seq_number != deregister_file_data["seq_number"]):
            raise Exception("Tracker is expecting sequence number {} (sequence number {} was sent)"
                            .format(peer.expected_seq_number, deregister_file_data["seq_number"]))

        # checks if specified peer is hosting specified file, if so deletes the record
        host_relationship = Hosts.select()\
            .join(File, on=(File.id == Hosts.hosted_file))\
            .join(Peer, on=(Peer.id == Hosts.hosting_peer))\
            .where(Peer.uuid == deregister_file_data["guid"] and File.id == deregister_file_data["file_id"]).get()
        host_relationship.delete_instance()

        # if there is no one hosting the file, delete it
        try:
            Hosts.get(Hosts.hosted_file == deregister_file_data["file_id"])
        except Hosts.DoesNotExist:
            File.get(File.id == deregister_file_data["file_id"]).delete_instance()

        # increment the peer's expected seq number
        peer.expected_seq_number += 1
        peer.save()

    except Peer.DoesNotExist:
        error = "Peer with guid {} does not exist".format(deregister_file_data["guid"])
        success = False
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


# removes a peer from the hosts list of a file
# if the file has no hosts remaining, removes it
def deregister_file_by_hash(deregister_file_by_hash_data, peer_ip):
    success = True
    deregister_file_by_hash_response = {
        "success": success,
    }

    try:
        # check if peer with guid exists, if so updates the peer's ip and timestamp
        peer = Peer.get(Peer.uuid == deregister_file_by_hash_data["guid"])
        if(peer.ip != peer_ip):
            peer.ip = peer_ip
        peer.save()

        if(peer.expected_seq_number != deregister_file_by_hash_data["seq_number"]):
            raise Exception("Tracker is expecting sequence number {} (sequence number {} was sent)"
                            .format(peer.expected_seq_number, deregister_file_by_hash_data["seq_number"]))

        # checks if specified peer is hosting specified file, if so deletes the record
        host_relationship = Hosts.select()\
            .join(File, on=(File.id == Hosts.hosted_file))\
            .join(Peer, on=(Peer.id == Hosts.hosting_peer))\
            .where(Peer.uuid == deregister_file_by_hash_data["guid"] and
                   File.full_hash == deregister_file_by_hash_data["file_hash"])\
            .get()
        host_relationship.delete_instance()

        # if there is no one hosting the file, delete it
        try:
            Hosts.select()\
                .join(File, on=(File.id == Hosts.hosted_file))\
                .where(File.full_hash == deregister_file_by_hash_data["file_hash"] and
                       Hosts.hosted_file == File.id)\
                .get()
        except Hosts.DoesNotExist:
            file_to_delete = File.get(File.full_hash == deregister_file_by_hash_data["file_hash"])
            Chunk.delete()\
                .where(Chunk.parent_file == file_to_delete.id)\
                .execute()

            File.get(File.full_hash == deregister_file_by_hash_data["file_hash"]).delete_instance()

        # increment the peer's expected seq number
        peer.expected_seq_number += 1
        peer.save()

    except Peer.DoesNotExist:
        error = "Peer with guid {} does not exist".format(deregister_file_by_hash_data["guid"])
        success = False
    except Hosts.DoesNotExist:
        error = "No peer with guid {} is currently hosting file with hash {}"\
            .format(deregister_file_by_hash_data["guid"], deregister_file_by_hash_data["file_hash"])
        success = False
    except Exception as e:
        error = str(e)
        success = False
        print(e)

    if(not success):
        deregister_file_by_hash_response = {
            "success": success,
            "error": error,
        }

    return deregister_file_by_hash_response


# returns the peers status on the tracker as a dict in the specified output format
# contains files the peer is hosting, and the peer's expected sequence numbers
def get_peer_status(peer_guid):
    success = True
    peer_status_response = {
        "success": success,
        "files": [],
        "expected_seq_number": None,
        "ka_expected_seq_number": None,
    }

    try:
        selected_peer = Peer.select().where(Peer.uuid == peer_guid).get()

        peer_file_list_query = File.select()\
            .join(Hosts, on=(File.id == Hosts.hosted_file))\
            .join(Peer, on=(Peer.id == Hosts.hosting_peer))\
            .where(Peer.uuid == selected_peer.uuid)

        if(peer_file_list_query.exists()):
            for file in peer_file_list_query:
                peer_status_response["files"].append(file.to_dict_simple())

        peer_status_response["expected_seq_number"] = selected_peer.expected_seq_number
        peer_status_response["ka_expected_seq_number"] = selected_peer.ka_expected_seq_number

    except Peer.DoesNotExist:
        error = "No peer with guid {} is known to tracker".format(peer_guid)
        success = False
    except Exception as e:
        error = str(e)
        success = False

    if(not success):
        peer_status_response = {
            "success": success,
            "error": error,
        }

    return peer_status_response


# check if a tracker with the given IP exists in the tracker list
def tracker_ip_exists(ip):
    try:
        Tracker.get(Tracker.ip == ip)
        return True
    except DoesNotExist:
        return False


# creates a new tracker with the given IP and name
def add_tracker(ip):
    tracker = Tracker.create(ip=ip)

    return tracker


# creates a new peer with the given UUID if it doesn't exist
def ensure_peer_exists(ip, puuid, seq_num=None):
    peer_uuid = uuid.UUID(puuid)
    try:
        Peer.get(Peer.uuid == peer_uuid)
    except DoesNotExist:
        if seq_num is None:
            Peer.create(uuid=peer_uuid, ip=ip)
        else:
            Peer.create(uuid=peer_uuid, ip=ip, expected_seq_number=seq_num)


# returns the expected sequence number for the given peer uuid
def peer_expected_seq(puuid):
    peer = Peer.get(Peer.uuid == puuid)
    return peer.expected_seq_number


# returns the expected keep-alive sequence number for the given peer uuid
def peer_expected_ka_seq(puuid):
    peer = Peer.get(Peer.uuid == puuid)
    return peer.ka_expected_seq_number


# dumps the db to a dictionary for new trackers
def new_tracker_dump():
    con = db.connection()
    output = StringIO()
    for line in con.iterdump():
        output.write(line)

    return output.getvalue()


# Replaces the database at the given path with the contents of the given sql string
def replace_database(sql_str):
    db.close()

    # Truncate the db_path file
    open(constants.DB_PATH, "w").close()

    load_database(constants.DB_PATH)
    db.connection().executescript(sql_str)


# removes the tracker with specified id from the tracker list
def remove_tracker_by_ip(ip):
    Tracker.delete().where(Tracker.ip == ip).execute()


# Decorators to explicitly manage connections
# These functions should maybe not be in this file? I'm not sure
@app.before_request
def before_request():
    db.connect()


@app.after_request
def after_request(response):
    db.close()
    return response
