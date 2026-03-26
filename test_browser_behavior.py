import requests
import json

def simulate_browser_behavior():
    print("=== SIMULATING BROWSER BEHAVIOR ===")
    
    # Simulate exactly what the JavaScript does
    email = "angelbrenna20@gmail.com"
    
    # Step 1: Get the tracking page (like a browser)
    print("\n1. Loading tracking page...")
    try:
        page_response = requests.get('http://localhost:8005/track-application')
        print(f"   Page loaded: Status {page_response.status_code}")
        
        # Step 2: Make the API call (like JavaScript fetch)
        print("\n2. Making API call...")
        api_url = f'http://localhost:8005/applications-by-email?email={email}'
        api_response = requests.get(api_url)
        
        print(f"   API URL: {api_url}")
        print(f"   API Status: {api_response.status_code}")
        
        if api_response.status_code == 200:
            data = api_response.json()
            print(f"   ✅ Data received: {len(data)} applications")
            
            # Step 3: Simulate the JavaScript HTML generation
            print("\n3. Simulating HTML generation...")
            if not data:
                html = '<div class="result-card">No applications found</div>'
                print(f"   HTML for empty result: {html}")
            else:
                # Generate HTML like the JavaScript does
                html_parts = []
                for app in data:
                    status = app.get('status', 'pending')
                    job_title = app.get('job_title', 'Unknown')
                    department = app.get('department', 'Unknown')
                    application_date = app.get('application_date', 'Unknown')
                    resume_score = app.get('resume_score')
                    
                    # Simplified HTML generation
                    app_html = f"""
                    <div class="result-card">
                        <h3>{job_title}</h3>
                        <p><strong>Status:</strong> {status}</p>
                        <p><strong>Department:</strong> {department}</p>
                        <p><strong>Applied:</strong> {application_date}</p>
                        {f'<p><strong>Resume Score:</strong> {resume_score}</p>' if resume_score else ''}
                    </div>
                    """
                    html_parts.append(app_html)
                
                final_html = '<div style="max-width:600px;margin:0 auto;">' + ''.join(html_parts) + '</div>'
                print(f"   ✅ Generated HTML for {len(data)} applications")
                print(f"   Sample HTML (first app):")
                print(f"   {html_parts[0][:200]}...")
                
        else:
            print(f"   ❌ API Error: {api_response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        import traceback
        traceback.print_exc()

def check_server_logs():
    print("\n=== CHECKING SERVER HEALTH ===")
    try:
        response = requests.get('http://localhost:8005/', timeout=5)
        print(f"Main page accessible: {response.status_code == 200}")
        
        # Check if server is responding to different endpoints
        endpoints = [
            '/',
            '/track-application',
            '/jobs',
            '/applications-by-email?email=test@test.com'
        ]
        
        for endpoint in endpoints:
            try:
                resp = requests.get(f'http://localhost:8005{endpoint}', timeout=5)
                status = "✅" if resp.status_code in [200, 404] else "❌"
                print(f"   {status} {endpoint}: {resp.status_code}")
            except Exception as e:
                print(f"   ❌ {endpoint}: {e}")
                
    except Exception as e:
        print(f"Server health check failed: {e}")

if __name__ == "__main__":
    check_server_logs()
    simulate_browser_behavior()
