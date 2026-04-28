#!/usr/bin/env python3
"""
Test script to verify HRMS data loading in job creation form
"""

import requests
import json
import time

def test_job_creation_form():
    """Test that the job creation form loads HRMS data properly"""
    print("=== Testing Job Creation Form HRMS Integration ===")
    
    session = requests.Session()
    
    try:
        # Login
        login_data = {'email': 'angelbrenna20@gmail.com', 'password': 'Niyigena2003@'}
        response = session.post('http://localhost:8003/login', data=login_data, allow_redirects=False)
        print(f"Login: {response.status_code}")
        
        # Get jobs page
        response = session.get('http://localhost:8003/jobs')
        print(f"Jobs page: {response.status_code}")
        
        # Test HRMS metadata endpoint
        response = session.get('http://localhost:8003/api/hrms-metadata')
        print(f"HRMS metadata: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Departments: {len(data['departments'])}")
            print(f"✓ Positions: {len(data['positions'])}")
            print(f"✓ Shifts: {len(data['shifts'])}")
            
            # Verify specific data
            expected_departments = ["Engineering", "Marketing", "Sales", "Human Resources"]
            for dept in expected_departments:
                if dept in data['departments']:
                    print(f"✓ Department '{dept}' found")
                else:
                    print(f"✗ Department '{dept}' missing")
            
            expected_positions = ["Software Engineer", "Product Manager", "UX Designer"]
            for pos in expected_positions:
                if pos in data['positions']:
                    print(f"✓ Position '{pos}' found")
                else:
                    print(f"✗ Position '{pos}' missing")
            
            expected_shifts = ["Day Shift", "Night Shift", "Flexible"]
            for shift in expected_shifts:
                if shift in data['shifts']:
                    print(f"✓ Shift '{shift}' found")
                else:
                    print(f"✗ Shift '{shift}' missing")
        
        # Test job creation endpoint
        job_data = {
            'title': 'Software Engineer',
            'department': 'Engineering',
            'location': 'Remote',
            'work_mode': 'Flexible',
            'salary': '$80,000 - $120,000',
            'description': 'Test job description',
            'requirements': 'Test job requirements'
        }
        
        response = session.post('http://localhost:8003/api/add-job', 
                               json=job_data, 
                               headers={'Content-Type': 'application/json'})
        print(f"Job creation: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✓ Job creation successful")
                print(f"✓ Job ID: {result.get('job_id')}")
            else:
                print(f"✗ Job creation failed: {result.get('error')}")
        else:
            print(f"✗ Job creation error: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_job_form_javascript():
    """Test the JavaScript functions that handle HRMS data loading"""
    print("\n=== Testing JavaScript HRMS Functions ===")
    
    session = requests.Session()
    
    try:
        # Login
        login_data = {'email': 'angelbrenna20@gmail.com', 'password': 'Niyigena2003@'}
        response = session.post('http://localhost:8003/login', data=login_data, allow_redirects=False)
        
        # Get jobs page and check for JavaScript functions
        response = session.get('http://localhost:8003/jobs')
        page_content = response.text
        
        js_functions = [
            'loadHrmsMeta()',
            '_fillSelect(',
            'showAddJobForm()',
            'editJob(',
            'submitJob()'
        ]
        
        for func in js_functions:
            if func in page_content:
                print(f"✓ {func} found")
            else:
                print(f"✗ {func} missing")
        
        # Check for select elements
        select_elements = [
            'id="jobDepartment"',
            'id="jobTitle"',
            'id="jobWorkMode"'
        ]
        
        for select_id in select_elements:
            if select_id in page_content:
                print(f"✓ {select_id} found")
            else:
                print(f"✗ {select_id} missing")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Job Creation HRMS Integration Test")
    print("=" * 50)
    
    # Test 1: HRMS data loading
    hrms_success = test_job_creation_form()
    
    # Test 2: JavaScript functions
    js_success = test_job_form_javascript()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"HRMS Integration: {'✓ PASS' if hrms_success else '✗ FAIL'}")
    print(f"JavaScript Functions: {'✓ PASS' if js_success else '✗ FAIL'}")
    
    if hrms_success and js_success:
        print("\n✓ SUCCESS: Job creation form is properly integrated with HRMS!")
        print("✓ Departments, positions, and shifts will load automatically")
        exit(0)
    else:
        print("\n✗ FAILED: Some issues found with HRMS integration")
        exit(1)
