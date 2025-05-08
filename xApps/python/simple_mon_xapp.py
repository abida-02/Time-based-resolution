# my_xapp.py

import time
import datetime
import argparse
import signal
from conflict_detection import ConflictDetection
from conflict_resolution import ConflictResolution
from lib.xAppBase import xAppBase

class MyXapp(xAppBase):
    def __init__(self, config, http_server_port, rmr_port, xapp_id, conflict_detection):
        super(MyXapp, self).__init__(config, http_server_port, rmr_port)
        self.xapp_id = xapp_id
        self.conflict_detection = conflict_detection
        self.start_time = time.time()

    @xAppBase.start_function
    def start(self, e2_node_id, ue_id):
        while self.running:
            min_prb_ratio = 1
            max_prb_ratio = 5
            current_time = datetime.datetime.now()
            print(f"{current_time.strftime('%H:%M:%S')} [{self.xapp_id}] Send RIC Control Request to E2 node ID: {e2_node_id} for UE ID: {ue_id}, PRB_min: {min_prb_ratio}, PRB_max: {max_prb_ratio}")

            # Add message to the conflict detection queue
            self.conflict_detection.add_message(self.xapp_id, e2_node_id, ue_id, min_prb_ratio, max_prb_ratio, current_time.timestamp())

            time.sleep(5)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='My example xApp')
    parser.add_argument("--config", type=str, default='', help="xApp config file path")
    parser.add_argument("--http_server_port", type=int, default=8091, help="HTTP server listen port")
    parser.add_argument("--rmr_port", type=int, default=4561, help="RMR port")
    parser.add_argument("--e2_node_id", type=str, default='gnbd_001_001_00019b_0', help="E2 Node ID")
    parser.add_argument("--ran_func_id", type=int, default=3, help="E2SM RC RAN function ID")
    parser.add_argument("--ue_id", type=int, default=0, help="UE ID")
    parser.add_argument("--xapp_id", type=str, required=True, help="Unique ID for the xApp instance")

    args = parser.parse_args()
    config = args.config
    e2_node_id = args.e2_node_id
    ran_func_id = args.ran_func_id
    ue_id = args.ue_id
    xapp_id = args.xapp_id

    # Initialize conflict detection and resolution modules
    conflict_resolution = ConflictResolution()
    conflict_detection = ConflictDetection(conflict_resolution)

    # Start the conflict detection thread
    conflict_detection.start()

    # Create MyXapp with conflict detection
    myXapp = MyXapp(config, args.http_server_port, args.rmr_port, xapp_id, conflict_detection)
    myXapp.e2sm_rc.set_ran_func_id(ran_func_id)

    signal.signal(signal.SIGQUIT, myXapp.signal_handler)
    signal.signal(signal.SIGTERM, myXapp.signal_handler)
    signal.signal(signal.SIGINT, myXapp.signal_handler)

    myXapp.start(e2_node_id, ue_id)

