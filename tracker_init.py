import base64
import binascii
import ipaddress

from api import constants, models
from peewee import DoesNotExist
import requests


def tracker_init(initial_tracker, db_path):
    if initial_tracker is None:
        try:
            tracker_list = map(lambda t: t["ip"], models.get_tracker_list())
        except DoesNotExist:
            print("No tracker specified and no trackers in database, using existing DB (or creating a new one)")
            return
    elif initial_tracker == "none":
        return
    else:
        try:
            ip = ipaddress.ip_address(initial_tracker)
            tracker_list = [ip]
        except ValueError:
            print(f"Error: user specified initial tracker '{initial_tracker}' is not an IP")
            exit(1)

    (database, ip) = _get_database(tracker_list)

    if database is None:
        print("Could not initialize database, try a different initial tracker (see --help)")
        exit(1)

    with open(db_path, mode='wb') as dbfd:
        dbfd.write(database)

    models.load_database(db_path)
    models.add_tracker(ip, "george")


def _get_database(tracker_list):
    for tracker_ip in tracker_list:
        response = requests.post(f"http://{tracker_ip}:{constants.DEFAULT_SERVER_PORT}/new_tracker", json={})

        if response.status_code != requests.codes.ok:
            # Couldn't talk to tracker, try next
            print(f"Got bad response code: {response.status_code} from tracker {tracker_ip}. Trying next tracker")
            continue

        try:
            json = response.json()
        except ValueError:
            # Couldn't parse JSON, try next
            print(f"Could not parse response from tracker {tracker_ip}. Trying next tracker")
            continue

        if not json["success"]:
            # Error making request, try next
            print(f"Request to {tracker_ip}, failed, response JSON follows. Trying next tracker")
            continue

        data_base64 = json["data"]
        try:
            return (base64.b64decode(data_base64, validate=True), tracker_ip)
        except binascii.Error:
            # Couldn't decode base64, try next
            print(f"Could not decode database dump from {tracker_ip}. Trying next tracker")
            continue

    return (None, None)