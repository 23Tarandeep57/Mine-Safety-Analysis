from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from utility.db import ensure_mongo_collection
from utility.config import DATA_DIR, REDIS_URL, CHAT_TIMEOUT_SECONDS
from bson import json_util
import json
import os
import time
import uuid
import redis

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

CHAT_QUEUE = "chat:queue"

app = Flask(__name__)
CORS(app)

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
    """
    Endpoint to handle chat messages using Redis queue and pub/sub.
    
    Flow:
    1. Generate unique request ID
    2. Push query to Redis queue (agent will pick it up)
    3. Subscribe to response channel for this request
    4. Stream responses back to client via SSE
    """
    data = request.get_json()
    user_message = data.get("message")
    history = data.get("history", [])

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Generate unique request ID
    request_id = str(uuid.uuid4())
    response_channel = f"chat:response:{request_id}"

    try:
        # Push query to Redis queue for agent to process
        query_payload = {
            "request_id": request_id,
            "query": user_message,
            "history": history
        }
        redis_client.lpush(CHAT_QUEUE, json.dumps(query_payload))
        
        def stream_response():
            """Generator that subscribes to Redis pub/sub for streaming response."""
            pubsub = redis_client.pubsub()
            pubsub.subscribe(response_channel)
            
            start_time = time.time()
            EOS_TOKEN = "<EOS>"  # Must match agent's EOS token
            
            try:
                for message in pubsub.listen():
                    # Check timeout
                    if time.time() - start_time > CHAT_TIMEOUT_SECONDS:
                        yield f"data: {json.dumps({'error': 'Request timed out'})}\n\n"
                        break
                    
                    # Skip subscription confirmation messages
                    if message['type'] != 'message':
                        continue
                    
                    # Get the raw text data from Redis
                    raw_data = message['data']
                    if isinstance(raw_data, bytes):
                        raw_data = raw_data.decode('utf-8')
                    
                    # Check for end of stream token
                    if EOS_TOKEN in raw_data:
                        # Send any text before EOS token
                        text_before_eos = raw_data.replace(EOS_TOKEN, '')
                        if text_before_eos:
                            yield f"data: {json.dumps({'text': text_before_eos})}\n\n"
                        yield f"data: {json.dumps({'end_of_stream': True})}\n\n"
                        break
                    
                    # Stream the text chunk
                    if raw_data:
                        yield f"data: {json.dumps({'text': raw_data})}\n\n"
                        
            finally:
                pubsub.unsubscribe(response_channel)
                pubsub.close()

        return Response(stream_response(), mimetype='text/event-stream')

    except redis.RedisError as e:
        print(f"Redis error: {e}")
        return jsonify({"error": "Message queue unavailable"}), 503
    except Exception as e:
        print(f"Error during chat setup: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint for Docker/Kubernetes."""
    try:
        redis_client.ping()
        redis_status = "healthy"
    except:
        redis_status = "unhealthy"
    
    try:
        if incidents_collection is not None:
            incidents_collection.find_one()
            mongo_status = "healthy"
        else:
            mongo_status = "unhealthy"
    except:
        mongo_status = "unhealthy"
    
    status = "healthy" if redis_status == "healthy" and mongo_status == "healthy" else "unhealthy"
    
    return jsonify({
        "status": status,
        "services": {
            "redis": redis_status,
            "mongodb": mongo_status
        }
    }), 200 if status == "healthy" else 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)