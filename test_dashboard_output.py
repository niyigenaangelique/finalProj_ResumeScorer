import requests
import json

def test_dashboard_output():
    """Test the actual HTML output from dashboard"""
    session = requests.Session()
    
    # Login
    login_data = {'email': 'angelbrenna20@gmail.com', 'password': 'Niyigena2003@'}
    response = session.post('http://localhost:8003/login', data=login_data, allow_redirects=False)
    
    if response.status_code != 302:
        print('❌ Login failed')
        return False
    
    print('✅ Login successful')
    
    # Get dashboard page
    dashboard_response = session.get('http://localhost:8003/dashboard')
    
    if dashboard_response.status_code != 200:
        print('❌ Dashboard page failed to load')
        print(f'Status: {dashboard_response.status_code}')
        print(f'Response: {dashboard_response.text[:500]}')
        return False
    
    print('✅ Dashboard page loads successfully')
    
    # Check the actual HTML content
    content = dashboard_response.text
    
    print('\n🔍 HTML Content Analysis:')
    
    # Check for CSS variables in the actual content
    if '--bg:' in content:
        print('✅ CSS variables found in HTML')
    else:
        print('❌ CSS variables NOT found in HTML')
    
    # Check for CSS classes
    if '.topnav {' in content:
        print('✅ CSS classes found in HTML')
    else:
        print('❌ CSS classes NOT found in HTML')
    
    # Check for Chart.js
    if 'chart.umd.min.js' in content:
        print('✅ Chart.js found in HTML')
    else:
        print('❌ Chart.js NOT found in HTML')
    
    # Check for Google Fonts
    if 'fonts.googleapis.com' in content:
        print('✅ Google Fonts found in HTML')
    else:
        print('❌ Google Fonts NOT found in HTML')
    
    # Check for HTML structure
    if '<!DOCTYPE html>' in content:
        print('✅ HTML structure found')
    else:
        print('❌ HTML structure NOT found')
    
    # Check for any Python errors or placeholders
    if '{total}' in content or '{scored}' in content:
        print('❌ Unsubstituted variables found - string formatting issue!')
    else:
        print('✅ Variables properly substituted')
    
    # Show a snippet of the content
    print('\n📋 HTML Content Sample (first 1000 chars):')
    print(content[:1000])
    
    return True

if __name__ == "__main__":
    print("🔍 Testing Dashboard HTML Output")
    print("=" * 50)
    
    success = test_dashboard_output()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Dashboard output test complete!")
    else:
        print("❌ Dashboard output test failed")
