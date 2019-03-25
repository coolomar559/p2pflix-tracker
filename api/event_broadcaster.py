from _thread import interrupt_main
from queue import Empty, Queue
import sys
from threading import Event, Thread
from traceback import print_exc

from api import models
from api.models import constants, Tracker
import requests


# Worker thread for taking events off of the event queue and sending them
# Can be interrupted by using the interrupt function
class BroadCasterThread(Thread):
    def __init__(self, event_broadcaster):
        super(BroadCasterThread, self).__init__()
        self.event_broadcaster = event_broadcaster
        self._interrupted_event = Event()

    def run(self):
        tracker_list = self.event_broadcaster.tracker_list
        while not self._interrupted():
            # Need to make a copy of the list of keys so we don't get dictionary size changed during
            # iteration errors
            for tid in list(tracker_list.keys()):
                if self._interrupted():
                    break

                try:
                    tracker = tracker_list[tid]
                    event = tracker["queue"].get(timeout=5)
                    self._send_event(event, tid, tracker)
                    tracker["queue"].task_done()
                except Empty:
                    continue
                except KeyError:
                    # Trackers may be removed from the list while we're iterating through our copy of
                    # the list of tracker ids, this is fine though so just continue
                    continue

    def interrupt(self):
        self._interrupted_event.set()

    # Returns a boolean for checking if the thread is interrupted or not
    def _interrupted(self):
        self._interrupted_event.is_set()

    # Send an event to the given tracker
    def _send_event(self, event, tid, tracker):
        keep_trying = True
        while keep_trying and not self._interrupted():
            try:
                response = requests.patch(
                    f"http://{tracker['ip']}:{constants.DEFAULT_SERVER_PORT}/tracker_sync",
                    json=event,
                    timeout=30,
                )
                keep_trying = not self._handle_response(response, tid)
            except Exception:
                print(f"Exception in thread {self.ident}:", file=sys.stderr)
                print_exc()
                keep_trying = not self._increment_tracker_fails(tid)

    # Handle a response from trying to send a tracker a new update
    # Returns true upon successfully handling an event, and false upon failure
    def _handle_response(self, response, tid):
        if response.status_code != requests.codes.ok:
            print(f"Thread {self.ident} got not-ok response code: {response.status_code} from tracker with id {tid}")
            return self._increment_tracker_fails(tid)

        try:
            json = response.json()

            if not json["success"] and "dead_tracker" in json and json["dead_tracker"]:
                print(f"Recieved message from tracker with id {tid} indicating death, shutting down")
                interrupt_main()
                return True  # This technically counts as successfully handling an event
            if not json["success"]:
                print(f"Unsuccessful broadcast to tracker with id {tid} on thread {self.ident}")
                print(f"Recieved error: {json['error']}")
                return self._increment_tracker_fails(tid)

            return True
        except ValueError:
            print(f"Could not parse response JSON in thread {self.ident}:", file=sys.stderr)
            print_exc()
            return self._increment_tracker_fails(tid)

    # Increment the number of failures for the tracker with given id
    # Remove the tracker from the tracker list if number of failures is higher than max tracker failures
    # Returns true if the tracker was above max and has officially failed, ending the attempts to send events
    # and false otherwise
    def _increment_tracker_fails(self, tid):
        tracker_list = self.event_broadcaster.tracker_list
        tracker_list[tid]["failures"] += 1

        if tracker_list[tid]["failures"] > constants.MAX_TRACKER_FAILURES:
            self.event_broadcaster.remove_tracker(tid)
            return True

        return False


# Class for broadcasting new events to all known trackers
class EventBroadcaster:
    # Since we need to ensure the database is actually initialized, don't
    # initialize everything on class construction
    def __init__(self):
        self.initialized = False

    # Only to be called after the database is initialized
    def initialize(self):
        self.initialized = True
        self.tracker_list = {}
        self.threads = []
        try:
            trackers = models.get_tracker_list()
        except Tracker.DoesNotExist:
            self.initialized = False
            return

        for tracker in trackers:
            self.tracker_list[tracker["id"]] = {
                "ip": tracker["ip"],
                "queue": Queue(),
                "failures": 0,
            }

        for _ in range(0, constants.BROADCAST_THREAD_COUNT):
            thread = BroadCasterThread(self)
            thread.daemon = True
            thread.start()
            self.threads.append(thread)

    # Add a new tracker event queue
    def new_tracker(self, tracker):
        if not self.initialized:
            self.initialize()

        self.tracker_list[tracker.id] = {
            "ip": tracker.ip,
            "queue": Queue(),
            "failures": 0,
        }

    # Add a new event to all tracker queues
    def new_event(self, event_type, event_ip, event_data):
        if not self.initialized:
            self.initialize()

        for tracker in self.tracker_list.values():
            tracker["queue"].put({
                "event": event_type,
                "event_ip": event_ip,
                "data": event_data,
            })

    # Remove a tracker from the list of trackers
    def remove_tracker(self, tracker_id):
        if not self.initialized:
            self.initialize()

        models.remove_tracker_by_ip(self.tracker_list[tracker_id]["ip"])

        try:
            del self.tracker_list[tracker_id]
        except KeyError:
            pass  # Ignore KeyError since it's fine if the tracker wasn't in the list
