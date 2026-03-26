import requests
import time

# Test HR portal pages
base_url = "http://localhost:8003"
pages_to_test = [
    "/",
    "/dashboard", 
    "/jobs",
    "/interviews",
    "/communications",
    "/offers",
    "/reports",
    "/post-job"
]

print("Testing HR Portal Pages...")
print("=" * 50)

# First login to get session
session = requests.Session()
login_data = {
    "email": "angelbrenna20@gmail.com",
    "password": "Niyigena2003@"
}

try:
    # Login
    print("1. Logging in...")
    login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
    print(f"   Login status: {login_response.status_code}")
    
    if login_response.status_code in [302, 303]:
        print("   ✅ Login successful - redirect received")
        
        # Follow redirect to dashboard
        dashboard_response = session.get(f"{base_url}/dashboard")
        print(f"   Dashboard status: {dashboard_response.status_code}")
        
        if dashboard_response.status_code == 200:
            print("   ✅ Dashboard loaded successfully")
        else:
            print(f"   ❌ Dashboard failed: {dashboard_response.status_code}")
            exit(1)
        
        # Test each page
        for i, page in enumerate(pages_to_test, 2):
            print(f"{i}. Testing {page}...")
            try:
                response = session.get(f"{base_url}{page}")
                if response.status_code == 200:
                    print(f"   ✅ {page} - OK")
                else:
                    print(f"   ❌ {page} - Error {response.status_code}")
            except Exception as e:
                print(f"   ❌ {page} - Exception: {e}")
            time.sleep(0.5)
    else:
        print(f"   ❌ Login failed: {login_response.status_code}")
        
except Exception as e:
    print(f"❌ Connection error: {e}")

print("=" * 50)
print("Test completed!")
print(f"Access the HR portal at: {base_url}")
print("Login with: angelbrenna20@gmail.com / Niyigena2003@")
