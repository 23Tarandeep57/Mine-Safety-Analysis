from flask import Flask, jsonify, request
from flask_cors import CORS
from utility.db import ensure_mongo_collection
from bson import json_util
import json
import os
import time
from utility.config import DATA_DIR

USER_QUERY_FILE = DATA_DIR / "user_query.txt"
BOT_RESPONSE_FILE = DATA_DIR / "bot_response.txt"
EOS_TOKEN = "<EOS>"
WAIT_TIMEOUT = 120  # seconds

app = Flask(__name__)
CORS(app) # This will allow the frontend to make requests to our backend

# --- Database Connection ---
incidents_collection = ensure_mongo_collection()


# --- API Endpoints ---

@app.route("/api/incidents", methods=["GET"])
def get_incidents():
    """Endpoint to get all incidents from the database."""
    if incidents_collection is None:
        return jsonify({"error": "Database connection failed"}), 500

    incidents = list(incidents_collection.find({}))
    # Use json_util to handle MongoDB's ObjectId and other BSON types
    return json.loads(json_util.dumps(incidents))

@app.route("/api/reports", methods=["GET"])
def get_reports():
    """Endpoint to get a list of generated audit reports."""
    try:
        report_files = [f for f in os.listdir(DATA_DIR) if f.startswith("safety_audit_report_") and f.endswith(".md")]
        return jsonify(sorted(report_files, reverse=True))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    """Endpoint to get the latest generated safety alerts."""
    try:
        alert_files = [f for f in os.listdir(DATA_DIR) if f.startswith("safety_alerts_") and f.endswith(".json")]
        if not alert_files:
            return jsonify([])

        # Find the most recent alerts file
        latest_alert_file = max(alert_files)
        with open(DATA_DIR / latest_alert_file, 'r', encoding='utf-8') as f:
            alerts = json.load(f)
        return jsonify(alerts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/chatbot", methods=["POST"])
def chatbot_endpoint():
    if not request.is_json:
        return jsonify({
            "error": "Unsupported Media Type",
            "message": "Request Content-Type must be 'application/json'"
        }), 415

    data = request.get_json()
    user_message = data.get("message")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    try:
        # Ensure files are clear before starting
        if USER_QUERY_FILE.exists():
            with open(USER_QUERY_FILE, "w") as f: f.truncate(0)
        if BOT_RESPONSE_FILE.exists():
            with open(BOT_RESPONSE_FILE, "w") as f: f.truncate(0)

        # Write the query to the user_query.txt file to trigger the agent
        with open(USER_QUERY_FILE, "w", encoding="utf-8") as f:
            f.write(user_message)

        # --- Wait for the agent's response ---
        start_time = time.time()
        while time.time() - start_time < WAIT_TIMEOUT:
            if BOT_RESPONSE_FILE.exists() and BOT_RESPONSE_FILE.stat().st_size > 0:
                with open(BOT_RESPONSE_FILE, "r", encoding="utf-8") as f:
                    response_text = f.read()
                
                if EOS_TOKEN in response_text:
                    # Clean up the response and remove the token
                    final_response = response_text.split(EOS_TOKEN)[0].strip()
                    
                    # Clean up files for the next request
                    with open(USER_QUERY_FILE, "w") as f: f.truncate(0)
                    with open(BOT_RESPONSE_FILE, "w") as f: f.truncate(0)
                    
                    return jsonify({"response": final_response})
            
            time.sleep(0.2) # Poll every 200ms

        return jsonify({"error": "Request timed out. The agent did not respond in time."}), 504

    except Exception as e:
        return jsonify({"error": f"An internal error occurred: {str(e)}"}), 500


@app.route("/api/debug", methods=["GET", "POST"])
def debug_endpoint():
    return jsonify({"method": request.method})

# --- Main Block ---

if __name__ == "__main__":
    # Note: The multi-agent system in `agent.py` should be run as a separate process.
    # This Flask app is only for serving the data and interacting with the agent via files.
    app.run(debug=True, port=5001)