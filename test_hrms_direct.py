#!/usr/bin/env python3
"""
Direct test of HRMS metadata functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_hrms_metadata_directly():
    """Test HRMS metadata function directly"""
    print("=== Testing HRMS Metadata Directly ===")
    
    try:
        # Import the function directly
        from hr_jobs import hrms_metadata
        
        # Create a mock request
        class MockRequest:
            def __init__(self):
                self.cookies = {"hr_token": "test_token"}
                self.headers = {}
                self.query_params = {}
                self.method = "GET"
                self.url = "/api/hrms-metadata"
        
        # Test the function directly
        import asyncio
        
        async def test_async():
            mock_request = MockRequest()
            result = await hrms_metadata(mock_request)
            print(f"Result type: {type(result)}")
            print(f"Result status: {result.status_code}")
            
            if hasattr(result, 'body'):
                import json
                body = result.body.decode('utf-8')
                data = json.loads(body)
                print(f"Departments: {len(data.get('departments', []))}")
                print(f"Positions: {len(data.get('positions', []))}")
                print(f"Shifts: {len(data.get('shifts', []))}")
                
                if len(data.get('positions', [])) == 0:
                    print("✗ ISSUE: Positions array is empty!")
                    return False
                else:
                    print("✓ Positions are populated")
                    return True
            return False
        
        return asyncio.run(test_async())
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_hrms_defaults():
    """Test the HRMS defaults directly"""
    print("\n=== Testing HRMS Defaults ===")
    
    try:
        # Check the current defaults in hr_jobs.py
        from hr_jobs import _hrms_base_url, _hrms_headers
        
        print(f"HRMS Base URL: {_hrms_base_url()}")
        print(f"HRMS Headers: {_hrms_headers()}")
        
        # Test the defaults by looking at the function
        import inspect
        source = inspect.getsource(hrms_metadata)
        
        if '"positions": []' in source:
            print("✗ ISSUE: Default positions array is empty!")
            return False
        else:
            print("✓ Default positions array should be populated")
            return True
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("HRMS Metadata Direct Test")
    print("=" * 40)
    
    # Test 1: Direct function test
    direct_success = test_hrms_metadata_directly()
    
    # Test 2: Defaults test
    defaults_success = test_hrms_defaults()
    
    print("\n" + "=" * 40)
    print("SUMMARY:")
    print(f"Direct Function Test: {'✓ PASS' if direct_success else '✗ FAIL'}")
    print(f"Defaults Test: {'✓ PASS' if defaults_success else '✗ FAIL'}")
    
    if not (direct_success and defaults_success):
        print("\n✗ ISSUE IDENTIFIED: HRMS positions are not loading")
        print("This is why the job title dropdown is empty")
        sys.exit(1)
    else:
        print("\n✓ HRMS integration is working correctly")
        sys.exit(0)
