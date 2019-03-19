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

Currently uses port `42069` by default, but will use the port specified in the config file.

## Endpoints
* GET - /file_list
* GET - /file/<file_id>
* GET - /file_by_hash/<file_full_hash>
* GET - /tracker_list
* POST - /add_file
* PUT - /keep_alive
* DELETE - /deregister_file

## GET - /file_list
Gets the list of files that the tracker knows about.

### Input
GET request to the endpoint url.

Ex: `localhost:42069/file_list`

### Output
JSON object in the form:
```python
{
    "success": true,   #boolean
    "files": [
        {
            "id": <file id>,    #integer
            "name": "<file's name>",   #string
            "hash": "<full file hash>" #base64 string
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

Ex: `localhost:42069/file/2`

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
            "hash": "<hash of chunk>"   #string (sha256 hash)
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

Ex: `localhost:42069/file_by_hash/lkjlkjalijfljsdll9823`

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
            "hash": "<hash of chunk>"   #string (sha256 hash)
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

Ex: `localhost:42069/tracker_list`

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
Requires the hash of the file and all its chunks.
If a file with a matching hash already exists, adds the peer as a host for that file.
Peer must provide their guid when adding a file.
If the peer does not already have a guid, they can provide `null` and will be given a guid in the response.

### Input
POST request to the endpoint url with a JSON object.

Ex: `localhost:42069/add_file`

JSON object in the form:
```python
{
    "name": "<file name>",  #string
    "full_hash": "<hash of full file>", #string (sha256 hash)
    "chunks": [
        {
            "id": <chunk id for sequencing>,    #integer
            "name": "<chunk filename>", #string
            "hash": "<hash of chunk>"   #string (sha256 hash)
        },
        ...
    ],
    "guid": "<client's guid>"/null   #string or null
}
```

### Output
JSON object in the form:
```python
{
    "success": true,    #boolean
    "file_id": <the existing id if the tracker already has it, or the new one if it didnt>,   #integer
    "guid": "<echoed guid if you had one already, otherwise your newly assigned one"    #string
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

## POST - /keep_alive
Tells the server you're still there hosting.
Updates your keep alive timestamp on the server.
Requires a guid.

### Input
PUT request to the endpoint url with a JSON object.

Ex: `localhost:42069/keep_alive`

JSON object in the form:
```python
{
    "guid": "<client's guid>"   #string
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

## POST - /deregister_file
Removes you as a host for the specified file.
Requires a guid.
If a file has no hosts remaining, removes it.

### Input
DELETE request to the endpoint url with a JSON object.

Ex: `localhost:42069/keep_alive`

JSON object in the form:
```python
{
    "file_id": <files id in the tracker db>,   #integer
    "guid": "<client's guid>"   #string
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
