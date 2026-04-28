#!/usr/bin/env python3
"""
Debug the job data enhancement functionality
"""

from database import ResumeDatabase
from modern_portal import enhance_job_data

def debug_enhancement():
    db = ResumeDatabase()
    jobs = db.get_all_jobs()
    print(f'Found {len(jobs)} jobs in database')
    
    if jobs:
        print('\nSample job data before enhancement:')
        job = jobs[0]
        print(f'  Title: {job.get("title", "N/A")}')
        print(f'  Department: {job.get("department", "N/A")}')
        
        # Test enhancement
        enhanced_jobs = enhance_job_data(jobs)
        enhanced_job = enhanced_jobs[0]
        print('\nAfter enhancement:')
        print(f'  Title Display: {enhanced_job.get("title_display", "N/A")}')
        print(f'  Department Title: {enhanced_job.get("department_title", "N/A")}')
        
        # Show all jobs with their codes and titles
        print('\nAll jobs with enhancement:')
        for i, job in enumerate(enhanced_jobs):
            print(f'  Job {i+1}: {job.get("title_display", "N/A")} - {job.get("department_title", "N/A")}')
    else:
        print('No jobs found in database')

if __name__ == '__main__':
    debug_enhancement()
