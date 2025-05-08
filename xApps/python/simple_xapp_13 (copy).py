#!/usr/bin/env python3

import time
import datetime
import argparse
import signal
import logging
import requests  # Add this import for HTTP requests
from lib.xAppBase import xAppBase
from central_controller import CentralController

class MyXapp(xAppBase):
    def __init__(self, config, http_server_port, rmr_port, controller, xapp_id, flask_server_url):
        super(MyXapp, self).__init__(config, http_server_port, rmr_port)
        self.controller = controller
        self.xapp_id = xapp_id
        self.start_time = time.time()
        self.processed_messages = 0
        self.latencies = []
        self.flask_server_url = flask_server_url

        # Set up logging for metrics
        log_filename = f'xapp_{xapp_id}_metrics.log'
        logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s - %(message)s')

    def notify_dashboard_onboard(self):
        # Notify the central controller (dashboard) that this xApp is onboarded
        try:
            # Directly notify CentralController instead of using an HTTP request for onboard
            self.controller.onboard_xapp(self.xapp_id)
            
            response = requests.post(f'{self.flask_server_url}/xapp-onboarded', json={'xapp_id': self.xapp_id})
            if response.status_code == 200:
                print(f"xApp {self.xapp_id} successfully onboarded and notified dashboard.")
            else:
                print(f"Failed to notify dashboard about onboarding of xApp {self.xapp_id}. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error notifying dashboard: {e}")

    @xAppBase.start_function
    def start(self, e2_node_id, ue_id):
        self.notify_dashboard_onboard()  # Notify dashboard when xApp starts
        while self.running:
            start_processing_time = time.time()
            min_prb_ratio = 1
            max_prb_ratio = 5
            current_time = datetime.datetime.now()
            print("{} [{}] Send RIC Control Request to E2 node ID: {} for UE ID: {}, PRB_min: {}, PRB_max: {}".format(
                current_time.strftime("%H:%M:%S"), self.xapp_id, e2_node_id, ue_id, min_prb_ratio, max_prb_ratio))

            # Log the message with the CentralController
            self.controller.log_message(self.xapp_id, e2_node_id, ue_id, min_prb_ratio, max_prb_ratio, current_time)
            self.e2sm_rc.control_slice_level_prb_quota(e2_node_id, ue_id, min_prb_ratio=1, max_prb_ratio=5, dedicated_prb_ratio=51, ack_request=1)

            min_prb_ratio = 1
            max_prb_ratio = 50
            print("{} Send RIC Control Request to E2 node ID: {} for UE ID: {}, PRB_min: {}, PRB_max: {}".format(current_time.strftime("%H:%M:%S"), e2_node_id, ue_id, min_prb_ratio, max_prb_ratio))
            self.e2sm_rc.control_slice_level_prb_quota(e2_node_id, ue_id, min_prb_ratio=1, max_prb_ratio=max_prb_ratio, dedicated_prb_ratio=100, ack_request=1)

            # Record throughput and latency metrics
            self.processed_messages += 1
            end_processing_time = time.time()
            latency = end_processing_time - start_processing_time
            self.latencies.append(latency)

            # Print metrics periodically
            if self.processed_messages % 10 == 0:
                self.print_metrics()

            time.sleep(5)

    def print_metrics(self):
        elapsed_time = time.time() - self.start_time
        throughput = self.processed_messages / elapsed_time
        average_latency = sum(self.latencies) / len(self.latencies) if self.latencies else 0
        metrics = (f"Throughput: {throughput:.2f} messages/sec\n"
                   f"Average Latency: {average_latency:.4f} seconds")
        print(metrics)
        logging.info(metrics)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='My example xApp')
    parser.add_argument("--config", type=str, default='', help="xApp config file path")
    parser.add_argument("--http_server_port", type=int, default=8090, help="HTTP server listen port")
    parser.add_argument("--rmr_port", type=int, default=4560, help="RMR port")
    parser.add_argument("--e2_node_id", type=str, default='gnbd_001_001_00019b_0', help="E2 Node ID")
    parser.add_argument("--ran_func_id", type=int, default=3, help="E2SM RC RAN function ID")
    parser.add_argument("--ue_id", type=int, default=0, help="UE ID")
    parser.add_argument("--xapp_id", type=str, required=True, help="Unique ID for the xApp instance")
    parser.add_argument("--flask_server_url", type=str, default='http://localhost:5000', help="URL of the Flask dashboard server")

    args = parser.parse_args()
    config = args.config
    e2_node_id = args.e2_node_id
    ran_func_id = args.ran_func_id
    ue_id = args.ue_id
    xapp_id = args.xapp_id
    flask_server_url = args.flask_server_url

    # Create CentralController
    controller = CentralController()

    # Create MyXapp with controller and Flask server URL
    myXapp = MyXapp(config, args.http_server_port, args.rmr_port, controller, xapp_id, flask_server_url)
    myXapp.e2sm_rc.set_ran_func_id(ran_func_id)

    signal.signal(signal.SIGQUIT, myXapp.signal_handler)
    signal.signal(signal.SIGTERM, myXapp.signal_handler)
    signal.signal(signal.SIGINT, myXapp.signal_handler)

    myXapp.start(e2_node_id, ue_id)

