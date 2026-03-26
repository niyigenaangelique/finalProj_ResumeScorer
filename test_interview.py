import requests
import json

session = requests.Session()

# Login
login_data = {'email': 'angelbrenna20@gmail.com', 'password': 'Niyigena2003@'}
response = session.post('http://localhost:8003/login', data=login_data, allow_redirects=False)

if response.status_code == 302:
    print("✅ Login successful")
    
    # Get interviews page
    interviews_response = session.get('http://localhost:8003/interviews')
    print(f'Interviews page status: {interviews_response.status_code}')
    
    if interviews_response.status_code == 200:
        print('✅ Interviews page loads successfully!')
        
        # Test interview scheduling API
        interview_data = {
            'application_id': '1',
            'interview_type': 'Technical',
            'interview_date': '2024-01-15',
            'interview_time': '14:00',
            'duration': 60,
            'interviewer_name': 'John Doe',
            'interview_mode': 'video'
        }
        
        schedule_response = session.post('http://localhost:8003/api/schedule-interview', 
                                       json=interview_data)
        print(f'Schedule interview API status: {schedule_response.status_code}')
        
        if schedule_response.status_code == 200:
            result = schedule_response.json()
            if result.get('success'):
                print('✅ Interview scheduling API working!')
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f'❌ API returned error: {error_msg}')
        else:
            print(f'❌ API failed with status: {schedule_response.status_code}')
            print(f'Response: {schedule_response.text}')
    else:
        print('❌ Interviews page failed')
else:
    print('❌ Login failed')
