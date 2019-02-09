
# --- ADD_FILE SCHEMA ---
# JSON schema for /add_file endpoint inputs
# Example:
'''
{
    "name" : "<file name>",
    "full_hash" : "<hash of full file>",
    "chunks" : [
        { 
            "name" : "<chunk filename>", 
            "hash" : "<hash of chunk>"
        },
        ...
    ],
    "guid" : "<client's guid>"
}
'''
ADD_FILE_SCHEMA = {
    "type" : "object",
    "maxProperties" : 4,
    "properties" : {
        "name" : { "type" : "string" },
        "full_hash" : { "type" : "string" },
        "chunks" : {
            "type" : "array",
            "minItems" : 1,
            "uniqueItems" : True,
            "items" : {
                "type" : "object",
                "maxProperties" : 2,
                "properties" : {
                    "name" : { "type" : "string" },
                    "hash" : { "type" : "string" }
                },
                "required" : ["name", "hash"]
            }
        },
        "guid" : { "type" : "string" }
    },
    "required" : ["name", "full_hash", "chunks", "guid"]
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
    "type" : "object",
    "maxProperties" : 1,
    "properties" : {
        "guid" : { "type" : "string" }
    },
    "required" : ["guid"]
}


# --- DEREGISTER_FILE SCHEMA ---
# JSON schema for /deregister_file endpoint inputs
# Example:
'''
{
    "file_id" : <file's id in the tracker db>,
    "guid" : "<client's guid>"
}
'''
DEREGISTER_FILE_SCHEMA = {
    "type" : "object",
    "maxProperties" : 2,
    "properties" : {
        "file_id" : { "type" : "integer" },
        "guid" : { "type" : "string" }
    },
    "required" : ["file_id", "guid"]
}