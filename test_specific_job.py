#!/usr/bin/env python3
"""
Test the specific POS-003 FIN job to see if titles are displaying correctly
"""

import requests

def test_specific_job():
    print("=== Testing POS-003 FIN Job Display ===")
    
    try:
        # Test the jobs list page
        response = requests.get('http://localhost:8005/jobs', timeout=5)
        if response.status_code == 200:
            content = response.text
            
            # Check for the specific job
            if 'Accountant' in content and 'Finance' in content:
                print("✓ Found 'Accountant' and 'Finance' on jobs page")
            else:
                print("✗ 'Accountant' and 'Finance' not found on jobs page")
                
            if 'POS-003' in content or 'FIN' in content:
                print("✗ Codes 'POS-003' or 'FIN' still present on jobs page")
            else:
                print("✓ Codes 'POS-003' and 'FIN' removed from jobs page")
                
        # Test the landing page
        response = requests.get('http://localhost:8005/', timeout=5)
        if response.status_code == 200:
            content = response.text
            
            if 'Accountant' in content and 'Finance' in content:
                print("✓ Found 'Accountant' and 'Finance' on landing page")
            else:
                print("✗ 'Accountant' and 'Finance' not found on landing page")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_specific_job()
