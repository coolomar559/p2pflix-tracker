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
    parent_file = peewee.ForeignKeyField(File, backref="chunks")


class Hosts(BaseModel):
    hosted_file = peewee.ForeignKeyField(File, backref='hosted_file')
    hosting_peer = peewee.ForeignKeyField(Peer, backref='hosting_peer')

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
    tracker_list_response = {
        "success": True,
        "trackers": [],
    }

    try:
        for tracker in Tracker.select():
            tracker_list_response["trackers"].append(tracker.to_dict())
    except Exception as e:
        tracker_list_response = {
            "success": False,
            "error": str(e),
        }

    return tracker_list_response


# returns the file list on the tracker as a dict in the specified output format
# TODO: only return files that have a recent timestamped peer
def get_file_list():
    file_list_response = {
        "success": True,
        "files": [],
    }

    try:
        for file in File.select():
            file_list_response["files"].append(file.to_dict_simple())
    except Exception as e:
        file_list_response = {
            "success": False,
            "error": str(e),
        }

    return file_list_response


# returns the data for a specific file
# TODO: finish this
def get_file(file_id):
    query = File.select(File.name, File.full_hash, Chunk.chunk_id, Chunk.chunk_hash, Chunk.name.alias("chunk_name")).join(Chunk, on=(File.id == Chunk.parent_file)).join(Hosts, on=(File.id == Hosts.hosted_file)).join(Peer, on=(Peer.id == Hosts.hosting_peer)).where(File.id == file_id)

    for item in query:
        print(item.chunk.chunk_hash)


# TODO: needs to check if the guid exists, currently assumes it does
def add_file(add_file_data, peer_ip):
    try:
        # if client has no guid, add them as a peer and generate a guid
        # else get the peer
        if(add_file_data["guid"] is None):
            peer = add_peer(peer_ip)
        else:
            peer = Peer.get(Peer.uuid == add_file_data["guid"])

        # add the file to the db
        new_file = File().create(
            name=add_file_data["name"],
            full_hash=add_file_data["full_hash"],
        )

        # add the chunks to the db and associate with the file
        for chunk_data in add_file_data["chunks"]:
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

        add_file_response = {
            "success": True,
            "file_id": new_file.id,
            "guid": peer.uuid,
        }
    except Exception as e:
        add_file_response = {
            "success": False,
            "error": str(e),
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


# Decorators to explicitly manage connections
# These functions should maybe not be in this file? I'm not sure
@app.before_request
def before_request():
    db.connect()


@app.after_request
def after_request(response):
    db.close()
    return response
