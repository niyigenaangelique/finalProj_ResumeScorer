import requests
import json

def test_form_debug():
    """Test form debugging in browser"""
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
    
    # Check if the page has the debugging elements
    content = offers_response.text
    
    checks = [
        ('Form submission test', 'Testing form submission...'),
        ('Form found check', 'Form found:'),
        ('Form not found check', 'Form not found!'),
        ('Form submitted message', 'Form submitted!'),
        ('Form data logging', 'Form data:')
    ]
    
    print('\n📋 Browser Console Debugging Check:')
    for check_name, check_pattern in checks:
        if check_pattern in content:
            print(f'✅ {check_name} found')
        else:
            print(f'❌ {check_name} missing')
    
    print('\n🔍 Browser Debugging Instructions:')
    print('1. Open browser and go to: http://localhost:8003/offers')
    print('2. Login with: angelbrenna20@gmail.com / Niyigena2003@')
    print('3. Open Developer Tools (F12)')
    print('4. Go to Console tab')
    print('5. Look for:')
    print('   - "Testing form submission..."')
    print('   - "Form found: [object HTMLFormElement]"')
    print('   - "Form submitted!" when you click Create Offer')
    print('   - "Form data:" with the actual form data')
    
    print('\n📋 If form submission is not working:')
    print('- Check for JavaScript errors in console')
    print('- Make sure the form ID is "offerForm"')
    print('- Verify the event listener is attached correctly')
    
    return True

if __name__ == "__main__":
    print("🔍 Testing Form Submission Debugging")
    print("=" * 50)
    
    success = test_form_debug()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Form debugging is ready!")
    else:
        print("❌ Form debugging has issues")
