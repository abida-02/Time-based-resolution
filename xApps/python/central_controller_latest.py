import threading
import time
from datetime import datetime, timedelta
import logging
import requests  # Import requests to make HTTP requests

class CentralController:
    def __init__(self):
        self.message_log = []
        self.lock = threading.Lock()
        self.onboarded_xapps = set()  # Track onboarded xApps
        logging.basicConfig(filename='central_controller.log', level=logging.INFO, format='%(asctime)s - %(message)s')

    def onboard_xapp(self, xapp_id):
        """Handle xApp onboarding and detect conflicts if necessary."""
        with self.lock:
            if xapp_id not in self.onboarded_xapps:
                self.onboarded_xapps.add(xapp_id)
                self.notify_dashboard(f"xApp {xapp_id} onboarded")
                # Immediately check for any conflicts upon onboarding the new xApp
                self.detect_conflict_onboarding(xapp_id)

    def log_message(self, xapp_id, e2_node_id, ue_id, min_prb_ratio, max_prb_ratio, timestamp):
        """Log messages from xApps and detect conflicts."""
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

            # Detect conflicts whenever a new message is logged
            self.detect_conflict()

    def detect_conflict_onboarding(self, new_xapp_id):
        """Check for conflicts immediately after onboarding a new xApp."""
        print(f"Checking for conflicts upon onboarding xApp {new_xapp_id}")

        # Check if there are any existing messages from other xApps
        for message in self.message_log:
            if message['xapp_id'] != new_xapp_id:
                for onboarded_xapp_id in self.onboarded_xapps:
                    if onboarded_xapp_id != new_xapp_id:
                        existing_messages = [msg for msg in self.message_log if msg['xapp_id'] == onboarded_xapp_id]
                        for existing_msg in existing_messages:
                            if self.is_conflict(existing_msg, message):
                                conflict_msg = f"Conflict detected between messages from  {existing_msg['xapp_id']} and  {message['xapp_id']}"
                                print(conflict_msg)
                                logging.info(conflict_msg)
                                self.notify_dashboard(conflict_msg)
                                self.resolve_conflict(existing_msg, message)
                                return  # Resolve the first detected conflict and exit

    def detect_conflict(self):
        """Detect conflicts based on recent messages."""
        current_time = datetime.now()
        time_window = timedelta(seconds=5)  # Define the short time frame for conflict detection
        recent_messages = [msg for msg in self.message_log if current_time - msg['timestamp'] <= time_window]

        print(f"Checking for conflicts among {len(recent_messages)} recent messages")

        if len(recent_messages) > 1:
            for i in range(len(recent_messages)):
                for j in range(i + 1, len(recent_messages)):
                    if self.is_conflict(recent_messages[i], recent_messages[j]):
                        conflict_msg = f"Conflict detected between messages from  {recent_messages[i]['xapp_id']} and  {recent_messages[j]['xapp_id']}"
                        print(conflict_msg)
                        logging.info(conflict_msg)
                        self.notify_dashboard(conflict_msg)
                        self.resolve_conflict(recent_messages[i], recent_messages[j])
                        return  # Resolve the first detected conflict and exit

    def is_conflict(self, msg1, msg2):
        """Detect conflicts when messages have different PRB allocations for the same e2_node_id and ue_id."""
        return (msg1['e2_node_id'] == msg2['e2_node_id'] and
                msg1['ue_id'] == msg2['ue_id'] and
                (msg1['min_prb_ratio'] != msg2['min_prb_ratio'] or msg1['max_prb_ratio'] != msg2['max_prb_ratio']))

    def resolve_conflict(self, msg1, msg2):
        """Resolve conflicts using a timestamp-based strategy."""
        print(f"Conflict detected. Both  {msg1['xapp_id']} and  {msg2['xapp_id']} sent conflicting messages.")
        logging.info(f"Conflict detected between xApp {msg1['xapp_id']} and xApp {msg2['xapp_id']}")

        # Timestamp-based resolution (first come, first served)
        if msg1['timestamp'] < msg2['timestamp']:
            self.apply_message(msg1)
            self.buffer_message(msg2)
        else:
            self.apply_message(msg2)
            self.buffer_message(msg1)

    def apply_message(self, msg):
        """Apply the PRB allocation message to the RAN node."""
        print(f"Applying message from  {msg['xapp_id']} to e2_node_id {msg['e2_node_id']} for ue_id {msg['ue_id']}")
        logging.info(f"Applying message from  {msg['xapp_id']} to e2_node_id {msg['e2_node_id']} for ue_id {msg['ue_id']}")

    def buffer_message(self, msg):
        """Buffer the message and schedule its execution after a delay."""
        print(f"Buffering message from  {msg['xapp_id']} for later execution.")
        logging.info(f"Buffering message from  {msg['xapp_id']} for later execution.")

        # Schedule execution after 20 seconds
        threading.Timer(20, self.execute_buffered_message, [msg]).start()

    def execute_buffered_message(self, msg):
        """Execute a buffered message after the delay."""
        print(f"Executing buffered message from xApp {msg['xapp_id']} after delay.")
        logging.info(f"Executing buffered message from xApp {msg['xapp_id']} after delay.")
        self.apply_message(msg)

    def notify_dashboard(self, message):
        """Notify the dashboard with a message."""
        try:
            requests.post('http://localhost:5000/update', json={'message': message})
        except Exception as e:
            print(f"Failed to send update to dashboard: {e}")

# Usage Example
if __name__ == '__main__':
    controller = CentralController()
    controller.onboard_xapp('xApp1')
    controller.log_message('xApp1', 'gnbd_001_001_00019b_0', 0, 1, 5, datetime.now())
    time.sleep(1)  # Short delay to simulate near-simultaneous messages
    controller.onboard_xapp('xApp2')
    controller.log_message('xApp2', 'gnbd_001_001_00019b_0', 0, 2, 6, datetime.now())

