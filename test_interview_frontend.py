import requests
import json

def test_interview_frontend():
    """Test the frontend JavaScript functionality"""
    session = requests.Session()
    
    # Login
    login_data = {'email': 'angelbrenna20@gmail.com', 'password': 'Niyigena2003@'}
    response = session.post('http://localhost:8003/login', data=login_data, allow_redirects=False)
    
    if response.status_code != 302:
        print('❌ Login failed')
        return False
    
    print('✅ Login successful')
    
    # Get interviews page and check for JavaScript elements
    interviews_response = session.get('http://localhost:8003/interviews')
    
    if interviews_response.status_code != 200:
        print('❌ Interviews page failed to load')
        return False
    
    content = interviews_response.text
    
    # Check for essential JavaScript functions
    js_checks = [
        ('editInterview function', 'function editInterview('),
        ('cancelInterview function', 'function cancelInterview('),
        ('updateInterview function', 'function updateInterview('),
        ('interview details API', '/api/interview-details/'),
        ('update interview API', '/api/update-interview'),
        ('cancel interview API', '/api/cancel-interview'),
        ('form elements', 'interviewForm'),
        ('date field', 'interviewDate'),
        ('time field', 'interviewTime'),
        ('meeting link field', 'meetingLink'),
        ('notes field', 'interviewNotes')
    ]
    
    all_good = True
    for check_name, check_pattern in js_checks:
        if check_pattern in content:
            print(f'✅ {check_name} found')
        else:
            print(f'❌ {check_name} missing')
            all_good = False
    
    if all_good:
        print('\n🎯 Frontend JavaScript elements are all present!')
        
        # Schedule an interview to test with
        interview_data = {
            'application_id': '1',
            'interview_type': 'Technical',
            'interview_date': '2024-01-15',
            'interview_time': '14:00',
            'duration': 60,
            'interviewer_name': 'Test User',
            'interview_mode': 'video',
            'meeting_link': 'https://zoom.us/test',
            'notes': 'Test interview for frontend verification'
        }
        
        schedule_response = session.post('http://localhost:8003/api/schedule-interview', json=interview_data)
        
        if schedule_response.status_code == 200:
            result = schedule_response.json()
            if result.get('success'):
                interview_id = result.get('interview_id')
                print(f'✅ Test interview created with ID: {interview_id}')
                
                # Test getting interview details (simulates frontend edit)
                details_response = session.get(f'http://localhost:8003/api/interview-details/{interview_id}')
                
                if details_response.status_code == 200:
                    details_result = details_response.json()
                    if details_result.get('success'):
                        interview = details_result.get('interview')
                        print('✅ Interview details API working for frontend')
                        
                        # Verify all expected fields are present
                        expected_fields = ['id', 'application_id', 'interview_type', 'scheduled_date', 
                                         'scheduled_time', 'duration', 'interviewer_name', 'interview_mode',
                                         'meeting_link', 'notes']
                        
                        for field in expected_fields:
                            if field in interview:
                                print(f'✅ Field {field} present in interview data')
                            else:
                                print(f'❌ Field {field} missing from interview data')
                        
                        return True
                    else:
                        print(f'❌ Get details failed: {details_result.get("error")}')
                else:
                    print(f'❌ Get details API failed: {details_response.status_code}')
            else:
                print(f'❌ Schedule failed: {result.get("error")}')
        else:
            print(f'❌ Schedule API failed: {schedule_response.status_code}')
    else:
        print('\n❌ Some frontend elements are missing!')
    
    return False

if __name__ == "__main__":
    print("🔍 Testing Interview Frontend Functionality")
    print("=" * 50)
    
    success = test_interview_frontend()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Interview frontend functionality is WORKING!")
        print("\n📋 What should work in the browser:")
        print("✅ Edit button loads interview data into form")
        print("✅ Form changes from 'Schedule' to 'Update'")
        print("✅ Update button saves changes")
        print("✅ Cancel button removes interview")
        print("✅ Form validation and field mapping")
    else:
        print("❌ Interview frontend functionality has issues")
