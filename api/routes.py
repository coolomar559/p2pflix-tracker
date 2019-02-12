from api import app, models, schemas

from flask import jsonify, request

from jsonschema import ValidationError, validate

# Gets the list of files the tracker knows about
# --- INPUT ---
# Nothing
# --- OUTPUT ---
# Returns a JSON blob of the form:
'''
{
    "success" : <true/false>,
    "files" : [
        {
            "id" : <file id>,
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
    "success" : false,
    "error" : "<error reason>"
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
# Gets the list of files the tracker knows about
# --- INPUT ---
# The file's id (as known by the tracker) via the url
# --- OUTPUT ---
# Returns a JSON blob of the form:
'''
{
    "success" : <true/false>,
    "name" : "<file name>",
    "file_hash" : "<hash of the full file>",
    "peers" : [
        { "ip" : "<peer's ip>" },
        ...
    ],
    "chunks" : [
        {
            "id" : <chunk id for sequencing>,
            "name" : "<chunk filename>",
            "hash" : "<hash of chunk>",
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

    models.get_file(file_id)

    dummy_response = {
        "success": True,
        "name": "sick nasty file with id {}".format(file_id),
        "file_hash": "arfihu9f87h49h72f89hyufaf9h78af439h878h9f739h8a8h7",
        "peers": [
            {"ip": "192.168.0.1"},
            {"ip": "192.168.0.2"},
            {"ip": "192.168.0.3"},
        ],
        "chunks": [
            {
                "id": 1,
                "name": "avengers_1.mp4",
                "hash": "asdljiksfadlkhjsadflkjhdsaflkjhsdaflkj",
            },
            {
                "id": 2,
                "name": "avengers_2.mp4",
                "hash": "assadf5f4sd54asfd456",
            },
            {
                "id": 3,
                "name": "avengers_3.mp4",
                "hash": "fdgh68fhg64d6d4f5gh3fg6h5d4687",
            },
        ],
    }

    return jsonify(dummy_response)


# Gets the list of other trackers the tracker knows about
# --- INPUT ---
# Nothing
# --- OUTPUT ---
# Returns a JSON blob of the form:
'''
{
    "success" : <true/false>,
    "trackers" : [
        { "name" : "<tracker name>", "ip" : "<tracker's ip>"},
        ...
    ]
}
'''
# --- ON ERROR ---
# Returns a JSON blob in the form:
'''
{
    "success" : false,
    "error" : "<error reason>"
}
'''
@app.route('/tracker_list', methods=['GET'])
def get_tracker_list():
    tracker_list_response = models.get_tracker_list()

    return jsonify(tracker_list_response)


# adds a file to the tracker's list
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
        {
            "id" : <chunk id for sequencing>,
            "name" : "<chunk filename>",
            "hash" : "<hash of chunk>",
        },
        ...
    ],
    "guid" : "<client's guid>"
}
'''
# --- OUTPUT ---
# Returns a JSON blob in the form:
'''
{
    "success" : <true/false>,
    "file_id" : "<the existing id if the tracker already has it, or the new one if it didnt>",
    "guid" : "<echoed guid if you had one already, otherwise your newly assigned one",
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
            response = models.add_file(request_data, requester_ip)
        except Exception as e:
            error = str(e)
            success = False

    if(not success):
        response = {
            "success": success,
            "error": error,
        }

    return jsonify(response)


# tells the server you're still there hosting
# takes a json request with the clients guid as an argument
# client ip collected from request
# --- INPUT ---
# Expects JSON blob in the form:
'''
{
    "guid" : "<client's guid>",
}
'''
# --- OUTPUT ---
# Returns a JSON blob in the form:
'''
{
    "success" : <true/false>,
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
@app.route('/keep_alive', methods=['PUT'])
def keep_alive():
    success = True

    request_data = request.get_json(silent=True)

    if(request_data is None):
        error = "Request is not JSON"
        success = False
    else:
        try:
            validate(request_data, schemas.KEEP_ALIVE_SCHEMA)
        except ValidationError as e:
            error = str(e)
            success = False

    if(success):
        response = {
            "success": success,
        }
    else:
        response = {
            "success": success,
            "error": error,
        }

    return jsonify(response)


# removes you as a host for this file
# takes a json req with the client's guid and the file id as args
# TODO: consider replacing the file id with a hash to make it tracker independent
# --- INPUT ---
# Expects JSON blob in the form:
'''
{
    "file_id" : <file's id in the tracker db>,
    "guid" : "<client's guid>",
}
'''
# --- OUTPUT ---
# Returns a JSON blob in the form:
'''
{
    "success" : <true/false>,
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
@app.route('/deregister_file', methods=['DELETE'])
def deregister_file():
    success = True

    request_data = request.get_json(silent=True)

    if(request_data is None):
        error = "Request is not JSON"
        success = False
    else:
        try:
            validate(request_data, schemas.DEREGISTER_FILE_SCHEMA)
        except ValidationError as e:
            error = str(e)
            success = False

    if(success):
        response = {
            "success": True,
        }
    else:
        response = {
            "success": False,
            "error": error,
        }

    return jsonify(response)
