import threading
import time
from datetime import datetime, timedelta
import logging
import requests
import tkinter as tk
from tkinter import scrolledtext


class TerminalGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Terminal Output")

        # Configure text widget with scrollable feature, black background, and white text
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Helvetica", 20), height=20, width=80, bg="#000000", fg="#FFFFFF")
        self.text_area.pack(expand=True, fill=tk.BOTH)

        # Make text_area read-only initially
        self.text_area.config(state=tk.DISABLED)

        # Configure tags for different colors
        self.text_area.tag_config("green", foreground="#00FF00")
        self.text_area.tag_config("red", foreground="#FF0000")
        self.text_area.tag_config("cyan", foreground="#00FFFF")
        self.text_area.tag_config("purple", foreground="#FF00FF")  # Bright neon purple
        self.text_area.tag_config("yellow", foreground="#FFFF00")  # Yellow for timestamps

    def append_text(self, message, color=None, font_size=12):
        """Appends a new message to the Text widget with optional color and font size."""
        self.text_area.config(state=tk.NORMAL)  # Allow editing to append new text

        # Split the message into words
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

        # Auto-scroll to the end
        self.text_area.yview(tk.END)

        # Disable editing again to keep it read-only
        self.text_area.config(state=tk.DISABLED)

    def is_timestamp(self, word):
        """Check if the word looks like a timestamp."""
        # This is a simple check. You might want to make it more robust
        # depending on your exact timestamp format.
        return len(word) >= 19 and word[4] == '-' and word[7] == '-' and word[10] == ' ' and word[13] == ':' and word[16] == ':'


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
                                self.terminal_gui.append_text(conflict_msg)  # Print to terminal GUI
                                logging.info(conflict_msg)
                                self.notify_dashboard(conflict_msg)
                                self.resolve_conflict(existing_msg, message)
                                return  # Resolve the first detected conflict and exit

    def detect_conflict(self):
        """Detect conflicts based on recent messages."""
        current_time = datetime.now()
        time_window = timedelta(seconds=5)  # Define the short time frame for conflict detection
        recent_messages = [msg for msg in self.message_log if current_time - msg['timestamp'] <= time_window]

        message = f"Checking for conflicts among {len(recent_messages)} recent messages"
        print(message)
        self.terminal_gui.append_text(message)  # Print to terminal GUI

        if len(recent_messages) > 1:
            for i in range(len(recent_messages)):
                for j in range(i + 1, len(recent_messages)):
                    if self.is_conflict(recent_messages[i], recent_messages[j]):
                        conflict_msg = f"Conflict detected between messages from  {recent_messages[i]['xapp_id']} and  {recent_messages[j]['xapp_id']}"
                        print(conflict_msg)
                        self.terminal_gui.append_text(conflict_msg)  # Print to terminal GUI
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
        conflict_msg = f"Conflict detected. Both  {msg1['xapp_id']} and  {msg2['xapp_id']} sent conflicting messages."
        print(conflict_msg)
        self.terminal_gui.append_text(conflict_msg)  # Print to terminal GUI
        logging.info(conflict_msg)

        # Timestamp-based resolution (first come, first served)
        if msg1['timestamp'] < msg2['timestamp']:
            self.apply_message(msg1)
            self.buffer_message(msg2)
        else:
            self.apply_message(msg2)
            self.buffer_message(msg1)

    def apply_message(self, msg):
        """Apply the PRB allocation message to the RAN node."""
        message = f"Initializing Conflict Mitigation Module"
        print(message)
        self.terminal_gui.append_text(message)  # Print to terminal GUI
        logging.info(message)

    def buffer_message(self, msg):
        """Buffer the message and schedule its execution after a delay."""
        message = f"Buffering message from  {msg['xapp_id']} for later execution."
        print(message)
        self.terminal_gui.append_text(message)  # Print to terminal GUI
        logging.info(message)

        # Schedule execution after 20 seconds
        threading.Timer(5, self.execute_buffered_message, [msg]).start()

    def execute_buffered_message(self, msg):
        """Execute a buffered message after the delay."""
        message = f"Executing buffered message from xApp {msg['xapp_id']} after delay."
        print(message)
        self.terminal_gui.append_text(message)  # Print to terminal GUI
        logging.info(message)
        self.apply_message(msg)

    def notify_dashboard(self, message):
        """Notify the dashboard with a message."""
        try:
            requests.post('http://localhost:5000/update', json={'message': message})
        except Exception as e:
            error_message = f"  "
            print(error_message)
            self.terminal_gui.append_text(error_message)  # Print to terminal GUI


def start_controller(terminal_gui):
    """Function to run CentralController logic in a separate thread."""
    controller = CentralController(terminal_gui)
    controller.onboard_xapp('xApp1')
    controller.log_message('xApp1', 'gnbd_001_001_00019b_0', 0, 1, 5, datetime.now())
    controller.onboard_xapp('xApp2')
    controller.log_message('xApp2', 'gnbd_001_001_00019b_0', 0, 3, 6, datetime.now())
    while True:
        time.sleep(5)  # Simulate continuous controller execution


if __name__ == "__main__":
    root = tk.Tk()

    # Initialize the TerminalGUI
    terminal_gui = TerminalGUI(root)

    # Start the CentralController in a separate thread
    controller_thread = threading.Thread(target=start_controller, args=(terminal_gui,))
    controller_thread.daemon = True  # Set the thread as a daemon so it exits when the main program exits
    controller_thread.start()

    # Run the Tkinter main loop
    root.mainloop()

