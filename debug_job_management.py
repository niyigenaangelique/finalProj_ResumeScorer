#!/usr/bin/env python3
"""
Debug script to identify the specific error in job management page
"""

import requests
import traceback
import sys
from database import ResumeDatabase

def test_job_management_directly():
    """Test the job management functions directly"""
    print("=== Testing Database Functions Directly ===")
    try:
        db = ResumeDatabase()
        
        # Test get_all_jobs
        print("Testing get_all_jobs...")
        jobs = db.get_all_jobs()
        print(f"✓ get_all_jobs returned {len(jobs)} jobs")
        
        # Test get_all_applications
        print("Testing get_all_applications...")
        applications = db.get_all_applications()
        print(f"✓ get_all_applications returned {len(applications)} applications")
        
        # Test get_statistics
        print("Testing get_statistics...")
        try:
            stats = db.get_statistics()
            print(f"✓ get_statistics returned: {stats}")
        except Exception as e:
            print(f"✗ get_statistics failed: {e}")
            traceback.print_exc()
        
        print("Database functions test completed successfully")
        return True
        
    except Exception as e:
        print(f"Database functions test failed: {e}")
        traceback.print_exc()
        return False

def test_job_management_page():
    """Test the job management page via HTTP"""
    print("\n=== Testing Job Management Page via HTTP ===")
    try:
        session = requests.Session()
        
        # First login
        print("Logging in...")
        login_data = {'email': 'angelbrenna20@gmail.com', 'password': 'Niyigena2003@'}
        response = session.post('http://localhost:8003/login', data=login_data, allow_redirects=False)
        print(f"Login response: {response.status_code}")
        
        # Test jobs page
        print("Accessing jobs page...")
        response = session.get('http://localhost:8003/jobs', allow_redirects=False)
        print(f"Jobs page response: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error response content: {response.text[:1000]}")
            return False
        else:
            print("✓ Jobs page loaded successfully")
            return True
            
    except Exception as e:
        print(f"HTTP test failed: {e}")
        traceback.print_exc()
        return False

def test_job_management_components():
    """Test individual components that might be causing the error"""
    print("\n=== Testing Job Management Components ===")
    
    try:
        # Import and test the job management function
        from hr_jobs import _build_job_rows, _build_app_rows, _badge, _STATUS_JOB, _STATUS_APP
        
        print("Testing _badge function...")
        badge_html = _badge("badge-green", "Test")
        print(f"✓ _badge works: {badge_html[:50]}...")
        
        print("Testing _build_job_rows...")
        db = ResumeDatabase()
        jobs = db.get_all_jobs()
        job_rows = _build_job_rows(jobs)
        print(f"✓ _build_job_rows works: {len(job_rows)} characters")
        
        print("Testing _build_app_rows...")
        applications = db.get_all_applications()
        app_rows = _build_app_rows(applications)
        print(f"✓ _build_app_rows works: {len(app_rows)} characters")
        
        return True
        
    except Exception as e:
        print(f"Component test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Job Management Debug Script")
    print("=" * 50)
    
    # Test 1: Database functions directly
    db_success = test_job_management_directly()
    
    # Test 2: Component functions
    component_success = test_job_management_components()
    
    # Test 3: HTTP request
    http_success = test_job_management_page()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Database Functions: {'✓ PASS' if db_success else '✗ FAIL'}")
    print(f"Component Functions: {'✓ PASS' if component_success else '✗ FAIL'}")
    print(f"HTTP Page Load: {'✓ PASS' if http_success else '✗ FAIL'}")
    
    if not http_success:
        print("\nThe error is likely in the HTTP request handling or template rendering.")
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)
