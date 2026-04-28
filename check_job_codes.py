#!/usr/bin/env python3
"""
Check what codes are actually in the job database
"""

from database import ResumeDatabase

def check_job_codes():
    db = ResumeDatabase()
    jobs = db.get_all_jobs()
    
    print('=== Current Job Data ===')
    departments = set()
    titles = set()
    
    for job in jobs:
        dept = job.get('department', 'N/A')
        title = job.get('title', 'N/A')
        departments.add(dept)
        titles.add(title)
        
        if 'POS-003' in title or 'FIN' in dept:
            print(f'Found target job: {title} in {dept}')
    
    print(f'\nDepartments found: {sorted(departments)}')
    print(f'Titles found: {sorted(titles)}')
    
    # Check for any jobs with your specific codes
    target_jobs = [job for job in jobs if 'POS-003' in job.get('title', '') or 'FIN' in job.get('department', '')]
    print(f'\nJobs with POS-003 or FIN: {len(target_jobs)}')
    for job in target_jobs:
        print(f'  - {job.get("title", "N/A")} in {job.get("department", "N/A")}')

if __name__ == '__main__':
    check_job_codes()
