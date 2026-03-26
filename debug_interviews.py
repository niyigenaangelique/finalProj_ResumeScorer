import requests
import json

session = requests.Session()

# Login
login_data = {'email': 'angelbrenna20@gmail.com', 'password': 'Niyigena2003@'}
response = session.post('http://localhost:8003/login', data=login_data, allow_redirects=False)

if response.status_code == 302:
    print('✅ Login successful')
    
    # Test interviews page
    interviews_response = session.get('http://localhost:8003/interviews')
    print(f'Interviews page status: {interviews_response.status_code}')
    
    if interviews_response.status_code == 200:
        print('✅ Interviews page loads')
        
        # Try to schedule an interview
        interview_data = {
            'application_id': '1',
            'interview_type': 'Technical',
            'interview_date': '2024-01-15',
            'interview_time': '14:00',
            'duration': 60,
            'interviewer_name': 'Test User',
            'interview_mode': 'video'
        }
        
        schedule_response = session.post('http://localhost:8003/api/schedule-interview', json=interview_data)
        print(f'Schedule interview status: {schedule_response.status_code}')
        
        if schedule_response.status_code == 200:
            result = schedule_response.json()
            if result.get('success'):
                print('✅ Schedule interview working')
                interview_id = result.get('interview_id')
                
                # Test edit
                update_data = {
                    'interview_id': interview_id,
                    'interview_type': 'Technical Updated',
                    'interview_date': '2024-01-16',
                    'interview_time': '15:00',
                    'duration': 90,
                    'interviewer_name': 'Updated User',
                    'interview_mode': 'in-person',
                    'location': 'Office Room 101'
                }
                
                update_response = session.post('http://localhost:8003/api/update-interview', json=update_data)
                print(f'Update interview status: {update_response.status_code}')
                
                if update_response.status_code == 200:
                    update_result = update_response.json()
                    if update_result.get('success'):
                        print('✅ Update interview working')
                        
                        # Test cancel
                        cancel_data = {'interview_id': interview_id}
                        cancel_response = session.post('http://localhost:8003/api/cancel-interview', json=cancel_data)
                        print(f'Cancel interview status: {cancel_response.status_code}')
                        
                        if cancel_response.status_code == 200:
                            cancel_result = cancel_response.json()
                            if cancel_result.get('success'):
                                print('✅ Cancel interview working')
                            else:
                                print(f'❌ Cancel failed: {cancel_result.get("error")}')
                        else:
                            print(f'❌ Cancel API failed: {cancel_response.status_code}')
                    else:
                        print(f'❌ Update failed: {update_result.get("error")}')
                else:
                    print(f'❌ Update API failed: {update_response.status_code}')
                    print(f'Error: {update_response.text[:200]}')
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f'❌ Schedule failed: {error_msg}')
        else:
            print(f'❌ Schedule API failed: {schedule_response.status_code}')
            print(f'Error: {schedule_response.text[:200]}')
    else:
        print(f'❌ Interviews page failed: {interviews_response.status_code}')
else:
    print('❌ Login failed')
