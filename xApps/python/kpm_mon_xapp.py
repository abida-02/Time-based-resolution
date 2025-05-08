#!/usr/bin/env python3

import threading
import time
import datetime
import argparse
import signal
import logging
import requests
import tkinter as tk
from tkinter import scrolledtext
from lib.xAppBase import xAppBase

# TerminalGUI class to create GUI
class TerminalGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Terminal Output")

        # Configure text widget with scrollable feature, black background, and white text
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Helvetica", 12), height=20, width=80, bg="#000000", fg="#FFFFFF")
        self.text_area.pack(expand=True, fill=tk.BOTH)

        # Make text_area read-only initially
        self.text_area.config(state=tk.DISABLED)

        # Configure tags for different colors
        self.text_area.tag_config("green", foreground="#00FF00")
        self.text_area.tag_config("red", foreground="#FF0000")
        self.text_area.tag_config("cyan", foreground="#00FFFF")
        self.text_area.tag_config("purple", foreground="#FF00FF")  # Bright neon purple
        self.text_area.tag_config("yellow", foreground="#FFFF00")  # Yellow for timestamps

    def append_text(self, message, color=None):
        """Appends a new message to the Text widget with optional color."""
        self.text_area.config(state=tk.NORMAL)  # Allow editing to append new text

        words = message.split()
        timestamp_mode = False
        for word in words:
            if timestamp_mode:
                self.text_area.insert(tk.END, word, "yellow")
            elif word.lower() in ["xapp1", "xapp2", "xapp3"]:
                self.text_area.insert(tk.END, word, "green")
            elif word.lower() in ["buffer", "buffering", "buffered"]:
                self.text_area.insert(tk.END, word, "cyan")
            elif word.lower() == "logging":
                self.text_area.insert(tk.END, word, "purple")
            elif "conflict detected" in message.lower():
                self.text_area.insert(tk.END, word, "red")
            elif word.lower() == "at":
                self.text_area.insert(tk.END, word)
                timestamp_mode = True
            else:
                self.text_area.insert(tk.END, word)
            self.text_area.insert(tk.END, " ")  # Add space between words

        self.text_area.insert(tk.END, "\n")  # New line at the end of the message
        self.text_area.yview(tk.END)  # Auto-scroll to the end
        self.text_area.config(state=tk.DISABLED)

class CentralController:
    def __init__(self, terminal_gui):
        self.terminal_gui = terminal_gui
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
                self.terminal_gui.append_text(f"xApp {xapp_id} onboarded")  # Print to terminal GUI
                self.detect_conflict_onboarding(xapp_id)

    def log_message(self, xapp_id, e2_node_id, ue_id, min_prb_ratio, max_prb_ratio, timestamp):
        """Log messages from xApps and detect conflicts."""
        with self.lock:
            message = f"Logging message from xApp {xapp_id} at {timestamp}"
            print(message)
            self.terminal_gui.append_text(message)  # Print to terminal GUI

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
        message = f"Checking for conflicts upon onboarding xApp {new_xapp_id}"
        print(message)
        self.terminal_gui.append_text(message)  # Print to terminal GUI

    def detect_conflict(self):
        """Detect conflicts based on recent messages."""
        current_time = datetime.datetime.now()
        time_window = datetime.timedelta(seconds=5)  # Define the short time frame for conflict detection
        recent_messages = [msg for msg in self.message_log if current_time - msg['timestamp'] <= time_window]

        message = f"Checking for conflicts among {len(recent_messages)} recent messages"
        print(message)
        self.terminal_gui.append_text(message)  # Print to terminal GUI

class MyXapp(xAppBase):
    def __init__(self, config, http_server_port, rmr_port, controller):
        super(MyXapp, self).__init__(config, http_server_port, rmr_port)
        self.controller = controller

    @xAppBase.start_function
    def start(self, e2_node_id, ue_id):
        while self.running:
            # First, send request for min_prb_ratio=12 for 20 seconds
            min_prb_ratio = 12
            max_prb_ratio = 12
            current_time = datetime.datetime.now()
            self.controller.log_message('xApp1', e2_node_id, ue_id, min_prb_ratio, max_prb_ratio, current_time)
            time.sleep(5)

            # Then, switch to max_prb_ratio=25 for the next 20 seconds
            min_prb_ratio = 25
            max_prb_ratio = 50
            current_time = datetime.datetime.now()
            self.controller.log_message('xApp2', e2_node_id, ue_id, min_prb_ratio, max_prb_ratio, current_time)
            time.sleep(5)

def start_controller(terminal_gui):
    """Function to run CentralController logic in a separate thread."""
    controller = CentralController(terminal_gui)
    controller.onboard_xapp('xApp1')
    return controller

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='My example xApp')
    parser.add_argument("--config", type=str, default='', help="xApp config file path")
    parser.add_argument("--http_server_port", type=int, default=8092, help="HTTP server listen port")
    parser.add_argument("--rmr_port", type=int, default=4560, help="RMR port")
    parser.add_argument("--e2_node_id", type=str, default='gnbd_001_001_00019b_0', help="E2 Node ID")
    parser.add_argument("--ue_id", type=int, default=0, help="UE ID")

    args = parser.parse_args()
    config = args.config
    e2_node_id = args.e2_node_id
    ue_id = args.ue_id

    # Initialize GUI
    root = tk.Tk()
    terminal_gui = TerminalGUI(root)

    # Start CentralController
    controller = start_controller(terminal_gui)

    # Create MyXapp with the CentralController
    myXapp = MyXapp(config, args.http_server_port, args.rmr_port, controller)

    # Connect exit signals
    signal.signal(signal.SIGQUIT, myXapp.signal_handler)
    signal.signal(signal.SIGTERM, myXapp.signal_handler)
    signal.signal(signal.SIGINT, myXapp.signal_handler)

    # Start xApp in a separate thread
    xapp_thread = threading.Thread(target=myXapp.start, args=(e2_node_id, ue_id))
    xapp_thread.daemon = True
    xapp_thread.start()

    # Run the Tkinter main loop
    root.mainloop()

