#!/usr/bin/env python3
"""
Test HR Portal endpoints directly to identify the issue
"""

import requests

def test_hr_portal_endpoints():
    print("=== HR Portal Endpoint Test ===")
    
    endpoints = [
        ('/', 'Home'),
        ('/login', 'Login'),
        ('/dashboard', 'Dashboard'),
        ('/jobs', 'Jobs'),
        ('/post-job', 'Post Job')
    ]
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f'http://localhost:8003{endpoint}', timeout=5)
            print(f'{name} ({endpoint}): {response.status_code}')
            if response.status_code >= 400:
                print(f'  Error: {response.text[:200]}')
        except Exception as e:
            print(f'{name} ({endpoint}): Error - {str(e)}')

if __name__ == '__main__':
    test_hr_portal_endpoints()
