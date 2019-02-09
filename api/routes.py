from api import app
from flask import request, jsonify


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

    dummyResponse = {
        "success" : True,
        "files" : [
            {
                "id" : 1,
                "name" : "joel",
                "hash" : "alksjhf98ufyah9"
            },
            {
                "id" : 2,
                "name" : "is",
                "hash" : "0f9ua40jf0j0934j0w39j09"
            },
            {
                "id" : 3,
                "name" : "great",
                "hash" : "j9ra09jrega546df684fgad648agdf"
            }
        ]
    }

    return jsonify(dummyResponse)


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
            "name" : "<chunk filename>",
            "hash" : "<hash of chunk>"
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
@app.route('/file/<id>', methods=['GET'])
def get_file(id):
    # pull the file metadata from the db (name, list of peers, list of chunks, etc)

    dummyResponse = {
        "success" : True,
        "name" : "sick nasty file with id {}".format(id),
        "file_hash" : "arfihu9f87h49h72f89hyufaf9h78af439h878h9f739h8a8h7",
        "peers" : [
            { "ip" : "192.168.0.1" },
            { "ip" : "192.168.0.2" },
            { "ip" : "192.168.0.3" }
        ],
        "chunks" : [
            { 
                "name" : "avengers_1.mp4",
                "hash" : "asdljiksfadlkhjsadflkjhdsaflkjhsdaflkj"
            },
            { 
                "name" : "avengers_2.mp4",
                "hash" : "assadf5f4sd54asfd456"
            },
            { 
                "name" : "avengers_3.mp4",
                "hash" : "fdgh68fhg64d6d4f5gh3fg6h5d4687"
            }
        ]
    }

    return jsonify(dummyResponse)


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
    # pull the list of other trackers from the db

    dummyResponse = {
        "success" : True,
        "trackers" : [
            { "name" : "the p2p bay", "ip" : "1.1.1.1"},
            { "name" : "the p2p bay", "ip" : "1.1.1.2"},
            { "name" : "the p2p bay", "ip" : "1.1.1.3"}
        ]
    }

    return jsonify(dummyResponse)


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
            "name" : "<chunk filename>", 
            "hash" : "<hash of chunk>"
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
    "guid" : "<echoed guid if you had one already, otherwise your newly assigned one"
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
@app.route('/add_file', methods=['POST'])
def add_file():
    if(not request.json):
        return "error: request is not json"

    print(request.json)

    dummyResponse = {
        "success" : True,
        "file_id" : 42,
        "guid" : "adsf54asd6f46asd54f65sd"
    }

    return jsonify(dummyResponse)


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
    "success" : <true/false>
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
@app.route('/keep_alive', methods=['PUT'])
def keep_alive():
    if(not request.json):
        return "error: request is not json"

    print(request.json)

    dummyResponse = {
        "success" : True
    }

    return jsonify(dummyResponse)


# takes a json req with the client's guid and the file id as args
# TODO: consider replacing the file id with a hash to make it tracker independent
# --- INPUT ---
# Expects JSON blob in the form:
'''
{
    "file_id" : <file's id in the tracker db>,
    "guid" : "<client's guid>"
}
'''
# --- OUTPUT ---
# Returns a JSON blob in the form:
'''
{
    "success" : <true/false>
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
@app.route('/deregister_file', methods=['DELETE'])
def deregister_file():
    if(not request.json or not "title" in request.json):
        return "error: request is not json"

    print(request.json)

    return "removed you as a host for this file"
