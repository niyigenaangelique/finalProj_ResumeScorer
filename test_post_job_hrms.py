#!/usr/bin/env python3
"""
Test script to verify HRMS integration on post-job page
"""

import requests
import json
import time

def test_post_job_hrms_integration():
    """Test HRMS integration on post-job page"""
    print("=== Testing Post-Job Page HRMS Integration ===")
    
    session = requests.Session()
    
    try:
        # Login
        login_data = {'email': 'angelbrenna20@gmail.com', 'password': 'Niyigena2003@'}
        response = session.post('http://localhost:8003/login', data=login_data, allow_redirects=False)
        print(f"Login: {response.status_code}")
        
        # Test HRMS metadata
        response = session.get('http://localhost:8003/api/hrms-metadata')
        print(f"HRMS metadata: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Departments: {len(data['departments'])}")
            print(f"✓ Positions: {len(data['positions'])}")
            print(f"✓ Shifts: {len(data['shifts'])}")
        else:
            print("✗ HRMS metadata not available")
            return False
        
        # Test post-job page
        response = session.get('http://localhost:8003/post-job')
        print(f"Post-job page: {response.status_code}")
        
        if response.status_code == 200:
            page_content = response.text
            
            # Check for HRMS functions
            if 'loadHrmsMeta' in page_content:
                print("✓ HRMS loading functions present")
            else:
                print("✗ HRMS loading functions missing")
                return False
            
            # Check for dropdown elements
            if 'id="department"' in page_content:
                print("✓ Department dropdown present")
            else:
                print("✗ Department dropdown missing")
                return False
                
            if 'id="job_title"' in page_content:
                print("✓ Job title dropdown present")
            else:
                print("✗ Job title dropdown missing")
                return False
                
            if 'id="work_mode"' in page_content:
                print("✓ Work mode dropdown present")
            else:
                print("✗ Work mode dropdown missing")
                return False
            
            # Check for HRMS data loading call
            if 'loadHrmsData' in page_content:
                print("✓ HRMS data loading call present")
            else:
                print("✗ HRMS data loading call missing")
                return False
            
            return True
        else:
            print(f"✗ Post-job page error: {response.text}")
            return False
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_job_creation_on_post_job():
    """Test actual job creation on post-job page"""
    print("\n=== Testing Job Creation on Post-Job Page ===")
    
    session = requests.Session()
    
    try:
        # Login
        login_data = {'email': 'angelbrenna20@gmail.com', 'password': 'Niyigena2003@'}
        response = session.post('http://localhost:8003/login', data=login_data, allow_redirects=False)
        
        # Test job creation with HRMS data
        job_data = {
            'job_title': 'Software Engineer',
            'department': 'Engineering',
            'employment_type': 'full-time',
            'experience_level': 'mid',
            'location': 'Kigali, Rwanda',
            'work_mode': 'Day Shift',
            'job_description': 'Test job description from post-job page',
            'requirements': 'Test requirements from post-job page'
        }
        
        response = session.post('http://localhost:8003/api/post-job', 
                               json=job_data, 
                               headers={'Content-Type': 'application/json'})
        print(f"Job creation: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✓ Job creation successful")
                print(f"✓ Job ID: {result.get('job_id')}")
                return True
            else:
                print(f"✗ Job creation failed: {result.get('error')}")
                return False
        else:
            print(f"✗ Job creation error: {response.text}")
            return False
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Post-Job Page HRMS Integration Test")
    print("=" * 50)
    
    # Test 1: HRMS integration
    hrms_success = test_post_job_hrms_integration()
    
    # Test 2: Job creation
    creation_success = test_job_creation_on_post_job()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"HRMS Integration: {'✓ PASS' if hrms_success else '✗ FAIL'}")
    print(f"Job Creation: {'✓ PASS' if creation_success else '✗ FAIL'}")
    
    if hrms_success and creation_success:
        print("\n✓ SUCCESS: Post-job page HRMS integration is working!")
        print("✓ Departments, positions, and shifts load automatically")
        exit(0)
    else:
        print("\n✗ FAILED: Some issues found with post-job HRMS integration")
        exit(1)
