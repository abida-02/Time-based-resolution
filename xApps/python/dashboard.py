from flask import Flask, jsonify, render_template, request
import logging
from datetime import datetime

app = Flask(__name__)

# Initialize global variables to keep track of onboarded xApps and conflicts
onboarded_xapps = set()
conflicts = []

# Configure logging
logging.basicConfig(filename='dashboard.log', level=logging.INFO, format='%(asctime)s - %(message)s')

@app.route('/')
def index():
    # Pass the onboarded xApps and conflicts to the template
    return render_template('index.html', onboarded_xapps=onboarded_xapps, conflicts=conflicts)

@app.route('/xapp-onboarded', methods=['POST'])
def xapp_onboarded():
    global onboarded_xapps
    data = request.json
    xapp_id = data.get('xapp_id')

    if xapp_id:
        onboarded_xapps.add(xapp_id)
        logging.info(f"xApp {xapp_id} onboarded.")
        print(f"xApp {xapp_id} onboarded and added to dashboard.")
    
    return jsonify(success=True)

@app.route('/conflict-detected', methods=['POST'])
def conflict_detected():
    global conflicts
    data = request.json
    conflict_info = data.get('conflict_info')

    if conflict_info:
        conflicts.append(conflict_info)
        logging.info(f"Conflict detected: {conflict_info}")
        print(f"Conflict detected and added to dashboard: {conflict_info}")

    return jsonify(success=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

