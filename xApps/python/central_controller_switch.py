import threading
import time
from datetime import datetime
import logging
import requests

class CentralController:
    def __init__(self):
        self.message_log = []
        self.lock = threading.Lock()
        self.onboarded_xapps = set()  # Track onboarded xApps
        logging.basicConfig(filename='central_controller.log', level=logging.INFO, format='%(asctime)s - %(message)s')

    def onboard_xapp(self, xapp_id):
        """Handle xApp onboarding."""
        with self.lock:
            if xapp_id not in self.onboarded_xapps:
                self.onboarded_xapps.add(xapp_id)
                self.notify_dashboard(f"xApp {xapp_id} onboarded")

    def log_message(self, xapp_id, e2_node_id, ue_id, min_prb_ratio, max_prb_ratio):
        """Log messages from xApps."""
        with self.lock:
            timestamp = datetime.now()
            print(f"Logging message from xApp {xapp_id} at {timestamp}")

            self.message_log.append({
                'xapp_id': xapp_id,
                'e2_node_id': e2_node_id,
                'ue_id': ue_id,
                'min_prb_ratio': min_prb_ratio,
                'max_prb_ratio': max_prb_ratio,
                'timestamp': timestamp
            })

            # Apply the message directly
            self.apply_message({
                'xapp_id': xapp_id,
                'e2_node_id': e2_node_id,
                'ue_id': ue_id,
                'min_prb_ratio': min_prb_ratio,
                'max_prb_ratio': max_prb_ratio
            })

    def apply_message(self, msg):
        """Apply the PRB allocation message to the RAN node."""
        print(f"Applying message from {msg['xapp_id']} to e2_node_id {msg['e2_node_id']} for ue_id {msg['ue_id']}")
        logging.info(f"Applying message from {msg['xapp_id']} to e2_node_id {msg['e2_node_id']} for ue_id {msg['ue_id']}")

    def notify_dashboard(self, message):
        """Notify the dashboard with a message."""
        try:
            requests.post('http://localhost:5000/update', json={'message': message})
        except Exception as e:
            print(f"Failed to send update to dashboard: {e}")

    def check_for_conflicts(self):
        """Check if there's any conflict between the two xApps' messages."""
        if len(self.message_log) < 2:
            return False  # Not enough messages to detect conflict

        # Get the last two messages from xApp1 and xApp2
        xapp1_messages = [msg for msg in self.message_log if msg['xapp_id'] == 'xApp1']
        xapp2_messages = [msg for msg in self.message_log if msg['xapp_id'] == 'xApp2']

        if not xapp1_messages or not xapp2_messages:
            return False  # Not enough messages to compare

        latest_xapp1_msg = xapp1_messages[-1]
        latest_xapp2_msg = xapp2_messages[-1]

        # Conflict if they request different PRBs for the same e2_node_id and ue_id
        return (latest_xapp1_msg['e2_node_id'] == latest_xapp2_msg['e2_node_id'] and
                latest_xapp1_msg['ue_id'] == latest_xapp2_msg['ue_id'] and
                (latest_xapp1_msg['min_prb_ratio'] != latest_xapp2_msg['min_prb_ratio'] or
                 latest_xapp1_msg['max_prb_ratio'] != latest_xapp2_msg['max_prb_ratio']))

    def resolve_conflict(self):
        """Resolve conflicts by favoring one xApp based on timestamp."""
        # Assuming the latest messages are conflicting, apply one of them based on timestamps
        xapp1_messages = [msg for msg in self.message_log if msg['xapp_id'] == 'xApp1']
        xapp2_messages = [msg for msg in self.message_log if msg['xapp_id'] == 'xApp2']

        if not xapp1_messages or not xapp2_messages:
            return

        latest_xapp1_msg = xapp1_messages[-1]
        latest_xapp2_msg = xapp2_messages[-1]

        # Use timestamp to decide which message gets applied
        if latest_xapp1_msg['timestamp'] < latest_xapp2_msg['timestamp']:
            print(f"Conflict resolved: Applying xApp1 policy (older message)")
            self.apply_message(latest_xapp1_msg)
        else:
            print(f"Conflict resolved: Applying xApp2 policy (older message)")
            self.apply_message(latest_xapp2_msg)

    def alternate_execution(self, e2_node_id, ue_id, min_prb_ratio_1, max_prb_ratio_1, min_prb_ratio_2, max_prb_ratio_2):
        """Alternate between xApp1 and xApp2 execution indefinitely."""
        xapp1_id = 'xApp1'
        xapp2_id = 'xApp2'
        x = 0  # Counter to alternate between policies

        while True:
            if x % 2 == 0:
                # Execute xApp1 Policy
                print(f"Sending Policy from {xapp1_id} with PRB_min: {min_prb_ratio_1}, PRB_max: {max_prb_ratio_1}")
                self.log_message(xapp1_id, e2_node_id, ue_id, min_prb_ratio_1, max_prb_ratio_1)
            else:
                # Execute xApp2 Policy
                print(f"Sending Policy from {xapp2_id} with PRB_min: {min_prb_ratio_2}, PRB_max: {max_prb_ratio_2}")
                self.log_message(xapp2_id, e2_node_id, ue_id, min_prb_ratio_2, max_prb_ratio_2)

            # Check for conflicts after each execution
            if self.check_for_conflicts():
                print("Conflict detected between xApp1 and xApp2!")
                self.resolve_conflict()

            # Increment x to alternate the policy in the next iteration
            x += 1

            # Simulate time interval between policy switches (e.g., 20 seconds)
            time.sleep(20)

# Usage Example
if __name__ == '__main__':
    controller = CentralController()
    
    # Onboard both xApps before starting the alternating execution
    controller.onboard_xapp('xApp1')
    controller.onboard_xapp('xApp2')

    # Start alternating execution between xApp1 and xApp2
    controller.alternate_execution(
        e2_node_id='gnbd_001_001_00019b_0',
        ue_id=0,
        min_prb_ratio_1=12,  # PRB for xApp1
        max_prb_ratio_1=12,  # PRB for xApp1
        min_prb_ratio_2=25,  # PRB for xApp2
        max_prb_ratio_2=25   # PRB for xApp2
    )

