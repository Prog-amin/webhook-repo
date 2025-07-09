import requests
import json
from datetime import datetime

def test_push_event():
    """Test push event webhook"""
    url = "http://localhost:5000/webhook"
    
    headers = {
        "X-GitHub-Event": "push",
        "Content-Type": "application/json"
    }
    
    payload = {
        "ref": "refs/heads/main",
        "commits": [
            {
                "id": "abc123",
                "message": "Test commit message",
                "author": {
                    "name": "Test User"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"Push Event Response: {response.status_code} - {response.text}")

def test_pull_request_event():
    """Test pull request event webhook"""
    url = "http://localhost:5000/webhook"
    
    headers = {
        "X-GitHub-Event": "pull_request",
        "Content-Type": "application/json"
    }
    
    payload = {
        "action": "opened",
        "number": 42,
        "pull_request": {
            "number": 42,
            "state": "open",
            "title": "Test PR",
            "user": {
                "login": "testuser"
            },
            "head": {
                "ref": "feature-branch"
            },
            "base": {
                "ref": "main"
            },
            "merged": False
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"Pull Request Event Response: {response.status_code} - {response.text}")

def test_merge_event():
    """Test merge event webhook"""
    url = "http://localhost:5000/webhook"
    
    headers = {
        "X-GitHub-Event": "pull_request",
        "Content-Type": "application/json"
    }
    
    payload = {
        "action": "closed",
        "number": 42,
        "pull_request": {
            "number": 42,
            "state": "closed",
            "title": "Test PR",
            "user": {
                "login": "testuser"
            },
            "merged_by": {
                "login": "reviewer"
            },
            "head": {
                "ref": "feature-branch"
            },
            "base": {
                "ref": "main"
            },
            "merged": True,
            "merged_at": datetime.utcnow().isoformat()
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"Merge Event Response: {response.status_code} - {response.text}")

if __name__ == "__main__":
    print("Testing webhook endpoints...")
    test_push_event()
    test_pull_request_event()
    test_merge_event()
    
    # Test getting all events
    response = requests.get("http://localhost:5000/events")
    print("\nAll Events:")
    print(json.dumps(response.json(), indent=2))
