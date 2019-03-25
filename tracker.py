#!/usr/bin/env python3
import argparse
from pathlib import Path

from api import app, constants, models
import toml
from tracker_init import tracker_init

# default settings
CONFIG_FILE = Path("config.toml")
INITIAL_TRACKER = None
SERVER_PORT = 42069
DEBUG = False
DB_PATH = Path("tracker.db")
KEEPALIVE_TIMEOUT = 5 * 60    # 5 minutes

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", metavar="[config filename]", help="specify a nonstandard config file")
    parser.add_argument(
        "-t",
        "--initial-tracker",
        metavar="[initial tracker ip]",
        help="specify an initial tracker IP to connect to, or 'none'",
    )
    args = parser.parse_args()

    if args.config is None:
        config_file = CONFIG_FILE
    else:
        config_file = args.config

    if args.initial_tracker is None:
        initial_tracker = INITIAL_TRACKER
    else:
        initial_tracker = args.initial_tracker.lower()

    try:
        with Path(config_file).open() as config:
            settings = toml.load(config)["settings"]

        print("Loading settings from \"{}\"...".format(config_file))
        port = settings["server_port"]
        debug_mode = settings["debug_mode"]
        db_path = Path(settings["db_path"])
        keepalive_timeout = settings["keepalive_timeout"]
        constants.BROADCAST_THREAD_COUNT = settings["broadcast_thread_count"]
        constants.MAX_TRACKER_FAILURES = settings["max_tracker_failures"]

    except Exception:
        print("Error in config file \"{}\", loading default settings...".format(config_file))
        port = SERVER_PORT
        debug_mode = DEBUG
        db_path = DB_PATH
        keepalive_timeout = KEEPALIVE_TIMEOUT

    constants.set_keepalive_timeout(keepalive_timeout)
    models.load_database(db_path)
    tracker_init(initial_tracker, db_path)
    app.run(port=port, debug=debug_mode)
