#!/usr/bin/env python3
"""
Test job position selection functionality
"""

import requests

def test_position_selection():
    print("=== Testing Job Position Selection ===")
    
    try:
        # Test HRMS metadata endpoint
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
            print(f'Positions available: {len(positions)}')
            if positions:
                print(f'First few positions: {positions[:5]}')
            else:
                print('❌ No positions found in HRMS metadata')
        else:
            print(f'❌ HRMS metadata error: {response.status_code}')
            
        # Test the jobs page to see if position dropdown loads
        response = session.get('http://localhost:8003/jobs', timeout=5)
        print(f'Jobs page status: {response.status_code}')
        
        if response.status_code == 200:
            content = response.text
            if 'jobTitle' in content:
                print('✅ Job title dropdown element found')
            else:
                print('❌ Job title dropdown element not found')
                
            if 'loadHrmsMeta' in content:
                print('✅ HRMS loading function found')
            else:
                print('❌ HRMS loading function not found')
                
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    test_position_selection()
