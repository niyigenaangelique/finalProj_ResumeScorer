import requests
import json

# Test the tracking endpoint
try:
    response = requests.get('http://localhost:8005/applications-by-email?email=angelbrenna20@gmail.com')
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} applications")
        for app in data:
            print(f"  - {app.get('job_title', 'Unknown')} - {app.get('status', 'Unknown')}")
except Exception as e:
    print(f"Error: {e}")
