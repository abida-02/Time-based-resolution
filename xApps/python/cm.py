#!/usr/bin/env python3

import time
import datetime
import argparse
import signal
import requests
from lib.xAppBase import xAppBase
from central_controller import CentralController

class MyXapp(xAppBase):
    def __init__(self, config, http_server_port, rmr_port, controller, flask_server_url, stop_xapp1_url, stop_xapp2_url):
        super(MyXapp, self).__init__(config, http_server_port, rmr_port)
        self.controller = controller
        self.flask_server_url = flask_server_url
        self.stop_xapp1_url = stop_xapp1_url
        self.stop_xapp2_url = stop_xapp2_url

    def stop_other_xapps(self):
        """
        Sends a stop signal to xApp 1 and xApp 2 using HTTP requests to their respective endpoints.
        """
        try:
            # Stop xApp 1
            response_xapp1 = requests.post(self.stop_xapp1_url, json={'action': 'stop'})
            if response_xapp1.status_code == 200:
                print("Successfully stopped xApp 1.")
            else:
                print(f"Failed to stop xApp 1. Status code: {response_xapp1.status_code}")

            # Stop xApp 2
            response_xapp2 = requests.post(self.stop_xapp2_url, json={'action': 'stop'})
            if response_xapp2.status_code == 200:
                print("Successfully stopped xApp 2.")
            else:
                print(f"Failed to stop xApp 2. Status code: {response_xapp2.status_code}")

        except Exception as e:
            print(f"Error stopping xApps: {e}")

    @xAppBase.start_function
    def start(self, e2_node_id, ue_id):
        # Notify dashboard that this xApp is onboarded (optional)
        self.controller.onboard_xapp("MyXapp3")

        # Stop xApp 1 and xApp 2
        self.stop_other_xapps()

        # Control logic for the 3rd xApp
        while self.running:
            min_prb_ratio = 12
            max_prb_ratio = 25
            current_time = datetime.datetime.now()
            print(f"{current_time.strftime('%H:%M:%S')} Send RIC Control Request for PRB_min: {min_prb_ratio}, PRB_max: {max_prb_ratio}")
            
            # Example of sending control to the RIC for slice level PRB quota
            self.e2sm_rc.control_slice_level_prb_quota(e2_node_id, ue_id, min_prb_ratio=min_prb_ratio, max_prb_ratio=max_prb_ratio, dedicated_prb_ratio=100, ack_request=1)
            
            time.sleep(5)  # Delay between control messages


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='My example xApp')
    parser.add_argument("--config", type=str, default='', help="xApp config file path")
    parser.add_argument("--http_server_port", type=int, default=8093, help="HTTP server listen port")
    parser.add_argument("--rmr_port", type=int, default=4560, help="RMR port")
    parser.add_argument("--e2_node_id", type=str, default='gnbd_001_001_00019b_0', help="E2 Node ID")
    parser.add_argument("--ran_func_id", type=int, default=3, help="E2SM RC RAN function ID")
    parser.add_argument("--ue_id", type=int, default=0, help="UE ID")
    parser.add_argument("--flask_server_url", type=str, default='http://localhost:5000', help="Flask server URL for central dashboard")
    parser.add_argument("--stop_xapp1_url", type=str, required=True, help="URL to stop xApp 1")
    parser.add_argument("--stop_xapp2_url", type=str, required=True, help="URL to stop xApp 2")

    args = parser.parse_args()
    config = args.config
    e2_node_id = args.e2_node_id
    ran_func_id = args.ran_func_id
    ue_id = args.ue_id
    flask_server_url = args.flask_server_url
    stop_xapp1_url = args.stop_xapp1_url
    stop_xapp2_url = args.stop_xapp2_url

    # Create CentralController instance
    controller = CentralController()

    # Create MyXapp instance with controller and Flask server URL
    myXapp = MyXapp(config, args.http_server_port, args.rmr_port, controller, flask_server_url, stop_xapp1_url, stop_xapp2_url)
    myXapp.e2sm_rc.set_ran_func_id(ran_func_id)

    # Connect exit signals
    signal.signal(signal.SIGQUIT, myXapp.signal_handler)
    signal.signal(signal.SIGTERM, myXapp.signal_handler)
    signal.signal(signal.SIGINT, myXapp.signal_handler)

    # Start xApp
    myXapp.start(e2_node_id, ue_id)

