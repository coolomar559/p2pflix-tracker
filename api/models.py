import peewee
import datetime
 
db = peewee.SqliteDatabase("trackerDB.db")

# The base model the other models extend, used to force all other models to use the same database
class BaseModel(peewee.Model):
    class Meta:
        database = db

class Tracker(BaseModel):
    ip = peewee.CharField()
    name = peewee.CharField()

class Peer(BaseModel):
     ip = peewee.CharField()
     uuid = peewee.UUIDField()
     keepAliveTimestamp = peewee.DateTimeField(default=datetime.datetime.now)

class File(BaseModel):
    name = peewee.CharField()
    fullHash = peewee.IntegerField()


class Chunk(BaseModel):
    chunkID = peewee.IntegerField()
    chunkHash = peewee.IntegerField()
    name = peewee.CharField()
    parentFile = peewee.ForeignKeyField(File, backref="chunks")

class Hosts(BaseModel):
    hostedFile = peewee.ForeignKeyField(File, backref='hostedFile')
    hostingPeer = peewee.ForeignKeyField(Peer, backref='hostingPeer')

    class Meta:
        indexes = (
            # Specify a unique multi-column index on hostedFile/hostingPeer
            (('hostedFile', 'hostingPeer'), True),
        )