from api import app


@app.route('/file_list', methods=['GET'])
def get_file_list():
    # pull the list of file ids and names from db and convert to json
    return "this will be a list of available files"

@app.route('/file/<id>', methods=['GET'])
def get_file(id):
    # pull the file metadata from the db (name, list of peers, list of chunks, etc)
    return "this will be file {}'s metadata, if it exists".format(id)

@app.route('/tracker_list', methods=['GET'])
def get_tracker_list():
    # pull the list of other trackers from the db
    return "this will be the list of trackers"