import os
import re
from database import ResumeDatabase
from resume_cv_generator import ResumeCVGenerator

# Initialize database and generator
db = ResumeDatabase()
generator = ResumeCVGenerator()

def extract_job_requirements(job):
    """Simple extraction of requirements from job description and requirements field"""
    full_text = f"{job['title']} {job['description']} {job['requirements']}".lower()
    
    # Extract years
    years_match = re.search(r'(\d+)\+?\s*years?', full_text)
    years = int(years_match.group(1)) if years_match else 3
    
    # Common technical skills to look for
    common_skills = [
        'python', 'javascript', 'java', 'sql', 'aws', 'azure', 'gcp', 'docker', 
        'kubernetes', 'react', 'angular', 'vue', 'node', 'servicenow', 'glide',
        'figma', 'sketch', 'tableau', 'power bi', 'agile', 'scrum', 'marketing',
        'seo', 'sem', 'devops', 'git', 'machine learning', 'data analysis'
    ]
    
    skills = [s for s in common_skills if s in full_text]
    
    # Certifications
    certs_list = ['CSA', 'CIS', 'CAD', 'CIS-EM', 'CSM', 'CSP', 'PMP', 'AWS', 'Azure']
    certs = [c for c in certs_list if c.lower() in full_text]
    
    return {
        'title': job['title'],
        'years': years,
        'skills': skills,
        'certs': certs,
        'department': job['department']
    }

def generate_high_score_data(reqs):
    # Ensure at least some skills even if not found
    all_skills = list(set(reqs['skills'] + ['Communication', 'Leadership', 'Problem Solving', 'Teamwork']))
    
    return {
        'name': f"Premium Candidate - {reqs['title']}",
        'contact': f"premium.candidate@example.com | +250 780 000 000 | Kigali, Rwanda",
        'summary': f"Highly accomplished {reqs['title']} with over {reqs['years'] + 3} years of proven expertise in {reqs['department']}. Recognized for driving technical excellence and delivering high-impact solutions in complex environments.",
        'skills': [s.upper() for s in all_skills],
        'experience': [
            {
                'title': f"Senior {reqs['title']}",
                'company': "Global Tech Innovations",
                'period': "2019 - Present",
                'desc': f"Leading large-scale implementations of {', '.join(reqs['skills'][:3])}. Mentored junior developers and improved system efficiency by 45%. Expertly utilized {', '.join(reqs['skills'])} to achieve business goals."
            },
            {
                'title': reqs['title'],
                'company': "Regional Solutions Ltd",
                'period': "2015 - 2019",
                'desc': f"Developed and maintained core modules. Specialized in {reqs['skills'][-1] if reqs['skills'] else 'Technical Development'}. Received 'Employee of the Year' award for outstanding performance."
            }
        ],
        'certifications': reqs['certs'] + (['ServiceNow Certified System Administrator (CSA)'] if 'servicenow' in reqs['skills'] else []),
        'education': [
            {'degree': f"Master of Science in Computer Science", 'school': "Top Tier University", 'year': "2015"},
            {'degree': f"Bachelor of Engineering", 'school': "National University", 'year': "2013"}
        ]
    }

def generate_low_score_data(reqs):
    return {
        'name': f"Ineligible Candidate - {reqs['title']}",
        'contact': f"ineligible.candidate@example.com | +250 780 111 222 | Kigali, Rwanda",
        'summary': f"I want this job.",
        'skills': ['None'],
        'experience': [
            {
                'title': "None",
                'company': "N/A",
                'period': "N/A",
                'desc': "No prior work."
            }
        ],
        'certifications': [],
        'education': [
            {'degree': "None", 'school': "N/A", 'year': "N/A"}
        ]
    }

from modern_portal import AIAgent, _extract_experience_years, _extract_skills, _extract_certifications, _extract_education, _extract_job_experience_requirement, _extract_job_skills, _extract_job_certifications

ai_agent = AIAgent()

def calculate_expected_score(data, job):
    # Convert structured data to text for the scorers
    text = f"{data['name']}\n{data['summary']}\n{' '.join(data['skills'])}\n"
    for exp in data['experience']:
        text += f"{exp['title']} {exp['company']} {exp['desc']}\n"
    text += " ".join(data.get('certifications', [])) + "\n"
    for edu in data['education']:
        text += f"{edu['degree']} {edu['school']}\n"
        
    resume_data = {
        'id': 1,
        'name': data['name'],
        'resume_text': text,
        'experience_years': _extract_experience_years(text),
        'skills': _extract_skills(text),
        'certifications': _extract_certifications(text),
        'education_level': _extract_education(text)
    }
    
    job_text = f"{job['description']} {job['requirements']}"
    job_requirements = {
        'id': job['id'],
        'title': job['title'],
        'experience_years': _extract_job_experience_requirement(job_text),
        'technical_skills': _extract_job_skills(job_text),
        'certifications': _extract_job_certifications(job_text)
    }
    
    result = ai_agent.screen_candidate(resume_data, job_requirements)
    return result['screening_score']

def main():
    jobs = db.get_all_jobs()
    print(f"Found {len(jobs)} jobs. Generating CVs with Score Marks...")
    
    output_dir = 'generated_cvs'
    os.makedirs(output_dir, exist_ok=True)
    
    for job in jobs:
        reqs = extract_job_requirements(job)
        job_slug = job['title'].lower().replace(' ', '_')
        
        # High Score CV
        high_data = generate_high_score_data(reqs)
        high_score = calculate_expected_score(high_data, job)
        high_file = f"{output_dir}/{job['id']}_{job_slug}_SCORE_{high_score:.0f}_HIGH.pdf"
        generator.generate_resume(high_data, high_file, score=high_score)
        
        # Low Score CV
        low_data = generate_low_score_data(reqs)
        low_score = calculate_expected_score(low_data, job)
        low_file = f"{output_dir}/{job['id']}_{job_slug}_SCORE_{low_score:.0f}_LOW.pdf"
        generator.generate_resume(low_data, low_file, score=low_score)
        
        print(f"Generated CVs for {job['title']} (Scores: {high_score:.0f} / {low_score:.0f})")

if __name__ == "__main__":
    main()
