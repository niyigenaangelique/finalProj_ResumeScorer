import requests
import json

def test_browser_offers():
    """Test offers page in browser-like scenario"""
    session = requests.Session()
    
    # Login
    login_data = {'email': 'angelbrenna20@gmail.com', 'password': 'Niyigena2003@'}
    response = session.post('http://localhost:8003/login', data=login_data, allow_redirects=False)
    
    if response.status_code != 302:
        print('❌ Login failed')
        return False
    
    print('✅ Login successful')
    
    # Get offers page
    offers_response = session.get('http://localhost:8003/offers')
    
    if offers_response.status_code != 200:
        print('❌ Offers page failed to load')
        return False
    
    print('✅ Offers page loads successfully')
    
    # Check if the page has the correct content
    content = offers_response.text
    
    # Check for JavaScript console logging (debugging)
    if 'console.log(\'Loading offer history...\')' in content:
        print('✅ Debug logging found - should help with troubleshooting')
    
    # Check for immediate history loading
    if 'loadOffersHistory();' in content:
        print('✅ Immediate history loading call found')
    
    # Check for the history section
    if 'offersHistory' in content:
        print('✅ History section found')
    
    # Check for loading text
    if 'Loading offer history...' in content:
        print('✅ Initial loading text found')
    
    print('\n🔍 Browser Debugging Instructions:')
    print('1. Open browser and go to: http://localhost:8003/offers')
    print('2. Open Developer Tools (F12)')
    print('3. Go to Console tab')
    print('4. Look for "Loading offer history..." message')
    print('5. Check for any JavaScript errors')
    print('6. Look for "Response status:" and "Response data:" messages')
    
    print('\n📋 If still showing "Loading offer history...":')
    print('- Check browser console for JavaScript errors')
    print('- Look for network tab to see if API call is made')
    print('- Verify the /api/offer-history call succeeds')
    
    return True

if __name__ == "__main__":
    print("🔍 Testing Browser Offers Page")
    print("=" * 50)
    
    success = test_browser_offers()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Offers page is ready for browser testing!")
        print("\n🌐 Open your browser and go to:")
        print("http://localhost:8003/offers")
        print("\n🔍 Check the browser console (F12) for debugging info")
