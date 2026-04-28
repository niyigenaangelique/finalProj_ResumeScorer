#!/usr/bin/env python3
"""
Debug script to capture the actual server-side error
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the job management function directly
from hr_jobs import job_management
from database import ResumeDatabase
from hr_base import get_current_user

class MockRequest:
    """Mock request object for testing"""
    def __init__(self, cookies=None):
        self.cookies = cookies or {}
        self.headers = {}
        self.query_params = {}
        self.method = "GET"
        self.url = "/jobs"

def test_job_management_function():
    """Test the job_management function directly with a mock request"""
    print("=== Testing job_management function directly ===")
    
    try:
        # Create a mock request with authentication
        mock_request = MockRequest(cookies={"hr_token": "test_token"})
        
        # This will fail because we don't have a real session, but let's see what happens
        result = job_management(mock_request)
        print("Function executed successfully")
        return True
        
    except Exception as e:
        print(f"Error in job_management function: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_real_session():
    """Test with a simulated real session"""
    print("\n=== Testing with simulated session ===")
    
    try:
        # Import the sessions dictionary and create a real session
        from hr_base import sessions, create_session
        
        # Create a real session
        email = "angelbrenna20@gmail.com"
        token = create_session(email)
        print(f"Created session token: {token[:10]}...")
        
        # Create mock request with real token
        mock_request = MockRequest(cookies={"hr_token": token})
        
        # Test the job management function
        result = job_management(mock_request)
        print("Function executed successfully with real session")
        return True
        
    except Exception as e:
        print(f"Error with real session: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_components():
    """Test individual components of the job management page"""
    print("\n=== Testing individual components ===")
    
    try:
        from hr_base import get_base_html, get_end_html
        from hr_jobs import _build_job_rows, _build_app_rows
        
        db = ResumeDatabase()
        
        # Test database calls
        jobs = db.get_all_jobs()
        applications = db.get_all_applications()
        print(f"Database calls successful: {len(jobs)} jobs, {len(applications)} applications")
        
        # Test HTML building
        job_rows = _build_job_rows(jobs)
        app_rows = _build_app_rows(applications)
        print(f"HTML building successful: {len(job_rows)} job rows, {len(app_rows)} app rows")
        
        # Test base HTML
        current_user = "angelbrenna20@gmail.com"
        base_html = get_base_html("Job Management", "jobs", current_user)
        end_html = get_end_html()
        print(f"Base HTML building successful: {len(base_html)} chars")
        
        return True
        
    except Exception as e:
        print(f"Error in components: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Server Error Debug Script")
    print("=" * 50)
    
    # Test 1: Individual components
    component_success = test_individual_components()
    
    # Test 2: Mock request (will likely fail)
    mock_success = test_job_management_function()
    
    # Test 3: Real session simulation
    session_success = test_with_real_session()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Component Tests: {'✓ PASS' if component_success else '✗ FAIL'}")
    print(f"Mock Request Test: {'✓ PASS' if mock_success else '✗ FAIL'}")
    print(f"Real Session Test: {'✓ PASS' if session_success else '✗ FAIL'}")
    
    if not (component_success and session_success):
        print("\nError identified in the job_management function or its dependencies.")
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)
