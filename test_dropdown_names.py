#!/usr/bin/env python3
"""
Test that job position and department dropdowns display names instead of codes
"""

import requests

def test_dropdown_names():
    print("=== Testing Dropdown Name Display ===")
    
    try:
        # Test HRMS metadata to ensure positions are available
        session = requests.Session()
        login_data = {'email': 'angelbrenna20@gmail.com', 'password': 'Niyigena2003@'}
        response = session.post('http://localhost:8003/login', data=login_data, timeout=5)
        print(f'Login status: {response.status_code}')
        
        # Test HRMS metadata
        response = session.get('http://localhost:8003/api/hrms-metadata', timeout=5)
        print(f'HRMS metadata status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            positions = data.get('positions', [])
            departments = data.get('departments', [])
            
            print(f'✓ Positions available: {len(positions)}')
            print(f'✓ Departments available: {len(departments)}')
            
            # Check for specific codes
            if 'POS-003' in positions:
                print('✓ POS-003 (Accountant) available')
            if 'FIN' in departments:
                print('✓ FIN (Finance) available')
                
            # Test the jobs page to verify dropdown functionality
            response = session.get('http://localhost:8003/jobs', timeout=5)
            print(f'Jobs page status: {response.status_code}')
            
            if response.status_code == 200:
                content = response.text
                
                # Check if the updated _fillSelect function is present
                if 'positionTitles' in content and 'departmentTitles' in content:
                    print('✓ Updated _fillSelect function with mappings found')
                else:
                    print('❌ Updated _fillSelect function not found')
                    
                # Check for specific mappings
                if 'Software Engineer' in content:
                    print('✓ Software Engineer mapping found')
                if 'Human Resources' in content:
                    print('✓ Human Resources mapping found')
                    
        else:
            print(f'❌ HRMS metadata error: {response.status_code}')
            
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    test_dropdown_names()
