# P2PFlix Tracker

This program is the tracker portion of the distributed P2PFlix application.

[![Build Status](https://travis-ci.org/coolomar559/p2pflix-tracker.svg?branch=master)](https://travis-ci.org/coolomar559/p2pflix-tracker)

## Requirements

This project requires:

- Python 3.7 or greater
- pipenv

## Getting started

To install all requirements use `pipenv install`. To install extra requirements for
linting and testing, use `pipenv install --dev`.

## Linting

This project is linted using `flake8` and some related plugins. To lint use `pipenv run
flake8`.

## Testing

This project uses pytest for testing. To run tests, use `pipenv run pytest`. To write
tests, put everything needed in the `tests` directory.

## Running

To run the tracker, use `pipenv run ./tracker.py [-h] [-c [config filename]]`

By default the tracker will load setting from `config.toml`.




# REST API Documentation

Currently uses port `42070` by default, but will use the port specified in the config file.

## Endpoints
* GET - /file_list
* GET - /file/<file_id>
* GET - /file_by_hash/<file_full_hash>
* GET - /tracker_list
* POST - /add_file
* PUT - /keep_alive
* DELETE - /deregister_file
* DELETE - /deregister_file_by_hash
* PATCH - /tracker_sync
* POST - /new_tracker

## GET - /file_list
Gets the list of files that the tracker knows about.

### Input
GET request to the endpoint url.

Ex: `localhost:42070/file_list`

### Output
JSON object in the form:
```python
{
    "success": true,   #boolean
    "files": [
        {
            "id": <file id>,    #integer
            "name": "<file's name>",   #string
            "full_hash": "<full file hash>", #base64 string
            "active_peers": <number of recently keepalived peers> #integer
        },
        ...
    ]
}
```

### On Error
JSON object in the form:
```python
{
    "success": false,   #boolean
    "error": "<error reason>"   #string
}
```

## GET - /file/<file_id>
Gets the information about a specified file, including peers hosting it and its chunks.

### Input
GET request to the endpoint url, containing the file's id in the url.

Ex: `localhost:42070/file/2`

### Output
JSON object in the form:
```python
{
    "success": true,    #boolean
    "name": "<file name>", #string
    "file_hash": "<hash of the full file>",    #string (sha256 hash)
    "peers": [
        {
            "ip": "<peer's ip>" #string
        },
        ...
    ],
    "chunks": [
        {
            "id": <chunk id for sequencing>,    #integer
            "name": "<chunk filename>", #string
            "chunk_hash": "<hash of chunk>"   #string (sha256 hash)
        },
        ...
    ]
}
```

### On Error
JSON object in the form:
```python
{
    "success": false,   #boolean
    "error": "<error reason>"   #string
}
```

## GET - /file_by_hash/<file_full_hash>
Gets the information about a specified file, including peers hosting it and its chunks.

### Input
GET request to the endpoint url, containing the file's full hash in the url.

If there are somehow multiple files with the same hash, returns the first one.

Ex: `localhost:42070/file_by_hash/lkjlkjalijfljsdll9823`

### Output
JSON object in the form:
```python
{
    "success": true,    #boolean
    "name": "<file name>", #string
    "full_hash": "<hash of the full file>",    #string (sha256 hash)
    "peers": [
        {
            "ip": "<peer's ip>" #string
        },
        ...
    ],
    "chunks": [
        {
            "id": <chunk id for sequencing>,    #integer
            "name": "<chunk filename>", #string
            "chunk_hash": "<hash of chunk>"   #string (sha256 hash)
        },
        ...
    ]
}
```

### On Error
JSON object in the form:
```python
{
    "success": false,   #boolean
    "error": "<error reason>"   #string
}
```

## GET - /tracker_list
Gets the list of other trackers the tracker knows about.

### Input
GET request to the endpoint url.

Ex: `localhost:42070/tracker_list`

### Output
JSON object in the form:
```python
{
    "success": true,    #boolean
    "trackers": [
        {
            "name": "<tracker name>",   #string
             "ip" : "<tracker's ip>"    #string
        },
        ...
    ]
}
```

### On Error
JSON object in the form:
```python
{
    "success": false,   #boolean
    "error": "<error reason>"   #string
}
```

## POST - /add_file
Adds a file to the tracker's list.
Requires the peer guid, the hash of the file, all its chunks, and a sequence number.
If a file with a matching hash already exists, adds the peer as a host for that file.
Peer must provide their guid when adding a file.
If the peer does not already have a guid, they can provide `null` and will be given a guid in the response.

### Input
POST request to the endpoint url with a JSON object.

Ex: `localhost:42070/add_file`

JSON object in the form:
```python
{
    "name": "<file name>",  #string
    "full_hash": "<hash of full file>", #string (sha256 hash)
    "chunks": [
        {
            "id": <chunk id for sequencing>,    #integer
            "name": "<chunk filename>", #string
            "chunk_hash": "<hash of chunk>"   #string (sha256 hash)
        },
        ...
    ],
    "guid": "<client's guid>"/null,   #string or null
    "seq_number": <clients current sequence number/sequence number of this message> #integer
}
```

### Output
JSON object in the form:
```python
{
    "success": true,    #boolean
    "file_id": <the existing id if the tracker already has it, or the new one if it didnt>,   #integer
    "guid": "<echoed guid if you had one already, otherwise your newly assigned one>"    #string
}
```

### On Error
JSON object in the form:
```python
{
    "success": false,   #boolean
    "error": "<error reason>"   #string
}
```

## PUT - /keep_alive
Tells the server you're still there hosting.
Updates your keep alive timestamp on the server.
Requires a guid.

### Input
PUT request to the endpoint url with a JSON object.

Ex: `localhost:42070/keep_alive`

JSON object in the form:
```python
{
    "guid": "<client's guid>",   #string
    "ka_seq_number": <keepalive sequence number>    #integer
}
```

### Output
JSON object in the form:
```python
{
    "success": true #boolean
}
```

### On Error
JSON object in the form:
```python
{
    "success": false,   #boolean
    "error": "<error reason>"   #string
}
```

## DELETE - /deregister_file
Removes you as a host for the specified file.
Requires a guid.
If a file has no hosts remaining, removes it.

### Input
DELETE request to the endpoint url with a JSON object.

Ex: `localhost:42070/keep_alive`

JSON object in the form:
```python
{
    "file_id": <files id in the tracker db>,   #integer
    "guid": "<client's guid>",   #string
    "seq_number": <clients current sequence number/sequence number of this message> #integer
}
```

### Output
JSON object in the form:
```python
{
    "success": true   #boolean
}
```

### On Error
JSON object in the form:
```python
{
    "success": false,   #boolean
    "error": "<error reason>"   #string
}
```

## DELETE - /deregister_file_by_hash
Removes you as a host for the specified file.
Requires a guid.
If a file has no hosts remaining, removes it.

### Input
DELETE request to the endpoint url with a JSON object.

Ex: `localhost:42070/keep_alive`

JSON object in the form:
```python
{
    "file_hash": <files full hash>,   #integer
    "guid": "<client's guid>",   #string
    "seq_number": <clients current sequence number/sequence number of this message> #integer
}
```

### Output
JSON object in the form:
```python
{
    "success": true   #boolean
}
```

### On Error
JSON object in the form:
```python
{
    "success": false,   #boolean
    "error": "<error reason>"   #string
}
```

## GET - /peer_status/<peer_guid>
Gets the information about a specific peer this includes what files it is hosting, its expected sequence number, and its expected keep alive number.

### Input
GET request to the endpoint url, containing the peer's guid in the url.

Ex: `localhost:42070/peer_guid/d16f97be-0325-4fe8-98f5-b1fc128ae0d6`

### Output
JSON object in the form:
```python
{
    "success": true,
    "files": [
        {
            "id": <file's id according to the tracker>,
            "name": "<file's name>",
            "full_hash": "<full file hash>"
        },
        ...
    ],
    "expected_seq_number": <expected normal sequence number>,
    "ka_expected_seq_number": <expected keepalive sequence number>
}
```

## PATCH - /tracker_sync
Send/receive an information update to/from another tracker.
If the tracker has seen the event already, it ignores it. If the tracker has not seen the
event, it applies it to its own database and broadcasts it to other trackers.

### Input
JSON object in the form:
```python
{
    "event": "add_file|keep_alive|deregister_file_by_hash|new_tracker",   #string
    "event_ip": "<the relevant tracker or peer IP for the event>",   #string
    "data": { ... }   #dictionary
}
```

### Output
JSON object in the form:
```python
{
    "success": true   #boolean
}
```

### On Error
JSON object in the form:
```python
{
    "success": false,   #boolean
    "error": "<error reason>"   #string
}
```

### Output
JSON object in the form:
```python
{
    "success": true   #boolean
}
```

### On Error
JSON object in the form:
```python
{
    "success": false,   #boolean
    "error": "<error reason>"   #string
}
```

## POST - /new_tracker
Register as a new tracker, getting a full database update.

### Input
Expects an empty JSON object:
```python
{ }
```

### Output
JSON object in the form:
```python
{
     "success": true   #boolean
     "data": "... A full database dump"   #string
}
```

### On Error
JSON object in the form:
```python
{
    "success": false,   #boolean
    "error": "<error reason>"   #string
}
```
