import os
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB connection URI
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/webhook_db')

# Initialize Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client.get_default_database()
events_collection = db['events']

# HTML template for the UI
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Webhook Events UI</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 2em; background: #f9f9f9; }
        h2 { color: #333; }
        #events { margin-top: 2em; }
        .event { background: #fff; border-radius: 6px; box-shadow: 0 1px 3px #ccc; padding: 1em; margin-bottom: 1em; }
    </style>
</head>
<body>
    <h2>Latest GitHub Events</h2>
    <div id="events">Loading...</div>
    <script>
        // Store displayed event IDs to avoid duplicates
        let displayedIds = new Set();
        // Format ISO date string to readable format
        function formatDate(isoString) {
            const date = new Date(isoString);
            return date.toLocaleString('en-GB', {
                day: 'numeric', month: 'long', year: 'numeric',
                hour: '2-digit', minute: '2-digit', hour12: true, timeZone: 'UTC'
            }) + ' UTC';
        }
        // Format event message based on action type
        function formatEvent(e) {
            const dateStr = formatDate(e.timestamp);
            if (e.action === 'PUSH') {
                return `<b>${e.author}</b> pushed to <b>${e.to_branch}</b> on ${dateStr}`;
            } else if (e.action === 'PULL_REQUEST') {
                return `<b>${e.author}</b> submitted a pull request from <b>${e.from_branch}</b> to <b>${e.to_branch}</b> on ${dateStr}`;
            } else if (e.action === 'MERGE') {
                return `<b>${e.author}</b> merged branch <b>${e.from_branch}</b> to <b>${e.to_branch}</b> on ${dateStr}`;
            } else {
                return JSON.stringify(e);
            }
        }
        // Fetch and display events, avoiding duplicates and only showing new ones
        async function fetchEvents() {
            const res = await fetch('/events');
            const data = await res.json();
            const eventsDiv = document.getElementById('events');
            if (!data.length) {
                eventsDiv.innerHTML = '<i>No events yet.</i>';
                return;
            }
            // Only display events not already shown
            const newEvents = data.filter(e => !displayedIds.has(e._id));
            if (newEvents.length === 0) return; // No new events
            newEvents.forEach(e => displayedIds.add(e._id));
            // Only keep the latest 20 events in the UI
            if (displayedIds.size > 20) {
                displayedIds = new Set(Array.from(displayedIds).slice(-20));
            }
            eventsDiv.innerHTML = data
                .filter(e => displayedIds.has(e._id))
                .map(e => `<div class='event'>${formatEvent(e)}</div>`)
                .join('');
        }
        fetchEvents();
        setInterval(fetchEvents, 15000);
    </script>
</body>
</html>
'''

def get_utc_iso():
    """Return current UTC time as ISO 8601 string with 'Z'."""
    return datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'


def parse_github_event(payload):
    """
    Parse the incoming GitHub webhook payload and extract relevant event data.
    Handles push, pull request, and merge events.
    """
    event_type = request.headers.get('X-GitHub-Event', '').lower()
    data = {
        'request_id': '',
        'author': '',
        'action': '',
        'from_branch': '',
        'to_branch': '',
        'timestamp': ''
    }
    if event_type == 'push':
        # Handle push event
        data['request_id'] = payload.get('after', '')
        data['author'] = payload.get('pusher', {}).get('name', '')
        data['action'] = 'PUSH'
        data['from_branch'] = payload.get('ref', '').split('/')[-1]
        data['to_branch'] = payload.get('ref', '').split('/')[-1]
        # Use the timestamp from the latest commit if available, ensure ISO 8601 with Z
        commits = payload.get('commits', [])
        if commits:
            ts = commits[-1].get('timestamp')
            if ts and not ts.endswith('Z'):
                ts = ts.rstrip('Z') + 'Z'
            data['timestamp'] = ts if ts else get_utc_iso()
        else:
            data['timestamp'] = get_utc_iso()
    elif event_type == 'pull_request':
        # Handle pull request and merge events
        pr = payload.get('pull_request', {})
        pr_action = payload.get('action', '')
        if pr_action == 'opened':
            data['request_id'] = str(pr.get('id', ''))
            data['author'] = pr.get('user', {}).get('login', '')
            data['action'] = 'PULL_REQUEST'
            data['from_branch'] = pr.get('head', {}).get('ref', '')
            data['to_branch'] = pr.get('base', {}).get('ref', '')
            ts = pr.get('created_at')
            if ts and not ts.endswith('Z'):
                ts = ts.rstrip('Z') + 'Z'
            data['timestamp'] = ts if ts else get_utc_iso()
        elif pr_action == 'closed' and pr.get('merged', False):
            data['request_id'] = str(pr.get('id', ''))
            data['author'] = pr.get('user', {}).get('login', '')
            data['action'] = 'MERGE'
            data['from_branch'] = pr.get('head', {}).get('ref', '')
            data['to_branch'] = pr.get('base', {}).get('ref', '')
            ts = pr.get('merged_at')
            if ts and not ts.endswith('Z'):
                ts = ts.rstrip('Z') + 'Z'
            data['timestamp'] = ts if ts else get_utc_iso()
        else:
            return None
    else:
        return None
    return data

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Webhook endpoint to receive GitHub events and store them in MongoDB.
    """
    payload = request.json
    data = parse_github_event(payload)
    if not data or not data['action']:
        return jsonify({'error': 'Unsupported or malformed event'}), 400
    events_collection.insert_one(data)
    return jsonify({'status': 'success'}), 201

@app.route('/events', methods=['GET'])
def get_events():
    """
    Return the latest 20 events, sorted by timestamp descending.
    """
    events = list(events_collection.find().sort('timestamp', -1).limit(20))
    for e in events:
        e['_id'] = str(e['_id'])
    return jsonify(events)

@app.route('/', methods=['GET'])
def index():
    """
    Render the minimal UI for displaying events.
    """
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
