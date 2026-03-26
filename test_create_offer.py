import requests
import json

def test_create_offer():
    """Test creating an offer via API"""
    session = requests.Session()
    
    # Login
    login_data = {'email': 'angelbrenna20@gmail.com', 'password': 'Niyigena2003@'}
    response = session.post('http://localhost:8003/login', data=login_data, allow_redirects=False)
    
    if response.status_code != 302:
        print('❌ Login failed')
        return False
    
    print('✅ Login successful')
    
    # Test creating an offer
    offer_data = {
        'application_id': '2',
        'position_title': 'Software Engineer',
        'department': 'Engineering',
        'salary': '$100,000',
        'start_date': '2026-03-27',
        'location': 'remote',
        'reporting_to': 'Angela',
        'offer_type': 'part-time',
        'benefits': 'none',
        'offer_details': 'none',
        'response_deadline': '2026-03-26'
    }
    
    create_response = session.post('http://localhost:8003/api/create-offer', json=offer_data)
    print(f'Create offer API status: {create_response.status_code}')
    
    if create_response.status_code == 200:
        result = create_response.json()
        if result.get('success'):
            print('✅ Offer created successfully!')
            print(f'   Offer ID: {result.get("offer_id", "N/A")}')
            return True
        else:
            print(f'❌ Offer creation failed: {result.get("error")}')
    else:
        print(f'❌ Create offer API failed: {create_response.status_code}')
        print(f'Response: {create_response.text[:200]}')
    
    return False

if __name__ == "__main__":
    print("🔍 Testing Offer Creation API")
    print("=" * 40)
    
    success = test_create_offer()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Offer creation API is working!")
    else:
        print("❌ Offer creation API has issues")
