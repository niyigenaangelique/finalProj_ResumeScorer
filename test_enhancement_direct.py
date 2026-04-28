#!/usr/bin/env python3
"""
Test the enhancement function directly
"""

from modern_portal import enhance_job_data, get_department_title, get_position_title

def test_enhancement():
    # Test the mapping functions directly
    print("=== Testing Mapping Functions ===")
    print(f"get_department_title('FIN') = {get_department_title('FIN')}")
    print(f"get_position_title('POS-003') = {get_position_title('POS-003')}")
    
    # Test with sample job data
    print("\n=== Testing Enhancement Function ===")
    test_jobs = [
        {'title': 'POS-003', 'department': 'FIN'},
        {'title': 'Software Engineer', 'department': 'Engineering'},
        {'title': 'POS-001', 'department': 'HR'}
    ]
    
    enhanced = enhance_job_data(test_jobs)
    for job in enhanced:
        print(f"Job: {job.get('title')} -> {job.get('title_display')}")
        print(f"Dept: {job.get('department')} -> {job.get('department_title')}")
        print()

if __name__ == '__main__':
    test_enhancement()
