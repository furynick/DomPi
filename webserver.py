from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

# A dictionary to store variables
variables = {"count": 0, "message": "Hello, World!"}

# Serve the favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Route to get all variables
@app.route('/variables', methods=['GET'])
def get_variables():
    return jsonify(variables)

# Route to update a variable (expects JSON input)
@app.route('/variables/<key>', methods=['POST'])
def update_variable(key):
    if key in variables:
        data = request.get_json()
        if "value" in data:
            variables[key] = data["value"]
            return jsonify({"success": True, "updated": {key: variables[key]}})
    return jsonify({"success": False, "error": "Invalid key or missing value"}), 400

# Route to reset all variables
@app.route('/reset', methods=['POST'])
def reset_variables():
    global variables
    variables = {"count": 0, "message": "Hello, World!"}
    return jsonify({"success": True, "message": "Variables reset."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
