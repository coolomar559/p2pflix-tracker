from copy import deepcopy

# --- CHUNK SCHEMA ---
# JSON schema for chunks within /add_file endpoint inputs
# Example:
'''
{
    "id" : <chunk id for sequencing>,
    "name" : "<chunk filename>",
    "hash" : "<hash of chunk>"
}
'''
CHUNK_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "hash": {"type": "string"},
    },
    "required": ["id", "name", "hash"],
    "additionalProperties": False,
}

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
    "properties": {
        "name": {"type": "string"},
        "full_hash": {"type": "string"},
        "chunks": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": CHUNK_SCHEMA,
        },
        "guid": {"type": ["string", "null"]},
        "seq_number": {"type": "integer"},
    },
    "required": ["name", "full_hash", "chunks", "guid", "seq_number"],
    "additionalProperties": False,
}

# --- ADD_FILE_MANDATORY_GUID_SCHEMA
# JSON schema for adding a file with a guaranteed non-null GUID
# Used for validating tracker sync requests
# See ADD_FILE for example
ADD_FILE_MANDATORY_GUID_SCHEMA = deepcopy(ADD_FILE_SCHEMA)
ADD_FILE_MANDATORY_GUID_SCHEMA["properties"]["guid"]["type"] = "string"

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
    "properties": {
        "guid": {"type": "string"},
        "ka_seq_number": {"type": "integer"},
    },
    "required": ["guid", "ka_seq_number"],
    "additionalProperties": False,
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
    "properties": {
        "file_id": {"type": "integer"},
        "guid": {"type": "string"},
        "seq_number": {"type": "integer"},
    },
    "required": ["file_id", "guid", "seq_number"],
    "additionalProperties": False,
}


# --- DEREGISTER_FILE_BY_HASH SCHEMA ---
# JSON schema for /deregister_file_by_hash endpoint inputs
# Example:
'''
{
    "file_hash" : <full hash of the file>,
    "guid" : "<client's guid>",
    "seq_number": <client's current sequence number/sequence number of this message>
}
'''
DEREGISTER_FILE_BY_HASH_SCHEMA = {
    "type": "object",
    "properties": {
        "file_hash": {"type": "string"},
        "guid": {"type": "string"},
        "seq_number": {"type": "integer"},
    },
    "required": ["file_hash", "guid", "seq_number"],
    "additionalProperties": False,
}


# --- NEW_TRACKER SCHEMA ---
# JSON schema for /deregister_file_by_hash endpoint inputs
# Expects an empty json object
NEW_TRACKER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
}


# --- TRACKER_SYNC SCHEMA ---
# JSON schema for /tracker_sync endpoint inputs
# Example:
'''
{
    "event": "add_file|keep_alive|deregister_file_by_hash|new_tracker",
    "event_ip": "<ip for event>"
    "data": { ... }
}
'''
TRACKER_SYNC_SCHEMA = {
    "type": "object",
    "properties": {
        "event": {
            "type": "string",
            "enum": ["add_file", "keep_alive", "deregister_file_by_hash", "new_tracker"],
        },
        "event_ip": {
            "type": "string",
            "format": "ipv4",
        },
        "data": {"type": "object"},
    },
    "required": ["event", "event_ip", "data"],
    "additionalProperties": False,
    "allOf": [
        {
            "if": {
                "properties": {"event": {"const": "add_file"}},
            },
            "then": {
                "properties": {"data": ADD_FILE_MANDATORY_GUID_SCHEMA},
            },
        },
        {
            "if": {
                "properties": {"event": {"const": "keep_alive"}},
            },
            "then": {
                "properties": {"data": KEEP_ALIVE_SCHEMA},
            },
        },
        {
            "if": {
                "properties": {"event": {"const": "deregister_file_by_hash"}},
            },
            "then": {
                "properties": {"data": DEREGISTER_FILE_BY_HASH_SCHEMA},
            },
        },
        {
            "if": {
                "properties": {"event": {"const": "new_tracker"}},
            },
            "then": {
                "properties": {
                    "data": NEW_TRACKER_SCHEMA,
                },
            },
        },
    ],
}
