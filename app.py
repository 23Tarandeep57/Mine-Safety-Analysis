from flask import Flask, jsonify, request, Response
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
CORS(app)

# --- Database Connection ---
incidents_collection = ensure_mongo_collection()

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

@app.route("/api/chat", methods=["POST"])
def chat():
    """Endpoint to handle chat messages by communicating with the agent via files."""
    data = request.get_json()
    user_message = data.get("message")
    history = data.get("history", []) # Get history, default to empty list

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    try:
       
        if BOT_RESPONSE_FILE.exists():
            with open(BOT_RESPONSE_FILE, "w") as f:
                f.truncate(0)

        agent_payload = {
            "query": user_message,
            "history": history
        }
        with open(USER_QUERY_FILE, "w", encoding="utf-8") as f:
            json.dump(agent_payload, f)

        def stream_response():
            """Generator function to poll the file and stream character by character."""
            read_position = 0
            start_time = time.time()
            eos_found = False

            while not eos_found and time.time() - start_time < WAIT_TIMEOUT:
                if not BOT_RESPONSE_FILE.exists():
                    time.sleep(0.05)
                    continue

                try:
                    with open(BOT_RESPONSE_FILE, "r", encoding="utf-8") as f:
                        file_size = os.path.getsize(BOT_RESPONSE_FILE)
                        if file_size > read_position:
                            f.seek(read_position)
                            new_text = f.read()
                            
                           
                            read_position += len(new_text.encode('utf-8'))

                            if EOS_TOKEN in new_text:
                                eos_found = True
                                final_chunk = new_text.split(EOS_TOKEN)[0]
                               
                                for char in final_chunk:
                                    yield f"data: {json.dumps({'text': char})}\n\n"
                                    time.sleep(0.02)  
                            else:
                               
                                for char in new_text:
                                    yield f"data: {json.dumps({'text': char})}\n\n"
                                    time.sleep(0.02)  
                except (IOError, json.JSONDecodeError):
                    pass
                
                time.sleep(0.05) 

            yield f"data: {json.dumps({'end_of_stream': True})}\n\n"

        return Response(stream_response(), mimetype='text/event-stream')

    except Exception as e:
        print(f"Error during chat setup: {e}") 
      
        return Response(json.dumps({"error": f"An error occurred: {str(e)}"}), status=500, mimetype='application/json')


if __name__ == "__main__":
    app.run(port=5001, debug=True)