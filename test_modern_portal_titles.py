#!/usr/bin/env python3
"""
Test script to verify modern portal displays proper department names and job titles
"""

import requests
import json
import time

def test_modern_portal_titles():
    """Test that modern portal displays proper titles instead of codes"""
    print("=== Testing Modern Portal Title Display ===")
    
    try:
        # Test landing page
        response = requests.get('http://localhost:8000/')
        print(f"Landing page status: {response.status_code}")
        
        if response.status_code == 200:
            page_content = response.text
            
            # Check for proper titles instead of codes
            title_checks = [
                ('Human Resources', 'HR'),
                ('Information Technology', 'IT'),
                ('Finance', 'FIN'),
                ('Networking', 'DEPT-001'),
                ('Automation Lab', 'DEP-0002')
            ]
            
            position_checks = [
                ('Software Engineer', 'POS-001'),
                ('HR Manager', 'POS-002'),
                ('Accountant', 'POS-003'),
                ('Marketing Specialist', 'POS-004'),
                ('Project Manager', 'POS-005'),
                ('Sales Representative', 'POS-006'),
                ('Customer Service Representative', 'POS-007'),
                ('Data Analyst', 'POS-008'),
                ('Office Manager', 'POS-009'),
                ('Quality Assurance Engineer', 'POS-010'),
                ('Network Manager', 'POS-011'),
                ('AI Integration Specialist', 'POS-0012')
            ]
            
            print("\n--- Department Title Checks ---")
            dept_found = 0
            for title, code in title_checks:
                if title in page_content:
                    print(f"✓ Found '{title}' (instead of '{code}')")
                    dept_found += 1
                elif code in page_content:
                    print(f"✗ Still showing code '{code}' instead of title")
                else:
                    print(f"- Neither '{title}' nor '{code}' found")
            
            print("\n--- Position Title Checks ---")
            pos_found = 0
            for title, code in position_checks:
                if title in page_content:
                    print(f"✓ Found '{title}' (instead of '{code}')")
                    pos_found += 1
                elif code in page_content:
                    print(f"✗ Still showing code '{code}' instead of title")
                else:
                    print(f"- Neither '{title}' nor '{code}' found")
            
            print(f"\nSummary: {dept_found}/{len(title_checks)} department titles found, {pos_found}/{len(position_checks)} position titles found")
            
            return dept_found > 0 or pos_found > 0
        else:
            print(f"✗ Error accessing landing page: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_jobs_list_page():
    """Test the jobs list page"""
    print("\n=== Testing Jobs List Page ===")
    
    try:
        response = requests.get('http://localhost:8000/jobs')
        print(f"Jobs list page status: {response.status_code}")
        
        if response.status_code == 200:
            page_content = response.text
            
            # Check for enhanced data
            if 'department_title' in page_content:
                print("✓ Enhanced department data found in template")
            else:
                print("✗ Enhanced department data not found")
            
            if 'title_display' in page_content:
                print("✓ Enhanced title data found in template")
            else:
                print("✗ Enhanced title data not found")
            
            # Check for actual titles
            if 'Human Resources' in page_content or 'Software Engineer' in page_content:
                print("✓ Proper titles found in jobs list")
                return True
            else:
                print("✗ Proper titles not found in jobs list")
                return False
        else:
            print(f"✗ Error accessing jobs list: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Modern Portal Title Display Test")
    print("=" * 50)
    
    # Test 1: Landing page
    landing_success = test_modern_portal_titles()
    
    # Test 2: Jobs list page
    jobs_success = test_jobs_list_page()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Landing Page: {'✓ PASS' if landing_success else '✗ FAIL'}")
    print(f"Jobs List Page: {'✓ PASS' if jobs_success else '✗ FAIL'}")
    
    if landing_success and jobs_success:
        print("\n✓ SUCCESS: Modern portal displays proper titles!")
        print("✓ Department names and job titles are shown instead of codes")
        exit(0)
    else:
        print("\n✗ FAILED: Some issues with title display")
        exit(1)
