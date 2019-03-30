import sys
from traceback import print_exc

from api import app, models, schemas
from api.event_broadcaster import EventBroadcaster
from flask import jsonify, request
from jsonschema import FormatChecker, validate, ValidationError
from peewee import DoesNotExist

broadcaster = EventBroadcaster()

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
    success = True

    try:
        trackers = models.get_tracker_list()
        tracker_list_response = {
            "success": success,
            "trackers": trackers,
        }
    except DoesNotExist:
        error = "No other trackers known to this one"
        success = False
    except Exception as e:
        error = str(e)
        success = False

    if(not success):
        tracker_list_response = {
            "success": success,
            "error": error,
        }

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

            if add_file_response["success"]:
                request_data["guid"] = str(add_file_response["guid"])
                broadcaster.new_event("add_file", requester_ip, request_data)
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

            if keep_alive_response["success"]:
                broadcaster.new_event("keep_alive", requester_ip, request_data)
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

            if deregister_file_by_hash_response["success"]:
                broadcaster.new_event("deregister_file_by_hash", requester_ip, request_data)
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


# updates the tracker's db based on a new operation from another tracker
# expects JSON blob of information regarding the event
# blob contains event type and a data dictionary that is specific to the event type
# see the different event's original method (e.g. add_file) for my detail on the data portion
# If the tracker sending this event does not exist in the DB, the event is ignored
# --- INPUT ---
# Expects JSON blob in the form:
'''
{
    "event": "add_file|keep_alive|deregister_file_by_hash|new_tracker",
    "event_ip": "ip address (e.g. 1.2.3.4)",
    "data": { ... }
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
@app.route('/tracker_sync', methods=['PATCH'])
def tracker_sync():
    request_data = request.get_json(silent=True)
    requester_ip = request.remote_addr

    if request_data is None:
        return jsonify({
            "error": "Request is not JSON",
            "success": False,
        })

    if not models.tracker_ip_exists(requester_ip):
        # Return an error if the tracker is not in the tracker list
        return jsonify({
            "success": False,
            "dead_tracker": True,
            "error": "Tracker not in tracker list",
        })

    try:
        validate(request_data, schemas.TRACKER_SYNC_SCHEMA, format_checker=FormatChecker())
    except ValidationError as e:
        return jsonify({
            "error": str(e),
            "success": False,
        })

    event = request_data["event"]
    event_ip = request_data["event_ip"]
    event_data = request_data["data"]

    # By default, don't rebroadcast and respond with success
    rebroadcast = False
    sync_response = {"success": True}

    try:
        if event == "new_tracker":
            # If the tracker doesn't exist, rebroadcast and add it
            if not models.tracker_ip_exists(event_ip):
                tracker = models.add_tracker(event_ip, "george")

                # Can't just set rebroadcast here since we need to broadcast before adding the tracker
                broadcaster.new_event(event, event_ip, event_data)
                broadcaster.new_tracker(tracker)

        elif event == "add_file":
            peer_guid = event_data["guid"]
            models.ensure_peer_exists(event_ip, peer_guid, event_data["seq_number"])

            # If the sequence number is new, apply and rebroadcast
            if event_data["seq_number"] >= models.peer_expected_seq(peer_guid):
                models.add_file(event_data, event_ip)
                rebroadcast = True

        elif event == "keep_alive":
            peer_guid = event_data["guid"]
            models.ensure_peer_exists(event_ip, peer_guid)

            # If the keepalive sequence number is new, apply and rebroadcast
            if event_data["ka_seq_number"] >= models.peer_expected_ka_seq(peer_guid):
                models.keep_alive(event_data, event_ip)
                rebroadcast = True

        elif event == "deregister_file_by_hash":
            peer_guid = event_data["guid"]
            models.ensure_peer_exists(event_ip, peer_guid)

            # If the sequence number is new, apply and rebroadcast
            if event_data["seq_number"] >= models.peer_expected_seq(peer_guid):
                models.deregister_file_by_hash(event_data, event_ip)
                rebroadcast = True

        # Only rebroadcast if specified
        if rebroadcast:
            broadcaster.new_event(event, event_ip, event_data)
    except Exception:
        print("Recieved exception during tracker sync", sys.stderr)
        print_exc()

        return jsonify({
            "error": "Unexpected error",
            "success": False,
        })

    return jsonify(sync_response)


# adds a new tracker to the tracker list and responds with a full database dump
# --- INPUT ---
# Expects JSON blob in the form: (empty)
'''
{ }
'''
# --- OUTPUT ---
# Returns a JSON blob in the form:
'''
{
    "success": true,
    "data": "... A full database dump"
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
@app.route('/new_tracker', methods=['POST'])
def new_tracker():
    success = True

    request_data = request.get_json(silent=True)
    requester_ip = request.remote_addr

    if request_data is None:
        error = "Request is not JSON"
        success = False
    else:
        try:
            validate(request_data, schemas.NEW_TRACKER_SCHEMA)

            if models.tracker_ip_exists(requester_ip):
                # If the tracker exists, remove it before dumping the DB and then re-add it but don't broadcast
                models.remove_tracker_by_ip(requester_ip)
                data_dump = models.new_tracker_dump()
                models.add_tracker(requester_ip, "george")
            else:
                # If the tracker doesn't exist, dump the DB before adding it and then broadcast
                data_dump = models.new_tracker_dump()
                broadcaster.new_event("new_tracker", requester_ip, {})
                new_tracker = models.add_tracker(requester_ip, "george")
                broadcaster.new_tracker(new_tracker)

            new_tracker_response = {
                "success": True,
                "data": data_dump,
            }
        except ValidationError as e:
            error = str(e)
            success = False
        except Exception as e:
            error = str(e)
            success = False

    if not success:
        new_tracker_response = {
            "success": success,
            "error": error,
        }

    return jsonify(new_tracker_response)
