#!/usr/bin/env python3
"""
Debug script to test the async job_management function properly
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_job_management_async():
    """Test the job_management function properly as async"""
    print("=== Testing job_management function as async ===")
    
    try:
        # Import the async function
        from hr_jobs import job_management
        from hr_base import sessions, create_session
        
        # Create a real session
        email = "angelbrenna20@gmail.com"
        token = create_session(email)
        print(f"Created session token: {token[:10]}...")
        
        # Create mock request with real token
        class MockRequest:
            def __init__(self, cookies=None):
                self.cookies = cookies or {}
                self.headers = {}
                self.query_params = {}
                self.method = "GET"
                self.url = "/jobs"
        
        mock_request = MockRequest(cookies={"hr_token": token})
        
        # Test the async job management function
        result = await job_management(mock_request)
        print("✓ Async function executed successfully")
        print(f"Result type: {type(result)}")
        if hasattr(result, 'body'):
            print(f"Response body length: {len(result.body)}")
        return True
        
    except Exception as e:
        print(f"✗ Error in async job_management: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_database_calls_async():
    """Test database calls that might be causing issues"""
    print("\n=== Testing database calls in async context ===")
    
    try:
        from database import ResumeDatabase
        
        db = ResumeDatabase()
        
        # Test all database calls used in job_management
        jobs = db.get_all_jobs()
        print(f"✓ get_all_jobs: {len(jobs)} jobs")
        
        applications = db.get_all_applications()
        print(f"✓ get_all_applications: {len(applications)} applications")
        
        # Check for any data issues that might cause template rendering errors
        print("Checking job data for issues...")
        for i, job in enumerate(jobs[:3]):  # Check first 3 jobs
            print(f"Job {i+1}: {job.get('title', 'No title')} - {job.get('status', 'No status')}")
        
        print("Checking application data for issues...")
        for i, app in enumerate(applications[:3]):  # Check first 3 applications
            print(f"App {i+1}: {app.get('applicant_name', 'No name')} - {app.get('status', 'No status')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in database calls: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_template_rendering():
    """Test template rendering components"""
    print("\n=== Testing template rendering ===")
    
    try:
        from hr_jobs import _build_job_rows, _build_app_rows
        from database import ResumeDatabase
        
        db = ResumeDatabase()
        jobs = db.get_all_jobs()
        applications = db.get_all_applications()
        
        # Test job rows building
        job_rows = _build_job_rows(jobs)
        print(f"✓ Job rows built: {len(job_rows)} characters")
        
        # Test application rows building
        app_rows = _build_app_rows(applications)
        print(f"✓ Application rows built: {len(app_rows)} characters")
        
        # Check for any HTML issues in the generated content
        if '<script>' in job_rows or '<script>' in app_rows:
            print("⚠ Warning: Script tags found in generated content")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in template rendering: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main async test function"""
    print("Async Server Error Debug Script")
    print("=" * 50)
    
    # Test 1: Database calls
    db_success = await test_database_calls_async()
    
    # Test 2: Template rendering
    template_success = await test_template_rendering()
    
    # Test 3: Full async function
    async_success = await test_job_management_async()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Database Calls: {'✓ PASS' if db_success else '✗ FAIL'}")
    print(f"Template Rendering: {'✓ PASS' if template_success else '✗ FAIL'}")
    print(f"Full Async Function: {'✓ PASS' if async_success else '✗ FAIL'}")
    
    if not async_success:
        print("\nError identified in the async job_management function.")
        return 1
    else:
        print("\nAll async tests passed!")
        return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
