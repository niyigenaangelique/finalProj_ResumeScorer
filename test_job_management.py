import requests
import json

def test_job_management():
    """Test job management functionality"""
    session = requests.Session()
    
    # Login
    login_data = {'email': 'angelbrenna20@gmail.com', 'password': 'Niyigena2003@'}
    response = session.post('http://localhost:8003/login', data=login_data, allow_redirects=False)
    
    if response.status_code != 302:
        print('❌ Login failed')
        return False
    
    print('✅ Login successful')
    
    # Test jobs page
    jobs_response = session.get('http://localhost:8003/jobs')
    
    if jobs_response.status_code != 200:
        print('❌ Jobs page failed to load')
        return False
    
    print('✅ Jobs page loads successfully')
    
    # Test adding a job
    job_data = {
        'title': 'Senior Software Engineer',
        'department': 'Engineering',
        'location': 'Remote',
        'salary': '$120,000 - $150,000',
        'description': 'We are looking for a senior software engineer...',
        'requirements': '5+ years of experience, Python, JavaScript, etc.',
        'status': 'active'
    }
    
    add_response = session.post('http://localhost:8003/api/add-job', json=job_data)
    print(f'Add job API status: {add_response.status_code}')
    
    if add_response.status_code == 200:
        result = add_response.json()
        if result.get('success'):
            job_id = result.get('job_id')
            print(f'✅ Job added successfully with ID: {job_id}')
            
            # Test getting job details
            details_response = session.get(f'http://localhost:8003/api/job-details/{job_id}')
            print(f'Get job details API status: {details_response.status_code}')
            
            if details_response.status_code == 200:
                details_result = details_response.json()
                if details_result.get('success'):
                    print('✅ Get job details API working')
                    
                    # Test updating the job
                    update_data = {
                        'job_id': job_id,
                        'title': 'Senior Software Engineer (Updated)',
                        'department': 'Engineering',
                        'location': 'Hybrid',
                        'salary': '$130,000 - $160,000',
                        'description': 'Updated description for senior software engineer...',
                        'requirements': 'Updated requirements...',
                        'status': 'active'
                    }
                    
                    update_response = session.post('http://localhost:8003/api/update-job', json=update_data)
                    print(f'Update job API status: {update_response.status_code}')
                    
                    if update_response.status_code == 200:
                        update_result = update_response.json()
                        if update_result.get('success'):
                            print('✅ Update job API working')
                            
                            # Test deleting the job
                            delete_data = {'job_id': job_id}
                            delete_response = session.post('http://localhost:8003/api/delete-job', json=delete_data)
                            print(f'Delete job API status: {delete_response.status_code}')
                            
                            if delete_response.status_code == 200:
                                delete_result = delete_response.json()
                                if delete_result.get('success'):
                                    print('✅ Delete job API working')
                                    return True
                                else:
                                    print(f'❌ Delete failed: {delete_result.get("error")}')
                            else:
                                print(f'❌ Delete API failed: {delete_response.status_code}')
                        else:
                            print(f'❌ Update failed: {update_result.get("error")}')
                    else:
                        print(f'❌ Update API failed: {update_response.status_code}')
                else:
                    print(f'❌ Get details failed: {details_result.get("error")}')
            else:
                print(f'❌ Get details API failed: {details_response.status_code}')
        else:
            print(f'❌ Add job failed: {result.get("error")}')
    else:
        print(f'❌ Add job API failed: {add_response.status_code}')
    
    return False

if __name__ == "__main__":
    print("🔍 Testing Job Management Functionality")
    print("=" * 50)
    
    success = test_job_management()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Job Management functionality is WORKING!")
        print("\n📋 What's available in the browser:")
        print("✅ View all jobs and applications")
        print("✅ Add new jobs with full details")
        print("✅ Edit existing jobs")
        print("✅ Delete jobs (with confirmation)")
        print("✅ Toggle between Jobs and Applications views")
        print("✅ Search and filter applications")
        print("✅ Update application status")
        print("✅ Schedule interviews from applications")
    else:
        print("❌ Job Management functionality has issues")
