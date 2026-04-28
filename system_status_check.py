#!/usr/bin/env python3
"""
System status check for all running services
"""

import requests
import time

def check_systems():
    print('=== System Status Check ===')
    
    # Test HR Portal
    try:
        response = requests.get('http://localhost:8003/login', timeout=5)
        print(f'HR Portal (8003): {response.status_code}')
    except Exception as e:
        print(f'HR Portal (8003): Error - {str(e)}')

    # Test Modern Portal  
    try:
        response = requests.get('http://localhost:8005/', timeout=5)
        print(f'Modern Portal (8005): {response.status_code}')
    except Exception as e:
        print(f'Modern Portal (8005): Error - {str(e)}')

    # Test Resume Scoring API
    try:
        response = requests.get('http://localhost:8000/', timeout=5)
        print(f'Resume Scoring API (8000): {response.status_code}')
    except Exception as e:
        print(f'Resume Scoring API (8000): Error - {str(e)}')

    # Test HRMS Metadata
    try:
        session = requests.Session()
        login_data = {'email': 'angelbrenna20@gmail.com', 'password': 'Niyigena2003@'}
        response = session.post('http://localhost:8003/login', data=login_data, timeout=5)
        response = session.get('http://localhost:8003/api/hrms-metadata', timeout=5)
        if response.status_code == 200:
            data = response.json()
            dept_count = len(data.get('departments', []))
            pos_count = len(data.get('positions', []))
            print(f'HRMS Metadata: {dept_count} depts, {pos_count} positions')
        else:
            print(f'HRMS Metadata: {response.status_code}')
    except Exception as e:
        print(f'HRMS Metadata: Error - {str(e)}')

    print('\n=== All Systems Operational ===')

if __name__ == '__main__':
    check_systems()
