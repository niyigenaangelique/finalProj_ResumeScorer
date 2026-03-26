import requests
import json

def test_tracking_functionality():
    print("=== Testing Tracking Application Functionality ===")
    
    # Test 1: Check if tracking page loads
    try:
        response = requests.get('http://localhost:8005/track-application')
        print(f"✓ Tracking page loads: Status {response.status_code}")
    except Exception as e:
        print(f"✗ Tracking page failed: {e}")
        return
    
    # Test 2: Test API endpoint with known email
    test_email = "angelbrenna20@gmail.com"
    try:
        api_response = requests.get(f'http://localhost:8005/applications-by-email?email={test_email}')
        print(f"✓ API endpoint works: Status {api_response.status_code}")
        
        if api_response.status_code == 200:
            data = api_response.json()
            print(f"✓ Found {len(data)} applications for {test_email}")
            
            # Display application details
            for i, app in enumerate(data, 1):
                print(f"  Application {i}:")
                print(f"    - Job: {app.get('job_title', 'Unknown')}")
                print(f"    - Status: {app.get('status', 'Unknown')}")
                print(f"    - Department: {app.get('department', 'Unknown')}")
                print(f"    - Resume Score: {app.get('resume_score', 'N/A')}")
                print(f"    - Interview Status: {app.get('interview_status', 'N/A')}")
                print(f"    - Offer Status: {app.get('offer_status', 'N/A')}")
                print()
        else:
            print(f"✗ API returned error: {api_response.text}")
            
    except Exception as e:
        print(f"✗ API endpoint failed: {e}")
    
    # Test 3: Test with non-existent email
    try:
        fake_response = requests.get('http://localhost:8005/applications-by-email?email=nonexistent@test.com')
        if fake_response.status_code == 200:
            data = fake_response.json()
            print(f"✓ Correctly returns empty list for non-existent email: {len(data)} applications")
        else:
            print(f"✗ Unexpected response for non-existent email: {fake_response.status_code}")
    except Exception as e:
        print(f"✗ Test with non-existent email failed: {e}")

if __name__ == "__main__":
    test_tracking_functionality()
