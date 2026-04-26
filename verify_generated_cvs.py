import os
import json
from database import ResumeDatabase
from modern_portal import AIAgent, _extract_experience_years, _extract_skills, _extract_certifications, _extract_education, _extract_job_experience_requirement, _extract_job_skills, _extract_job_certifications
from simple_app import SimpleResumeScorer

db = ResumeDatabase()
ai_agent = AIAgent()
traditional_scorer = SimpleResumeScorer()

def main():
    jobs = db.get_all_jobs()
    print(f"{'Job Title':<30} | {'AI High':<8} | {'AI Low':<8} | {'Trad High':<10}")
    print("-" * 70)
    
    # We'll use the same logic as the portal to generate scores from data
    from generate_cvs_for_jobs import extract_job_requirements, generate_high_score_data, generate_low_score_data
    
    for job in jobs[:5]: # Check first 5 for brevity
        reqs = extract_job_requirements(job)
        
        # High Score Data
        high_data = generate_high_score_data(reqs)
        # Convert structured data back to text for the scorers
        high_text = f"{high_data['name']}\n{high_data['summary']}\n{' '.join(high_data['skills'])}\n"
        for exp in high_data['experience']:
            high_text += f"{exp['title']} {exp['company']} {exp['desc']}\n"
        high_text += " ".join(high_data['certifications']) + "\n"
        for edu in high_data['education']:
            high_text += f"{edu['degree']} {edu['school']}\n"
            
        # AI Screening logic (from modern_portal.py submit_application)
        resume_data_high = {
            'id': 1,
            'name': high_data['name'],
            'resume_text': high_text,
            'experience_years': _extract_experience_years(high_text),
            'skills': _extract_skills(high_text),
            'certifications': _extract_certifications(high_text),
            'education_level': _extract_education(high_text)
        }
        
        job_requirements = {
            'id': job['id'],
            'title': job['title'],
            'experience_years': _extract_job_experience_requirement(f"{job['description']} {job['requirements']}"),
            'technical_skills': _extract_job_skills(f"{job['description']} {job['requirements']}"),
            'certifications': _extract_job_certifications(f"{job['description']} {job['requirements']}")
        }
        
        high_ai_result = ai_agent.screen_candidate(resume_data_high, job_requirements)
        high_trad_result = traditional_scorer.score_resume(high_text)
        
        # Low Score Data
        low_data = generate_low_score_data(reqs)
        low_text = f"{low_data['name']}\n{low_data['summary']}\n{' '.join(low_data['skills'])}\n"
        for exp in low_data['experience']:
            low_text += f"{exp['title']} {exp['company']} {exp['desc']}\n"
        
        resume_data_low = {
            'id': 2,
            'name': low_data['name'],
            'resume_text': low_text,
            'experience_years': _extract_experience_years(low_text),
            'skills': _extract_skills(low_text),
            'certifications': _extract_certifications(low_text),
            'education_level': _extract_education(low_text)
        }
        
        low_ai_result = ai_agent.screen_candidate(resume_data_low, job_requirements)
        
        print(f"{job['title'][:30]:<30} | {high_ai_result['screening_score']:<8.1f} | {low_ai_result['screening_score']:<8.1f} | {high_trad_result['score']:<10.1f}")

if __name__ == "__main__":
    main()
