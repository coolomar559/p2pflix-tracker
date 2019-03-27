from api import app, models, schemas
from flask import jsonify, request
from jsonschema import validate, ValidationError

# Gets the list of files the tracker knows about
# --- INPUT ---
# Nothing
# --- OUTPUT ---
# Returns a JSON blob of the form:
'''
{
    "success": true,
    "files": [
        {
            "id": <file id>,
            "name": "<file's name>",
            "hash": "<full file hash>",
            "active_peers": <number of recently keepalived peer>
        },
        ...
    ]
}
'''
# --- ON ERROR ---
# Returns a JSON blob in the form:
'''
{
    "success": false,
    "error": "<error reason>"
}
'''
@app.route('/file_list', methods=['GET'])
def get_file_list():
    # pull the list of file ids and names from db and convert to json

    file_list_response = models.get_file_list()

    return jsonify(file_list_response)


# TODO: consider replacing the id with the file's hash or to a json blob input to make it tracker independent
# TODO: consider giving the chunk an id as well to make the chunk order clear
# TODO: consider associating peers for each chunk
# Gets the information about a specific file id
# --- INPUT ---
# The file's id (as known by the tracker) via the url
# --- OUTPUT ---
# Returns a JSON blob of the form:
'''
{
    "success": true,
    "name": "<file name>",
    "file_hash": "<hash of the full file>",
    "peers": [
        {"ip": "<peer's ip>"},
        ...
    ],
    "chunks": [
        {
            "id": <chunk id for sequencing>,
            "name": "<chunk filename>",
            "hash": "<hash of chunk>"
        },
        ...
    ]
}
'''
# --- ON ERROR ---
# Returns a JSON blob in the form:
'''
{
    "success" : false,
    "error" : "<error reason>",
}
'''
@app.route('/file/<file_id>', methods=['GET'])
def get_file(file_id):
    # pull the file metadata from the db (name, list of peers, list of chunks, etc)

    get_file_response = models.get_file(file_id)

    return jsonify(get_file_response)


# TODO: consider giving the chunk an id as well to make the chunk order clear
# TODO: consider associating peers for each chunk
# Gets the information about a specific file hash
# --- INPUT ---
# The file's id (as known by the tracker) via the url
# --- OUTPUT ---
# Returns a JSON blob of the form:
'''
{
    "success": true,
    "name": "<file name>",
    "file_hash": "<hash of the full file>",
    "peers": [
        {"ip": "<peer's ip>"},
        ...
    ],
    "chunks": [
        {
            "id": <chunk id for sequencing>,
            "name": "<chunk filename>",
            "hash": "<hash of chunk>"
        },
        ...
    ]
}
'''
# --- ON ERROR ---
# Returns a JSON blob in the form:
'''
{
    "success" : false,
    "error" : "<error reason>",
}
'''
@app.route('/file_by_hash/<file_full_hash>', methods=['GET'])
def get_file_by_hash(file_full_hash):
    # pull the file metadata from the db (name, list of peers, list of chunks, etc)

    get_file_by_hash_response = models.get_file_by_hash(file_full_hash)

    return jsonify(get_file_by_hash_response)


# Gets the list of other trackers the tracker knows about
# --- INPUT ---
# Nothing
# --- OUTPUT ---
# Returns a JSON blob of the form:
'''
{
    "success": true,
    "trackers": [
        {"name": "<tracker name>", "ip": "<tracker's ip>"},
        ...
    ]
}
'''
# --- ON ERROR ---
# Returns a JSON blob in the form:
'''
{
    "success": false,
    "error": "<error reason>"
}
'''
@app.route('/tracker_list', methods=['GET'])
def get_tracker_list():
    tracker_list_response = models.get_tracker_list()

    return jsonify(tracker_list_response)


# adds a file to the tracker's list
# expects JSON blob of metadata about the file
# blob contains file name, full file hash, list of chunk names + hashes, guid
# TODO: do something about getting files added by localhost
# client ip collected from request
# --- INPUT ---
# Expects JSON blob in the form:
'''
{
    "name": "<file name>",
    "full_hash": "<hash of full file>",
    "chunks": [
        {
            "id": <chunk id for sequencing>,
            "name": "<chunk filename>",
            "hash": "<hash of chunk>"
        },
        ...
    ],
    "guid": "<client's guid>",
    "seq_number": <client's current sequence number/sequence number of this message>
}
'''
# --- OUTPUT ---
# Returns a JSON blob in the form:
'''
{
    "success": true,
    "file_id": "<the existing id if the tracker already has it, or the new one if it didnt>",
    "guid": "<echoed guid if you had one already, otherwise your newly assigned one"
}
'''
# --- ON ERROR ---
# Returns a JSON blob in the form:
'''
{
    "success": false,
    "error": "<error reason>"
}
'''
@app.route('/add_file', methods=['POST'])
def add_file():
    success = True

    request_data = request.get_json(silent=True)
    requester_ip = request.remote_addr

    if(request_data is None):
        error = "Request is not JSON"
        success = False
    else:
        try:
            validate(request_data, schemas.ADD_FILE_SCHEMA)
            add_file_response = models.add_file(request_data, requester_ip)
        except ValidationError as e:
            error = str(e)
            success = False
        except Exception as e:
            error = str(e)
            success = False

    if(not success):
        add_file_response = {
            "success": success,
            "error": error,
        }

    return jsonify(add_file_response)


