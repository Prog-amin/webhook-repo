# Webhook Receiver (webhook-repo)

This repository contains a Flask app that receives GitHub webhook events (Push, Pull Request, Merge), stores them in MongoDB, and exposes an API for a UI to poll the latest events.

## Setup

1. **Clone the repository**
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up MongoDB**
   - You can use a local MongoDB instance or a cloud provider (e.g., MongoDB Atlas).
   - Create a `.env` file in the root directory:
     ```env
     MONGO_URI=mongodb://localhost:27017/webhook_db
     ```
4. **Run the Flask app**
   ```bash
   python app.py
   ```
   The app will start on `http://localhost:5000`.

## Endpoints

### POST `/webhook`
- Receives GitHub webhook events.
- Example test with curl:
  ```bash
    $headers = @{
        "Content-Type" = "application/json"
        "X-GitHub-Event" = "push"
    }
    $body = '{"after": "abc123", "pusher": {"name": "Travis"}, "ref": "refs/heads/staging"}'
    Invoke-RestMethod -Uri http://localhost:5000/webhook -Method Post -Headers $headers -Body $body
  ```

### GET `/events`
- Returns the latest 20 events in JSON format.
- Example:
  ```bash
  curl http://localhost:5000/events
  ```

## Notes
- The app supports CORS for local frontend development.
- For real GitHub integration, set up a webhook in your GitHub repo to POST to `/webhook`.
- The UI should poll `/events` every 15 seconds to display the latest activity.

Refer my portfolio: https://prog-amin.github.io/my-portfolio
