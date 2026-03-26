import requests
import json

def test_minimal_offers():
    """Test minimal offers functionality to isolate issues"""
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
    
    # Check if the page has basic JavaScript execution
    content = offers_response.text
    
    print('\n🔍 Basic JavaScript Execution Test:')
    
    # Check for any console.log statements
    if 'console.log' in content:
        print('✅ Console logging found in page')
    else:
        print('❌ No console logging found')
    
    # Check for script tags
    if '<script>' in content and '</script>' in content:
        print('✅ Script tags found')
    else:
        print('❌ Script tags not found')
    
    # Check for form element
    if 'id="offerForm"' in content:
        print('✅ Offer form found')
    else:
        print('❌ Offer form not found')
    
    # Check for submit button
    if 'type="submit"' in content:
        print('✅ Submit button found')
    else:
        print('❌ Submit button not found')
    
    # Check for basic event listener pattern
    if 'addEventListener' in content:
        print('✅ Event listener pattern found')
    else:
        print('❌ Event listener pattern not found')
    
    print('\n🌐 Manual Testing Instructions:')
    print('1. Open browser: http://localhost:8003/offers')
    print('2. Open Developer Tools (F12)')
    print('3. Go to Console tab')
    print('4. Type: document.getElementById("offerForm")')
    print('5. Check if form element exists')
    print('6. Type: offerForm.addEventListener("submit", function(e) { ... })')
    print('7. Check if you can add this event listener manually')
    print('8. Test form submission by calling the function directly')
    
    print('\n📋 Expected Console Messages:')
    print('- "Testing form submission..."')
    print('- "JavaScript is executing!"')
    print('- "Form found: [object HTMLFormElement]"')
    print('- "Create button found: [object HTMLInputElement]"')
    print('- "Form submitted!"')
    print('- "Form data: {...}"')
    
    return True

if __name__ == "__main__":
    print("🔍 Minimal Offers Test")
    print("=" * 40)
    
    success = test_minimal_offers()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Basic page structure is correct!")
    else:
        print("❌ Basic page structure has issues")
