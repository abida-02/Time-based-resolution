from flask import Flask, request, jsonify

app = Flask(__name__)

# A simple in-memory store for PRB data
prb_data_store = []

@app.route('/update_prb', methods=['POST'])
def update_prb():
    data = request.json
    prb_data_store.append(data)
    return jsonify({"status": "success"}), 200

@app.route('/get_prb_data', methods=['GET'])
def get_prb_data():
    return jsonify(prb_data_store)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

