#!/usr/bin/env python3
"""
Check modern portal content for proper title display
"""

import requests

def check_portal_content():
    try:
        response = requests.get('http://localhost:8005/')
        if response.status_code == 200:
            content = response.text
            
            print("=== Checking for Department Names ===")
            departments = ['Human Resources', 'Information Technology', 'Finance', 'Networking', 'Automation Lab']
            dept_codes = ['HR', 'IT', 'FIN', 'DEPT-001', 'DEP-0002']
            
            for dept in departments:
                if dept in content:
                    print(f"✓ Found: {dept}")
                else:
                    print(f"✗ Missing: {dept}")
            
            print("\n=== Checking for Position Titles ===")
            positions = ['Software Engineer', 'HR Manager', 'Accountant', 'Marketing Specialist', 'Project Manager']
            pos_codes = ['POS-001', 'POS-002', 'POS-003', 'POS-004', 'POS-005']
            
            for pos in positions:
                if pos in content:
                    print(f"✓ Found: {pos}")
                else:
                    print(f"✗ Missing: {pos}")
            
            print("\n=== Checking for Codes (should NOT be present) ===")
            for code in dept_codes + pos_codes:
                if code in content:
                    print(f"✗ Code still present: {code}")
                else:
                    print(f"✓ Code removed: {code}")
            
            print("\n=== Checking Enhanced Data Structure ===")
            if 'department_title' in content:
                print("✓ department_title found in template")
            else:
                print("✗ department_title not found in template")
                
            if 'title_display' in content:
                print("✓ title_display found in template")
            else:
                print("✗ title_display not found in template")
            
            # Show a snippet of the content around job cards
            if 'job-card' in content:
                print("\n=== Job Card Sample ===")
                start = content.find('job-card')
                if start != -1:
                    snippet = content[start:start+500]
                    print(snippet[:300] + "..." if len(snippet) > 300 else snippet)
        else:
            print(f"Error: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    check_portal_content()
