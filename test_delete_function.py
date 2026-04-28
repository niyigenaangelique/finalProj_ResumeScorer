#!/usr/bin/env python3
"""
Test the delete job functionality
"""

import requests

def test_delete_job():
    print("=== Testing Delete Job Functionality ===")
    
    try:
        # Login first
        session = requests.Session()
        login_data = {'email': 'angelbrenna20@gmail.com', 'password': 'Niyigena2003@'}
        response = session.post('http://localhost:8003/login', data=login_data, timeout=5)
        print(f'Login status: {response.status_code}')
        
        # Get a list of jobs to find one to delete
        response = session.get('http://localhost:8003/api/job-details/20', timeout=5)
        print(f'Job details status: {response.status_code}')
        
        if response.status_code == 200:
            job_data = response.json()
            print(f'Job found: {job_data.get("title", "N/A")} - {job_data.get("department", "N/A")}')
            
            # Test the delete endpoint
            response = session.post('http://localhost:8003/api/delete-job', 
                                  json={'job_id': 20}, timeout=5)
            print(f'Delete API status: {response.status_code}')
            
            if response.status_code == 200:
                result = response.json()
                print(f'Delete response: {result}')
                if result.get('success'):
                    print('✅ Delete functionality working')
                else:
                    print(f'❌ Delete failed: {result.get("error", "Unknown error")}')
            else:
                print(f'❌ Delete API error: {response.status_code}')
                print(f'Error content: {response.text[:200]}')
        else:
            print(f'❌ Could not get job details: {response.status_code}')
            
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    test_delete_job()
