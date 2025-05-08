# conflict_detection.py

from queue import Queue
from threading import Thread
import time

class ConflictDetection:
    def __init__(self, conflict_resolution):
        self.message_queue = Queue()
        self.conflict_resolution = conflict_resolution
        self.processed_messages = {}
        self.running = True

    def add_message(self, xapp_id, e2_node_id, ue_id, min_prb_ratio, max_prb_ratio, timestamp):
        self.message_queue.put((xapp_id, e2_node_id, ue_id, min_prb_ratio, max_prb_ratio, timestamp))

    def detect_conflict(self):
        while self.running:
            if not self.message_queue.empty():
                message = self.message_queue.get()
                xapp_id, e2_node_id, ue_id, min_prb_ratio, max_prb_ratio, timestamp = message

                # Check for conflicts
                if (e2_node_id, ue_id) in self.processed_messages:
                    previous_message = self.processed_messages[(e2_node_id, ue_id)]
                    previous_xapp_id = previous_message[0]
                    if previous_xapp_id != xapp_id:
                        # Conflict detected
                        self.conflict_resolution.resolve_conflict(previous_message, message)
                    else:
                        # No conflict, just update the processed message
                        self.processed_messages[(e2_node_id, ue_id)] = message
                else:
                    # No previous message, store this one
                    self.processed_messages[(e2_node_id, ue_id)] = message

            time.sleep(1)

    def start(self):
        detection_thread = Thread(target=self.detect_conflict)
        detection_thread.start()

