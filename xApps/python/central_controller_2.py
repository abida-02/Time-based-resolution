import threading
import time
from datetime import datetime, timedelta
import logging

class CentralController:
    def __init__(self):
        self.message_log = []
        self.lock = threading.Lock()
        logging.basicConfig(filename='central_controller.log', level=logging.INFO, format='%(asctime)s - %(message)s')

    def log_message(self, xapp_id, e2_node_id, ue_id, min_prb_ratio, max_prb_ratio, timestamp):
        with self.lock:
            print(f"Logging message from xApp {xapp_id} at {timestamp}")
            self.message_log.append({
                'xapp_id': xapp_id,
                'e2_node_id': e2_node_id,
                'ue_id': ue_id,
                'min_prb_ratio': min_prb_ratio,
                'max_prb_ratio': max_prb_ratio,
                'timestamp': timestamp
            })
            self.detect_conflict()

    def detect_conflict(self):
        current_time = datetime.now()
        time_window = timedelta(seconds=5)  # Define the short time frame for conflict detection
        recent_messages = [msg for msg in self.message_log if current_time - msg['timestamp'] <= time_window]

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
        # Print conflict detection message
        print(f"Conflict detected. Both xApp {msg1['xapp_id']} and xApp {msg2['xapp_id']} sent conflicting messages.")
        logging.info(f"Conflict detected between xApp {msg1['xapp_id']} and xApp {msg2['xapp_id']}")

        # Timestamp-based resolution (first come, first served)
        if msg1['timestamp'] < msg2['timestamp']:
            self.apply_message(msg1)
            self.buffer_message(msg2)
        else:
            self.apply_message(msg2)
            self.buffer_message(msg1)

    def apply_message(self, msg):
        # Apply the PRB allocation message to the RAN node
        print(f"Applying message from xApp {msg['xapp_id']} to e2_node_id {msg['e2_node_id']} for ue_id {msg['ue_id']}")
        logging.info(f"Applying message from xApp {msg['xapp_id']} to e2_node_id {msg['e2_node_id']} for ue_id {msg['ue_id']}")

    def buffer_message(self, msg):
        # Store the message and schedule its execution after 20 seconds
        print(f"Buffering message from xApp {msg['xapp_id']} for later execution.")
        logging.info(f"Buffering message from xApp {msg['xapp_id']} for later execution.")

        # Schedule execution after 20 seconds
        threading.Timer(20, self.execute_buffered_message, [msg]).start()

    def execute_buffered_message(self, msg):
        print(f"Executing buffered message from xApp {msg['xapp_id']} after delay.")
        logging.info(f"Executing buffered message from xApp {msg['xapp_id']} after delay.")
        self.apply_message(msg)

    def notify_xapp(self, xapp_id, message):
        # Notify the xApp about the conflict resolution
        print(f"Notify xApp {xapp_id}: {message}")
        logging.info(f"Notify xApp {xapp_id}: {message}")

# Usage Example
if __name__ == '__main__':
    controller = CentralController()
    controller.log_message('xApp1', 'gnbd_001_001_00019b_0', 0, 1, 5, datetime.now())
    time.sleep(1)  # Short delay to simulate near-simultaneous messages
    controller.log_message('xApp2', 'gnbd_001_001_00019b_0', 0, 2, 6, datetime.now())

