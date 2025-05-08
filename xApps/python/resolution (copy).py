#!/usr/bin/env python3

import time
import datetime
import argparse
import signal
import os
import subprocess  # To run shell commands
from lib.xAppBase import xAppBase

class MyXapp(xAppBase):
    def __init__(self, config, http_server_port, rmr_port):
        super(MyXapp, self).__init__(config, http_server_port, rmr_port)

    # Helper function to find the PID of the process using a specific port
    def get_pid_from_port(self, port):
        try:
            # Run the lsof command to find the PID using the port
            result = subprocess.run(['lsof', '-i', f':{port}'], stdout=subprocess.PIPE, text=True)
            lines = result.stdout.splitlines()
            # Look for the line that has the PID, usually the second line
            if len(lines) > 1:
                pid = int(lines[1].split()[1])  # Extract the PID
                return pid
            else:
                print(f"No process found using port {port}")
                return None
        except Exception as e:
            print(f"Error finding PID for port {port}: {e}")
            return None

    # Mark the function as xApp start function using xAppBase.start_function decorator.
    # It is required to start the internal msg receive loop.
    @xAppBase.start_function
    def start(self, e2_node_id, ue_id):
        # Stop HTTP servers running on ports 8091 and 8092
        for port in [8091, 8092]:
            pid = self.get_pid_from_port(port)
            if pid:
                print(f"Sending SIGTERM to process running on port {port} (PID: {pid})")
                try:
                    os.kill(pid, signal.SIGTERM)  # Send SIGTERM to stop the process
                except Exception as e:
                    print(f"Error stopping process on port {port}: {e}")
            else:
                print(f"No process found using port {port}")

        # Switching control every 5 seconds
        while self.running:
            # First, send request for min_prb_ratio=12 for 20 seconds
            min_prb_ratio = 12
            max_prb_ratio = 12
            current_time = datetime.datetime.now()
            print(f"{current_time.strftime('%H:%M:%S')} Send RIC Control Request for xApp1 PRB_min: {min_prb_ratio}, PRB_max: {max_prb_ratio}")
            self.e2sm_rc.control_slice_level_prb_quota(e2_node_id, ue_id, min_prb_ratio=min_prb_ratio, max_prb_ratio=max_prb_ratio, dedicated_prb_ratio=100, ack_request=1)
            time.sleep(5)  # Wait for 20 seconds

            # Then, switch to max_prb_ratio=25 for the next 20 seconds
            min_prb_ratio = 25
            max_prb_ratio = 50
            current_time = datetime.datetime.now()
            print(f"{current_time.strftime('%H:%M:%S')} Send RIC Control Request for xApp2 PRB_min: {min_prb_ratio}, PRB_max: {max_prb_ratio}")
            self.e2sm_rc.control_slice_level_prb_quota(e2_node_id, ue_id, min_prb_ratio=min_prb_ratio, max_prb_ratio=max_prb_ratio, dedicated_prb_ratio=100, ack_request=1)
            time.sleep(5)  # Wait for another 5 seconds


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='My example xApp')
    parser.add_argument("--config", type=str, default='', help="xApp config file path")
    parser.add_argument("--http_server_port", type=int, default=8092, help="HTTP server listen port")
    parser.add_argument("--rmr_port", type=int, default=4560, help="RMR port")
    parser.add_argument("--e2_node_id", type=str, default='gnbd_001_001_00019b_0', help="E2 Node ID")
    parser.add_argument("--ran_func_id", type=int, default=3, help="E2SM RC RAN function ID")
    parser.add_argument("--ue_id", type=int, default=0, help="UE ID")

    args = parser.parse_args()
    config = args.config
    e2_node_id = args.e2_node_id
    ran_func_id = args.ran_func_id
    ue_id = args.ue_id

    # Create MyXapp.
    myXapp = MyXapp(config, args.http_server_port, args.rmr_port)
    myXapp.e2sm_rc.set_ran_func_id(ran_func_id)

    # Connect exit signals.
    signal.signal(signal.SIGQUIT, myXapp.signal_handler)
    signal.signal(signal.SIGTERM, myXapp.signal_handler)
    signal.signal(signal.SIGINT, myXapp.signal_handler)

    # Start xApp.
    myXapp.start(e2_node_id, ue_id)

