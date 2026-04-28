#!/usr/bin/env python3
"""
Simple test for modern portal title display
"""

import requests

def test_portal():
    try:
        response = requests.get('http://localhost:8000/')
        print(f'Status: {response.status_code}')
        
        if response.status_code == 200:
            content = response.text
            
            # Check for titles
            if 'Human Resources' in content:
                print('✓ Found Human Resources')
            if 'Software Engineer' in content:
                print('✓ Found Software Engineer')
            if 'Accountant' in content:
                print('✓ Found Accountant')
                
            # Check if still showing codes
            if 'POS-003' in content:
                print('✗ Still showing POS-003 code')
            if 'FIN' in content:
                print('✗ Still showing FIN code')
                
        else:
            print(f'Error: {response.status_code}')
            
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    test_portal()
