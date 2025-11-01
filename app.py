
from flask import Flask, jsonify
from flask_cors import CORS
from utility.db import ensure_mongo_collection
from bson import json_util
import json
import os
from utility.config import DATA_DIR

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

# --- Main Block ---

if __name__ == "__main__":
    # Note: The multi-agent system in `agent.py` should be run as a separate process.
    # This Flask app is only for serving the data.
    app.run(debug=True, port=5001)