# tells the server you're still there hosting
# takes a json request with the clients guid as an argument
# client ip collected from request
# --- INPUT ---
# Expects JSON blob in the form:
'''
{
    "guid": "<client's guid>",
    "ka_seq_number": <keepalive sequence number>    #integer
}
'''
# --- OUTPUT ---
# Returns a JSON blob in the form:
'''
{
    "success": true
}
'''
# --- ON ERROR ---
# Returns a JSON blob in the form:
'''
{
    "success": false,
    "error": "<error reason>"
}
'''
@app.route('/keep_alive', methods=['PUT'])
def keep_alive():
    success = True

    request_data = request.get_json(silent=True)
    requester_ip = request.remote_addr

    if(request_data is None):
        error = "Request is not JSON"
        success = False
    else:
        try:
            validate(request_data, schemas.KEEP_ALIVE_SCHEMA)
            keep_alive_response = models.keep_alive(request_data, requester_ip)
        except ValidationError as e:
            error = str(e)
            success = False
        except Exception as e:
            error = str(e)
            success = False

    if(not success):
        keep_alive_response = {
            "success": success,
            "error": error,
        }

    return jsonify(keep_alive_response)


# removes you as a host for this file
# takes a json req with the client's guid and the file id as args
# --- INPUT ---
# Expects JSON blob in the form:
'''
{
    "file_id": <file's id in the tracker db>,
    "guid": "<client's guid>",
    "seq_number": <client's current sequence number/sequence number of this message>
}
'''
# --- OUTPUT ---
# Returns a JSON blob in the form:
'''
{
    "success": true
}
'''
# --- ON ERROR ---
# Returns a JSON blob in the form:
'''
{
    "success": false,
    "error": "<error reason>"
}
'''
@app.route('/deregister_file', methods=['DELETE'])
def deregister_file():
    success = True

    request_data = request.get_json(silent=True)
    requester_ip = request.remote_addr

    if(request_data is None):
        error = "Request is not JSON"
        success = False
    else:
        try:
            validate(request_data, schemas.DEREGISTER_FILE_SCHEMA)
            deregister_file_response = models.deregister_file(request_data, requester_ip)
        except ValidationError as e:
            error = str(e)
            success = False
        except Exception as e:
            error = str(e)
            success = False

    if(not success):
        deregister_file_response = {
            "success": success,
            "error": error,
        }

    return jsonify(deregister_file_response)


# removes you as a host for this file
# takes a json req with the client's guid and the file's full hash as args
# --- INPUT ---
# Expects JSON blob in the form:
'''
{
    "file_hash": <file's full hash>,
    "guid": "<client's guid>",
    "seq_number": <client's current sequence number/sequence number of this message>
}
'''
# --- OUTPUT ---
# Returns a JSON blob in the form:
'''
{
    "success": true
}
'''
# --- ON ERROR ---
# Returns a JSON blob in the form:
'''
{
    "success": false,
    "error": "<error reason>"
}
'''
@app.route('/deregister_file_by_hash', methods=['DELETE'])
def deregister_file_by_hash():
    success = True

    request_data = request.get_json(silent=True)
    requester_ip = request.remote_addr

    if(request_data is None):
        error = "Request is not JSON"
        success = False
    else:
        try:
            validate(request_data, schemas.DEREGISTER_FILE_BY_HASH_SCHEMA)
            deregister_file_by_hash_response = models.deregister_file_by_hash(request_data, requester_ip)
        except ValidationError as e:
            error = str(e)
            success = False
        except Exception as e:
            error = str(e)
            success = False

    if(not success):
        deregister_file_by_hash_response = {
            "success": success,
            "error": error,
        }

    return jsonify(deregister_file_by_hash_response)


# Gets the information about a specific peer
# this includes what files it is hosting, its expected sequence number,
# and its expected keep alive number
# --- INPUT ---
# The peer's guid via the url
# --- OUTPUT ---
# Returns a JSON blob of the form:
'''
{
    "success": true,
    "files": [
        {
            "id": <file's id according to the tracker>,
            "name": "<file's name>",
            "hash": "<full file hash>"
        },
        ...
    ],
    "expected_seq_number": <expected normal sequence number>,
    "ka_expected_seq_number": <expected keepalive sequence number>
}
'''
# --- ON ERROR ---
# Returns a JSON blob in the form:
'''
{
    "success" : false,
    "error" : "<error reason>",
}
'''
@app.route('/peer_status/<peer_guid>', methods=['GET'])
def peer_status(peer_guid):
    # pull the peer data from the db (hosted files, seq numbers)

    peer_status_response = models.get_peer_status(peer_guid)

    return jsonify(peer_status_response)
