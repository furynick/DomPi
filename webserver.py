import global_vars
from flask import Flask, request, jsonify, send_from_directory, render_template

app = Flask(__name__)

def check_data(data):
    if "weekday" in data and isinstance(data["weekday"], int) and 0 <= data["weekday"] <= 6:
        if "start_h" in data and isinstance(data["start_h"], int) and 0 <= data["start_h"] <= 23:
            if "start_m" in data and isinstance(data["start_m"], int) and 0 <= data["start_m"] <= 59:
                if "target_temp" in data and isinstance(data["target_temp"], (int, float)):
                    return True
    return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/schedule', methods=['GET'])
def get_schedule():
    return jsonify(global_vars.boiler_schedule)

@app.route('/schedule', methods=['POST'])
def add_schedule():
    req_keys = ["weekday", "start_h", "start_m", "target_temp"]
    data = request.get_json()

    if check_data(data):
        schedule = {key: data[key] for key in req_keys if key in data}
        global_vars.boiler_schedule.append()
        global_vars.save_schedule()
        return jsonify({"success": True, "append": schedule})
    return jsonify({"success": False, "error": "Invalid data or missing value"}), 400

@app.route('/schedule', methods=['DELETE'])
def del_schedule():
    data = request.get_json()
    if "id" in data:
        if data["id"] < len(boiler_schedule):
            schedule = global_vars.boiler_schedule.pop(data['id'])
            global_vars.save_schedule()
            return jsonify({"success": True, "deleted": schedule})
    return jsonify({"success": False, "error": "Invalid id or missing value"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
