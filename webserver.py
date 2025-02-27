import global_vars
from flask import Flask, request, jsonify, send_from_directory, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/schedule', methods=['GET'])
def get_schedule():
    return jsonify(global_vars.boiler_schedule)

@app.route('/schedule', methods=['POST']) # TODO
def add_schedule():
    data = request.get_json()
    boiler_schedule.append({"weekday": 2, "start_h": 6, "start_m": 30, "target_temp": 20.0})
    if "value" in data:
        variables[key] = data["value"]
        return jsonify({"success": True, "updated": {key: variables[key]}})
    return jsonify({"success": False, "error": "Invalid key or missing value"}), 400

@app.route('/schedule', methods=['DELETE']) # TODO
def del_schedule():
    data = request.get_json()
    if "id" in data:
        if data["id"] < len(boiler_schedule):
            return jsonify({"success": True, "updated": {data: boiler_schedule.pop(data['id'])}})
    return jsonify({"success": False, "error": "Invalid id or missing value"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
