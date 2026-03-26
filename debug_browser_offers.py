import requests
import json

def debug_browser_offers():
    """Debug browser JavaScript issues for offers page"""
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
    
    # Check for all JavaScript functions and elements
    content = offers_response.text
    
    print('\n🔍 JavaScript Function Analysis:')
    
    # Check for critical JavaScript functions
    js_functions = {
        'loadOffersHistory': 'Load offer history function',
        'viewOffer': 'View offer details function',
        'sendOffer': 'Send offer function',
        'deleteOffer': 'Delete offer function',
        'withdrawOffer': 'Withdraw offer function',
        'getStatusClass': 'Status styling function',
        'updateOfferDetails': 'Update offer details function',
        'updateOfferFields': 'Update offer fields function',
        'previewOffer': 'Preview offer function',
        'saveOfferDraft': 'Save draft function'
    }
    
    for func_name, description in js_functions.items():
        if f'function {func_name}(' in content:
            print(f'✅ {description} - FOUND')
        else:
            print(f'❌ {description} - MISSING')
    
    print('\n🔍 HTML Element Analysis:')
    
    # Check for critical HTML elements
    html_elements = {
        'offerForm': 'Offer submission form',
        'applicationSelect': 'Application selection dropdown',
        'offersHistory': 'Offer history container',
        'offerType': 'Offer type selection',
        'createButton': 'Create Offer button'
    }
    
    for elem_id, description in html_elements.items():
        if f'id="{elem_id}"' in content:
            print(f'✅ {description} - FOUND')
        else:
            print(f'❌ {description} - MISSING')
    
    print('\n🔍 API Endpoint Analysis:')
    
    # Check for API calls in JavaScript
    api_calls = {
        '/api/create-offer': 'Create offer API',
        '/api/offer-history': 'Get offer history API',
        '/api/offer-details/': 'Get offer details API',
        '/api/send-offer/': 'Send offer API',
        '/api/delete-offer/': 'Delete offer API',
        '/api/withdraw-offer/': 'Withdraw offer API'
    }
    
    for api_endpoint, description in api_calls.items():
        if api_endpoint in content:
            print(f'✅ {description} - FOUND')
        else:
            print(f'❌ {description} - MISSING')
    
    print('\n🔍 Event Listener Analysis:')
    
    # Check for event listeners
    if 'addEventListener' in content:
        print('✅ Event listeners detected')
        
        # Check for specific event listeners
        event_listeners = [
            'submit', 'click', 'change', 'load'
        ]
        
        for event_type in event_listeners:
            if f'addEventListener({event_type}' in content or f'addEventListener("{event_type}"' in content:
                print(f'✅ {event_type} event listener found')
            else:
                print(f'❌ {event_type} event listener not found')
    else:
        print('❌ No event listeners detected')
    
    print('\n🔍 Error Handling Analysis:')
    
    # Check for error handling
    error_handling = {
        'console.log': 'Console logging',
        'console.error': 'Error logging',
        'try/catch': 'Exception handling',
        '.catch': 'Promise error handling'
    }
    
    for error_type, description in error_handling.items():
        if error_type in content:
            print(f'✅ {description} - FOUND')
        else:
            print(f'❌ {description} - MISSING')
    
    print('\n🌐 Browser Testing Instructions:')
    print('1. Open browser: http://localhost:8003/offers')
    print('2. Login: angelbrenna20@gmail.com / Niyigena2003@')
    print('3. Open Developer Tools (F12)')
    print('4. Go to Console tab')
    print('5. Try to create an offer')
    print('6. Check for JavaScript errors:')
    print('   - Red error messages in console')
    print('   - Look for "Form submitted!" message')
    print('   - Check for "Form data:" message')
    print('7. Check if offer appears in history')
    print('8. Try to view offer details')
    print('9. Check for any network errors')
    
    return True

if __name__ == "__main__":
    print("🔍 Comprehensive Browser Debugging for Offers")
    print("=" * 60)
    
    success = debug_browser_offers()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Browser debugging analysis complete!")
    else:
        print("❌ Browser debugging failed")
