from api import app
from flask import request


# Gets the list of files the tracker knows about
# --- INPUT ---
# Nothing
# --- OUTPUT ---
# Returns a JSON blob of the form:
'''
{
    "success" : "<true/false>",
    "files" : [
        {
            "id" : "<file id>",
            "name" : "<file's name>",
            "hash" : "<full file hash>"
        },
        ...
    ]
}
'''
# --- ON ERROR ---
# Returns a JSON blob in the form:
'''
{
    "success" : "false",
    "error" : "<error reason>"
}
'''
@app.route('/file_list', methods=['GET'])
def get_file_list():
    # pull the list of file ids and names from db and convert to json
    return "this will be a list of available files"


# TODO: consider replacing the id with the file's hash or to a json blob input to make it tracker independent
# TODO: consider giving the chunk an id as well to make the chunk order clear
# TODO: consider associating peers for each chunk
# Gets the list of files the tracker knows about
# --- INPUT ---
# The file's id (as known by the tracker) via the url
# --- OUTPUT ---
# Returns a JSON blob of the form:
'''
{
    "success" : "<true/false>",
    "name" : "<file name>",
    "file_hash" : "<hash of the full file>",
    "peers" : [
        { "ip" : "<peer's ip>" },
        ...
    ],
    "chunks" : [
        { 
            "name" : "<chunk filename",
            "hash" : "<hash of chunk>"
        }
    ]
}
'''
# --- ON ERROR ---
# Returns a JSON blob in the form:
'''
{
    "success" : "false",
    "error" : "<error reason>"
}
'''
@app.route('/file/<id>', methods=['GET'])
def get_file(id):
    # pull the file metadata from the db (name, list of peers, list of chunks, etc)
    return "this will be file {}'s metadata, if it exists".format(id)


# Gets the list of other trackers the tracker knows about
# --- INPUT ---
# Nothing
# --- OUTPUT ---
# Returns a JSON blob of the form:
'''
{
    "success" : "<true/false>",
    "trackers" : [
        { "name" : "<tracker name>", ip : "<tracker's ip"},
        ...
    ]
}
'''
# --- ON ERROR ---
# Returns a JSON blob in the form:
'''
{
    "success" : "false",
    "error" : "<error reason>"
}
'''
@app.route('/tracker_list', methods=['GET'])
def get_tracker_list():
    # pull the list of other trackers from the db
    return "this will be the list of trackers"


# expects JSON blob of metadata about the file
# blob contains file name, full file hash, list of chunk names + hashes, guid
# client ip collected from request
# --- INPUT ---
# Expects JSON blob in the form:
'''
{
    "name" : "<file name>",
    "full_hash" : "<hash of full file>",
    "chunks" : [
        { "name" : "<chunk filename>", "hash" : "<hash of chunk>"},
        ...
    ],
    "guid" : "<client's guid>"
}
'''
# --- OUTPUT ---
# Returns a JSON blob in the form:
'''
{
    "success" : "<true/false>",
    "file_id" : "<the existing id if the tracker already has it, or the new one if it didnt>"
}
'''
# --- ON ERROR ---
# Returns a JSON blob in the form:
'''
{
    "success" : "false",
    "error" : "<error reason>"
}
'''
@app.route('/add_file', methods=['POST'])
def add_file():
    if(not request.json or not "title" in request.json):
        return "error: request is not json"

    print(request.json)

    return "file added to tracker, you are added as a host"


# takes a json request with the clients guid as an argument
# client ip collected from request
# --- INPUT ---
# Expects JSON blob in the form:
'''
{
    "guid" : "<client's guid>"
}
'''
# --- OUTPUT ---
# Returns a JSON blob in the form:
'''
{
    "success" : "<true/false>"
}
'''
# --- ON ERROR ---
# Returns a JSON blob in the form:
'''
{
    "success" : "false",
    "error" : "<error reason>"
}
'''
@app.route('/keep_alive' methods=['PUT'])
def keep_alive():
    if(not request.json or not "title" in request.json):
        return "error: request is not json"

    print(request.json)

    return "updated your ip as a host"


# takes a json req with the client's guid and the file id as args
# TODO: consider replacing the file id with a hash to make it tracker independent
# --- INPUT ---
# Expects JSON blob in the form:
'''
{
    "file_id" : "<file's id in the tracker db>",
    "guid" : "<client's guid>"
}
'''
# --- OUTPUT ---
# Returns a JSON blob in the form:
'''
{
    "success" : "<true/false>"
}
'''
# --- ON ERROR ---
# Returns a JSON blob in the form:
'''
{
    "success" : "false",
    "error" : "<error reason>"
}
'''
@app.route('/deregister_file', methods=['DELETE'])
def deregister_file():
    if(not request.json or not "title" in request.json):
        return "error: request is not json"

    print(request.json)

    return "removed you as a host for this file"
