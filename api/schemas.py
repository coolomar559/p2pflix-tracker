
# --- ADD_FILE SCHEMA ---
# JSON schema for /add_file endpoint inputs
# Example:
'''
{
    "name" : "<file name>",
    "full_hash" : "<hash of full file>",
    "chunks" : [
        {
            "id" : <chunk id for sequencing>,
            "name" : "<chunk filename>",
            "hash" : "<hash of chunk>"
        },
        ...
    ],
    "guid" : "<client's guid>",
    "seq_number": <client's current sequence number/sequence number of this message>
}
'''
ADD_FILE_SCHEMA = {
    "type": "object",
    "maxProperties": 5,
    "properties": {
        "name": {"type": "string"},
        "full_hash": {"type": "string"},
        "chunks": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": {
                "type": "object",
                "maxProperties": 3,
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "hash": {"type": "string"},
                },
                "required": ["id", "name", "hash"],
            },
        },
        "guid": {"type": ["string", "null"]},
        "seq_number": {"type": "integer"},
    },
    "required": ["name", "full_hash", "chunks", "guid", "seq_number"],
}


# --- KEEP_ALIVE SCHEMA ---
# JSON schema for /keep_alive endpoint inputs
# Example:
'''
{
    "guid" : "<client's guid>"
}
'''
KEEP_ALIVE_SCHEMA = {
    "type": "object",
    "maxProperties": 1,
    "properties": {
        "guid": {"type": "string"},
    },
    "required": ["guid"],
}


# --- DEREGISTER_FILE SCHEMA ---
# JSON schema for /deregister_file endpoint inputs
# Example:
'''
{
    "file_id" : <file's id in the tracker db>,
    "guid" : "<client's guid>",
    "seq_number": <client's current sequence number/sequence number of this message>
}
'''
DEREGISTER_FILE_SCHEMA = {
    "type": "object",
    "maxProperties": 3,
    "properties": {
        "file_id": {"type": "integer"},
        "guid": {"type": "string"},
        "seq_number": {"type": "integer"},
    },
    "required": ["file_id", "guid", "seq_number"],
}
