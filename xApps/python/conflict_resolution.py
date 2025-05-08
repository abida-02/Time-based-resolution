# conflict_resolution.py

import time

class ConflictResolution:
    def __init__(self):
        self.conflict_log = []

    def resolve_conflict(self, message1, message2):
        xapp1, e2_node_id1, ue_id1, min_prb_ratio1, max_prb_ratio1, timestamp1 = message1
        xapp2, e2_node_id2, ue_id2, min_prb_ratio2, max_prb_ratio2, timestamp2 = message2

        print(f"Conflict detected between {xapp1} and {xapp2} for E2 Node {e2_node_id1}, UE {ue_id1}")

        # Decide which message to process first based on timestamp
        if timestamp1 < timestamp2:
            print(f"Executing {xapp1} immediately and delaying {xapp2}")
            self.execute_message(message1)
            time.sleep(20)  # Delay of 20 seconds
            self.execute_message(message2)
        else:
            print(f"Executing {xapp2} immediately and delaying {xapp1}")
            self.execute_message(message2)
            time.sleep(20)  # Delay of 20 seconds
            self.execute_message(message1)

    def execute_message(self, message):
        xapp_id, e2_node_id, ue_id, min_prb_ratio, max_prb_ratio, timestamp = message
        print(f"Executing {xapp_id}'s control command for E2 Node {e2_node_id}, UE {ue_id} with PRB_min: {min_prb_ratio}, PRB_max: {max_prb_ratio}")
        # This is where you would actually call the control command, e.g., self.e2sm_rc.control_slice_level_prb_quota(...)

