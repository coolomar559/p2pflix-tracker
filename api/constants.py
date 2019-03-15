from datetime import timedelta

KEEP_ALIVE_TIMEOUT = timedelta(minutes=5)   # default timeout is 5 minutes


def set_keepalive_timeout(seconds):
    global KEEP_ALIVE_TIMEOUT
    KEEP_ALIVE_TIMEOUT = timedelta(seconds=seconds)
