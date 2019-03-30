from datetime import timedelta

KEEP_ALIVE_TIMEOUT = timedelta(minutes=5)   # default timeout is 5 minutes
BROADCAST_THREAD_COUNT = 4
MAX_TRACKER_FAILURES = 3
DEFAULT_SERVER_PORT = 42069


def set_keepalive_timeout(seconds):
    global KEEP_ALIVE_TIMEOUT
    KEEP_ALIVE_TIMEOUT = timedelta(seconds=seconds)
