#!/usr/bin/env python3 
import threading
import time
from datetime import datetime, timedelta
import logging

class CentralController:
    def __init__(self):
        self.message_queue = []
        self.lock = threading.Lock()
        logging.basicConfig(filename='central_controller.log', level=logging.INFO, format='%(asctime)s - %(message)s')

    def log_message(self, xapp_id, e2_node_id, ue_id, min_prb_ratio, max_prb_ratio, timestamp):
        with self.lock:
            print(f"Logging message from xApp {xapp_id} at {timestamp}")
            message = {
                'xapp_id': xapp_id,
                'e2_node_id': e2_node_id,
                'ue_id': ue_id,
                'min_prb_ratio': min_prb_ratio,
                'max_prb_ratio': max_prb_ratio,
                'timestamp': timestamp
            }
            self.message_queue.append(message)
            self.detect_conflict()

    def detect_conflict(self):
        current_time = datetime.now()
        time_window = timedelta(seconds=5)  # Define the short time frame for conflict detection
        recent_messages = [msg for msg in self.message_queue if current_time - msg['timestamp'] <= time_window]

        print(f"Checking for conflicts among {len(recent_messages)} recent messages")

        if len(recent_messages) > 1:
            for i in range(len(recent_messages)):
                for j in range(i + 1, len(recent_messages)):
                    if self.is_conflict(recent_messages[i], recent_messages[j]):
                        conflict_msg = f"Conflict detected between messages from xApp {recent_messages[i]['xapp_id']} and xApp {recent_messages[j]['xapp_id']}"
                        print(conflict_msg)
                        logging.info(conflict_msg)
                        self.resolve_conflict(recent_messages[i], recent_messages[j])
                        return  # Resolve the first detected conflict and exit

    def is_conflict(self, msg1, msg2):
        # Detect conflicts when messages have different PRB allocations for the same e2_node_id and ue_id
        return (msg1['e2_node_id'] == msg2['e2_node_id'] and
                msg1['ue_id'] == msg2['ue_id'] and
                (msg1['min_prb_ratio'] != msg2['min_prb_ratio'] or msg1['max_prb_ratio'] != msg2['max_prb_ratio']))

    def resolve_conflict(self, msg1, msg2):
        # Execute the message that arrived first
        self.apply_message(msg1)

        # Hold the second message for 20 seconds
        print(f"Holding message from xApp {msg2['xapp_id']} for 20 seconds.")
        logging.info(f"Holding message from xApp {msg2['xapp_id']} for 20 seconds.")
        threading.Timer(20, self.swap_messages, [msg1, msg2]).start()

    def swap_messages(self, msg1, msg2):
        # After 20 seconds, stop the first xApp and execute the second xApp's message
        self.stop_xapp(msg1['xapp_id'])
        self.apply_message(msg2)

    def apply_message(self, msg):
        # Apply the PRB allocation message to the RAN node
        print(f"Applying message from xApp {msg['xapp_id']} to e2_node_id {msg['e2_node_id']} for ue_id {msg['ue_id']}")
        logging.info(f"Applying message from xApp {msg['xapp_id']} to e2_node_id {msg['e2_node_id']} for ue_id {msg['ue_id']}")

    def stop_xapp(self, xapp_id):
        # Stop the xApp that has been executing
        print(f"Stopping xApp {xapp_id}")
        logging.info(f"Stopping xApp {xapp_id}")
        # You need to implement the logic to stop the xApp from here.
        # For example, you could send a signal to the xApp or use some IPC mechanism.

    def notify_xapp(self, xapp_id, message):
        # Notify the xApp about the conflict resolution
        print(f"Notify xApp {xapp_id}: {message}")
        logging.info(f"Notify xApp {xapp_id}: {message}")


