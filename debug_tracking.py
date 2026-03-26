import requests
import json

def debug_tracking():
    print("=== DEBUGGING TRACKING APPLICATION ===")
    
    # Test 1: Direct API call (same as JavaScript)
    print("\n1. Testing direct API call...")
    try:
        response = requests.get('http://localhost:8005/applications-by-email?email=angelbrenna20@gmail.com')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Data received: {len(data)} applications")
            print(f"   First app keys: {list(data[0].keys()) if data else 'None'}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 2: Test tracking page HTML structure
    print("\n2. Testing tracking page structure...")
    try:
        response = requests.get('http://localhost:8005/track-application')
        print(f"   Page status: {response.status_code}")
        
        # Check for key elements
        content = response.text
        has_email_input = 'id="trackEmail"' in content
        has_track_button = 'onclick="trackApps()"' in content
        has_results_div = 'id="trackerResults"' in content
        has_track_function = 'function trackApps()' in content or 'async function trackApps()' in content
        
        print(f"   Has email input: {has_email_input}")
        print(f"   Has track button: {has_track_button}")
        print(f"   Has results div: {has_results_div}")
        print(f"   Has trackApps function: {has_track_function}")
        
        if not all([has_email_input, has_track_button, has_results_div, has_track_function]):
            print("   ❌ Missing required elements!")
            # Show what's missing
            if not has_email_input:
                print("   - Missing: email input with id='trackEmail'")
            if not has_track_button:
                print("   - Missing: button with onclick='trackApps()'")
            if not has_results_div:
                print("   - Missing: div with id='trackerResults'")
            if not has_track_function:
                print("   - Missing: trackApps() JavaScript function")
        else:
            print("   ✅ All required elements present")
            
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 3: Test with different emails
    print("\n3. Testing with different emails...")
    test_emails = [
        "angelbrenna20@gmail.com",  # Known to have applications
        "test@example.com",         # Likely no applications
        "",                         # Empty email
        "invalid-email"            # Invalid format
    ]
    
    for email in test_emails:
        try:
            response = requests.get(f'http://localhost:8005/applications-by-email?email={email}')
            if response.status_code == 200:
                data = response.json()
                print(f"   '{email}': {len(data)} applications")
            else:
                print(f"   '{email}': Error {response.status_code}")
        except Exception as e:
            print(f"   '{email}': Exception - {e}")

if __name__ == "__main__":
    debug_tracking()
