import os
import json
import hashlib
import hmac
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/webhook_events")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")

# Initialize MongoDB client
try:
    client = MongoClient(MONGODB_URI)
    db = client.get_database()
    events_collection = db.events
    print(f"Connected to MongoDB: {MONGODB_URI}")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    events_collection = None

def verify_github_signature(payload_body, signature_header):
    """Verify that the payload was sent from GitHub by validating SHA256 signature."""
    # DEBUG prints - remove in production
    print(f"DEBUG: signature_header = {signature_header}")
    print(f"DEBUG: GITHUB_WEBHOOK_SECRET = {GITHUB_WEBHOOK_SECRET}")

    if not signature_header or not GITHUB_WEBHOOK_SECRET:
        print("DEBUG: Skipping signature verification (no header or no secret).")
        return True  # Skip verification if no secret is configured
    
    hash_object = hmac.new(
        GITHUB_WEBHOOK_SECRET.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    
    print(f"DEBUG: Expected Signature: {expected_signature}")
    print(f"DEBUG: Received Signature: {signature_header}")

    if not hmac.compare_digest(expected_signature, signature_header):
        print("DEBUG: Signature mismatch!")
        return False
    print("DEBUG: Signature match!")
    return True

def parse_push_event(payload):
    """Parse GitHub push event payload."""
    try:
        author = payload["pusher"]["name"]
        to_branch = payload["ref"].split("/")[-1]  # Extract branch name from refs/heads/branch_name
        request_id = payload["head_commit"]["id"] if "head_commit" in payload and payload["head_commit"] else "N/A"
        timestamp = datetime.utcnow().isoformat()
        
        return {
            "request_id": request_id,
            "author": author,
            "action": "PUSH",
            "from_branch": None, # Not applicable for push events in this schema
            "to_branch": to_branch,
            "timestamp": timestamp,
            "message": f'"{author}" pushed to "{to_branch}" on {timestamp}',
            "raw_payload": payload
        }
    except KeyError as e:
        print(f"Error parsing push event: {e}")
        return None

def parse_pull_request_event(payload):
    """Parse GitHub pull request event payload."""
    try:
        action = payload["action"]
        
        author = payload["pull_request"]["user"]["login"]
        from_branch = payload["pull_request"]["head"]["ref"]
        to_branch = payload["pull_request"]["base"]["ref"]
        request_id = str(payload["pull_request"]["id"])
        timestamp = datetime.utcnow().isoformat()
        
        event_action = None
        message = None

        if action == "opened":
            event_action = "PULL_REQUEST"
            message = f'"{author}" submitted a pull request from "{from_branch}" to "{to_branch}" on {timestamp}'
        elif action == "closed" and payload["pull_request"].get("merged", False):
            event_action = "MERGE"
            message = f'"{author}" merged branch "{from_branch}" to "{to_branch}" on {timestamp}'
        else:
            return None  # PR closed but not merged, or other unsupported PR actions
        
        return {
            "request_id": request_id,
            "author": author,
            "action": event_action,
            "from_branch": from_branch,
            "to_branch": to_branch,
            "timestamp": timestamp,
            "message": message,
            "raw_payload": payload
        }
    except KeyError as e:
        print(f"Error parsing pull request event: {e}")
        return None

@app.route("/webhook", methods=["POST"])
def github_webhook():
    """Handle GitHub webhook events."""
    # Verify GitHub signature
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_github_signature(request.data, signature):
        return jsonify({"error": "Invalid signature"}), 401
    
    # Get event type
    event_type = request.headers.get("X-GitHub-Event")
    payload = request.json
    
    if not payload:
        return jsonify({"error": "No payload received"}), 400
    
    event_data = None
    
    # Parse different event types
    if event_type == "push":
        event_data = parse_push_event(payload)
    elif event_type == "pull_request":
        event_data = parse_pull_request_event(payload)
    else:
        print(f"Unsupported event type: {event_type}")
        return jsonify({"message": "Event type not supported"}), 200
    
    # Store event in MongoDB
    if event_data and events_collection is not None:
        try:
            # Update the message field with the new timestamp format
            # This is done here to ensure the stored message reflects the desired display format
            # For a more robust solution, store raw timestamp and format in UI only
            # For this assignment, updating the message here is sufficient
            formatted_timestamp = format_timestamp_for_display(event_data["timestamp"])
            event_data["message"] = event_data["message"].replace(event_data["timestamp"], formatted_timestamp)
            event_data["timestamp"] = formatted_timestamp # Store formatted timestamp

            result = events_collection.insert_one(event_data)
            print(f"Event stored with ID: {result.inserted_id}")
            return jsonify({"message": "Event processed successfully", "id": str(result.inserted_id)}), 200
        except Exception as e:
            print(f"Error storing event: {e}")
            return jsonify({"error": "Failed to store event"}), 500
    elif event_data:
        print("Event parsed but MongoDB not available")
        return jsonify({"message": "Event parsed but not stored (MongoDB unavailable)"}), 200
    else:
        return jsonify({"error": "Failed to parse event"}), 400

@app.route("/events", methods=["GET"])
def get_events():
    """Get latest events from MongoDB."""
    if events_collection is None:
        return jsonify({"error": "MongoDB not available"}), 500
    
    try:
        # Get latest 50 events, sorted by timestamp descending
        events = list(events_collection.find(
            {},
            {"_id": 0, "raw_payload": 0}  # Exclude _id and raw_payload from response
        ).sort("timestamp", -1).limit(50))
        
        return jsonify({"events": events}), 200
    except Exception as e:
        print(f"Error fetching events: {e}")
        return jsonify({"error": "Failed to fetch events"}), 500

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    mongodb_status = "connected" if events_collection is not None else "disconnected"
    return jsonify({
        "status": "healthy",
        "mongodb": mongodb_status,
        "timestamp": datetime.utcnow().isoformat()
    }), 200

def format_timestamp_for_display(iso_timestamp):
    """Formats an ISO timestamp string to \'2nd April 2021 - 12:00 PM UTC\'."""
    try:
        dt_object = datetime.fromisoformat(iso_timestamp)
        # Add ordinal suffix
        day = dt_object.day
        if 10 <= day % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
        
        # Format: Day with suffix, Month Name, Year - Hour:Minute AM/PM UTC
        return dt_object.strftime(f"{day}{suffix} %B %Y - %#I:%M %p UTC")
    except ValueError:
        return iso_timestamp # Return original if parsing fails



@app.route("/", methods=["GET"])
def index():
    """Serve the main UI."""
    return render_template('index.html')

if __name__ == "__main__":
   
    # Run the Flask app
    app.run(host="0.0.0.0", port=5000, debug=True)
