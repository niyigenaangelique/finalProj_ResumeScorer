import requests
import json
import time

def test_browser_communications():
    """Test communications page in browser-like scenario"""
    session = requests.Session()
    
    # Login
    login_data = {'email': 'angelbrenna20@gmail.com', 'password': 'Niyigena2003@'}
    response = session.post('http://localhost:8003/login', data=login_data, allow_redirects=False)
    
    if response.status_code != 302:
        print('❌ Login failed')
        return False
    
    print('✅ Login successful')
    
    # Get communications page
    comm_response = session.get('http://localhost:8003/communications')
    
    if comm_response.status_code != 200:
        print('❌ Communications page failed to load')
        return False
    
    print('✅ Communications page loads successfully')
    
    # Check if the page has the correct content
    content = comm_response.text
    
    # Check for JavaScript console logging (debugging)
    if 'console.log(\'Loading communication history...\')' in content:
        print('✅ Debug logging found - should help with troubleshooting')
    
    # Check for immediate history loading
    if 'loadCommunicationHistory();' in content:
        print('✅ Immediate history loading call found')
    
    # Check for the history section
    if 'communicationsHistory' in content:
        print('✅ History section found')
    
    # Check for loading text
    if 'Loading communication history...' in content:
        print('✅ Initial loading text found')
    
    print('\n🔍 Browser Debugging Instructions:')
    print('1. Open browser and go to: http://localhost:8003/communications')
    print('2. Open Developer Tools (F12)')
    print('3. Go to Console tab')
    print('4. Look for "Loading communication history..." message')
    print('5. Check for any JavaScript errors')
    print('6. Look for "Response status:" and "Response data:" messages')
    
    print('\n📋 If still showing "Loading communication history...":')
    print('- Check browser console for JavaScript errors')
    print('- Look for network tab to see if API call is made')
    print('- Verify the /api/communication-history call succeeds')
    
    return True

if __name__ == "__main__":
    print("🔍 Testing Browser Communications Page")
    print("=" * 50)
    
    success = test_browser_communications()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Communications page is ready for browser testing!")
        print("\n🌐 Open your browser and go to:")
        print("http://localhost:8003/communications")
        print("\n🔍 Check the browser console (F12) for debugging info")
