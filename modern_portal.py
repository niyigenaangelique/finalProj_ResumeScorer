from fastapi import FastAPI, Request, HTTPException, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from database import ResumeDatabase
from simple_app import SimpleResumeScorer
from typing import List, Dict, Any, Optional
import io
import pypdf
import json
import re

app = FastAPI(title="Talent Flow Style Portal", description="Modern recruitment portal")
db = ResumeDatabase()
scorer = SimpleResumeScorer()

class AIAgent:
    """AI Agent for intelligent recruitment automation"""
    
    def __init__(self):
        self.screening_criteria = {
            "experience_years": 3,
            "certifications": ["CSA", "CIS", "CAD", "CIS-EM", "CSM", "CSP"],
            "technical_skills": ["JavaScript", "Glide", "Flow Designer", "Integration Hub", "Service Portal"],
            "soft_skills": ["communication", "problem-solving", "teamwork", "leadership"]
        }
    
    def screen_candidate(self, resume_data: Dict[str, Any], job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """AI-powered candidate screening - Enhanced for better scoring"""
        score = 40  # Base score for applying
        max_score = 100
        
        # Experience matching - more generous scoring
        candidate_exp = resume_data.get("experience_years", 0)
        required_exp = job_requirements.get("experience_years", 0)
        if candidate_exp >= required_exp:
            score += 30
        elif candidate_exp >= required_exp * 0.5:
            score += 20
        elif candidate_exp > 0:
            score += 10
        
        # Skills matching - broader skill recognition
        candidate_skills = [skill.lower() for skill in resume_data.get("skills", [])]
        required_skills = [skill.lower() for skill in job_requirements.get("technical_skills", [])]
        
        # Add common related skills
        expanded_skills = set(candidate_skills)
        skill_synonyms = {
            'javascript': ['js', 'typescript', 'node', 'nodejs'],
            'servicenow': ['servicenow platform', 'now platform', 'snc'],
            'react': ['reactjs', 'react.js', 'jsx'],
            'angular': ['angularjs', 'angular.js', 'ng'],
            'html': ['html5', 'markup'],
            'css': ['css3', 'sass', 'scss', 'styling'],
            'sql': ['database', 'mysql', 'postgresql', 'oracle'],
            'git': ['github', 'gitlab', 'version control']
        }
        
        for skill in candidate_skills:
            for synonym in skill_synonyms.get(skill, []):
                expanded_skills.add(synonym)
        
        skill_match = len(expanded_skills & set(required_skills))
        if required_skills:
            skill_percentage = skill_match / len(required_skills)
            score += skill_percentage * 25
        
        # Certification matching - more recognition
        candidate_certs = [cert.lower() for cert in resume_data.get("certifications", [])]
        required_certs = [cert.lower() for cert in job_requirements.get("certifications", [])]
        
        # Recognize related certifications
        cert_bonus = 0
        for cert in candidate_certs:
            if any(req in cert for req in required_certs):
                cert_bonus += 1
            elif 'csa' in cert or 'cis' in cert or 'cad' in cert:
                cert_bonus += 0.5
        
        score += min(cert_bonus * 10, 20)
        
        # Education bonus
        education = resume_data.get("education_level", "").lower()
        if education in ["master", "phd", "doctorate"]:
            score += 10
        elif education in ["bachelor", "bs", "ba", "b.s.", "b.a."]:
            score += 5
        
        # Bonus for having any relevant experience
        if candidate_exp > 0:
            score += 5
        
        # Bonus for having multiple skills
        if len(candidate_skills) >= 5:
            score += 5
        elif len(candidate_skills) >= 3:
            score += 3
        
        # Build detailed match summary
        matched_skills = list(set(candidate_skills) & set(required_skills))
        missing_skills = list(set(required_skills) - set(candidate_skills))
        
        summary = f"Candidate has {candidate_exp} years of experience (Required: {required_exp}). "
        if candidate_exp >= required_exp:
            summary += "Experience requirements met. "
        else:
            summary += "Experience gap identified. "
            
        summary += f"Matched {len(matched_skills)}/{len(required_skills)} technical skills. "
        
        return {
            "candidate_id": resume_data.get("id"),
            "screening_score": round(score, 2),
            "max_score": max_score,
            "status": "shortlisted" if score >= 70 else "review_needed" if score >= 50 else "rejected",
            "match_details": {
                "summary": summary,
                "experience_match": candidate_exp >= required_exp,
                "certification_match": f"{int(cert_bonus)}/{len(required_certs)}",
                "skill_match": f"{skill_match}/{len(required_skills)}",
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "education_level": resume_data.get("education_level")
            }
        }
    
    def generate_interview_questions(self, resume_data: Dict[str, Any], job_requirements: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate intelligent interview questions based on candidate profile and job requirements"""
        questions = []
        
        # Technical questions based on skills gap
        candidate_skills = [skill.lower() for skill in resume_data.get("skills", [])]
        required_skills = [skill.lower() for skill in job_requirements.get("technical_skills", [])]
        skill_gaps = set(required_skills) - set(candidate_skills)
        
        for skill in list(skill_gaps)[:3]:
            questions.append({
                "type": "technical",
                "question": f"Can you describe your experience with {skill} and how you've applied it in ServiceNow projects?",
                "category": "Technical Assessment"
            })
        
        # Experience-based questions
        experience_years = resume_data.get("experience_years", 0)
        if experience_years < 2:
            questions.append({
                "type": "experience",
                "question": "Since you're early in your ServiceNow career, what specific projects have demonstrated your ability to learn quickly and deliver results?",
                "category": "Experience Assessment"
            })
        elif experience_years > 5:
            questions.append({
                "type": "experience",
                "question": "With your extensive ServiceNow experience, can you share an example of how you've mentored junior developers or led complex implementations?",
                "category": "Leadership Assessment"
            })
        
        # Behavioral questions
        questions.extend([
            {
                "type": "behavioral",
                "question": "Describe a challenging ServiceNow implementation you worked on and how you overcame obstacles to deliver successfully.",
                "category": "Problem Solving"
            },
            {
                "type": "behavioral",
                "question": "How do you stay updated with ServiceNow platform changes and new features?",
                "category": "Continuous Learning"
            }
        ])
        
        return questions
    
    def filter_candidates(self, candidates: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Intelligent candidate filtering with AI-powered ranking"""
        filtered_candidates = []
        
        for candidate in candidates:
            # Apply filters
            if filters.get("department") and candidate.get("department") != filters["department"]:
                continue
            
            if filters.get("job_type") and candidate.get("job_type") != filters["job_type"]:
                continue
            
            if filters.get("min_experience") and candidate.get("experience_years", 0) < filters["min_experience"]:
                continue
            
            # AI-powered relevance scoring
            relevance_score = self._calculate_relevance(candidate, filters)
            candidate["ai_relevance_score"] = relevance_score
            filtered_candidates.append(candidate)
        
        # Sort by AI relevance score
        filtered_candidates.sort(key=lambda x: x.get("ai_relevance_score", 0), reverse=True)
        return filtered_candidates
    
    def _calculate_relevance(self, candidate: Dict[str, Any], filters: Dict[str, Any]) -> float:
        """Calculate AI-powered relevance score"""
        score = 0
        
        # Skills matching
        if filters.get("required_skills"):
            candidate_skills = [skill.lower() for skill in candidate.get("skills", [])]
            required_skills = [skill.lower() for skill in filters["required_skills"]]
            skill_match = len(set(candidate_skills) & set(required_skills))
            score += (skill_match / len(required_skills)) * 40
        
        # Experience bonus
        exp_years = candidate.get("experience_years", 0)
        if exp_years >= 5:
            score += 20
        elif exp_years >= 3:
            score += 10
        
        # Certification bonus
        certs = candidate.get("certifications", [])
        if any(cert in self.screening_criteria["certifications"] for cert in certs):
            score += 20
        
        # Recent activity bonus
        if candidate.get("last_active_days", 999) <= 30:
            score += 10
        
        # Education bonus
        if candidate.get("education_level") in ["Master", "PhD"]:
            score += 10
        
        return min(score, 100)

# Initialize AI Agent
ai_agent = AIAgent()

# ─────────────────────────────────────────────────────────────────────────────
#  SHARED PIECES
# ─────────────────────────────────────────────────────────────────────────────

_BASE_HEAD = """<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Nunito+Sans:wght@300;400;600&display=swap" rel="stylesheet">
<style>
:root{--blue:#3b5bdb;--blue-dark:#2846c4;--blue-light:#5c7cfa;--violet:#7048e8;--red:#fa5252;--white:#ffffff;--off:#f8f9fc;--text:#2d3748;--muted:#718096;--border:#e8edf5;--card-sh:0 8px 40px rgba(59,91,219,.10);--card-sh-h:0 16px 60px rgba(59,91,219,.18);}
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{font-family:'Nunito Sans',sans-serif;background:var(--white);color:var(--text);overflow-x:hidden;}
::-webkit-scrollbar{width:4px;}::-webkit-scrollbar-thumb{background:var(--blue);border-radius:2px;}
@keyframes fadeUp{from{opacity:0;transform:translateY(30px)}to{opacity:1;transform:translateY(0)}}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes floatUI{0%,100%{transform:translateY(0)}50%{transform:translateY(-14px)}}
@keyframes slideDown{from{opacity:0;transform:translateY(-16px)}to{opacity:1;transform:translateY(0)}}
@keyframes loaderOut{to{opacity:0;pointer-events:none}}
@keyframes spin{to{transform:rotate(360deg)}}
.page-loader{position:fixed;inset:0;background:var(--white);z-index:9999;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:1rem;animation:loaderOut .3s 1s ease both;}
.loader-logo{font-family:'Nunito',sans-serif;font-size:1.6rem;font-weight:900;color:var(--blue);}
.loader-spin{width:28px;height:28px;border:3px solid var(--border);border-top-color:var(--blue);border-radius:50%;animation:spin .7s linear infinite;}
.reveal{opacity:0;transform:translateY(28px);transition:opacity .65s ease,transform .65s ease;}
.reveal.visible{opacity:1;transform:translateY(0);}
.reveal-d1{transition-delay:.1s}.reveal-d2{transition-delay:.2s}.reveal-d3{transition-delay:.3s}.reveal-d4{transition-delay:.4s}
nav{position:fixed;top:0;left:0;right:0;z-index:200;display:flex;align-items:center;justify-content:space-between;padding:.9rem 4rem;background:rgba(255,255,255,.96);backdrop-filter:blur(16px);box-shadow:0 2px 20px rgba(59,91,219,.08);animation:slideDown .5s ease both;}
.nav-logo{font-family:'Nunito',sans-serif;font-size:1.3rem;font-weight:900;color:var(--blue);text-decoration:none;display:flex;align-items:center;gap:.5rem;}
.nav-logo-dot{width:8px;height:8px;border-radius:50%;background:var(--red);display:inline-block;}
.nav-links-list{display:flex;align-items:center;gap:2.5rem;list-style:none;}
.nav-links-list a{color:var(--text);text-decoration:none;font-size:.88rem;font-weight:600;transition:color .2s;}
.nav-links-list a:hover{color:var(--blue);}
.nav-signin{background:var(--red);color:var(--white);padding:.55rem 1.5rem;border-radius:4px;font-weight:700;font-size:.88rem;text-decoration:none;transition:background .2s,transform .2s;}
.nav-signin:hover{background:#e53e3e;transform:translateY(-1px);}
.hero{min-height:100vh;background:linear-gradient(135deg,var(--blue) 0%,var(--violet) 55%,#6b3fcf 100%);position:relative;overflow:hidden;display:flex;align-items:center;padding:7rem 4rem 5rem;}
.hero::after{content:'';position:absolute;bottom:-2px;left:0;right:0;height:120px;background:var(--white);clip-path:polygon(0 60%,100% 0,100% 100%,0 100%);}
.hero-blob{position:absolute;border-radius:50%;filter:blur(60px);pointer-events:none;}
.hero-blob-1{width:400px;height:400px;background:rgba(255,255,255,.06);top:-100px;right:30%;}
.hero-blob-2{width:250px;height:250px;background:rgba(112,72,232,.4);bottom:10%;left:5%;}
.hero-content{position:relative;z-index:2;display:flex;align-items:center;gap:3rem;width:100%;}
.hero-text{flex:0 0 auto;max-width:500px;z-index:3;}
.hero-images{flex:1;display:flex;gap:1.5rem;position:relative;z-index:2;opacity:0;animation:floatUI 5s 1s ease-in-out infinite,fadeIn .9s .6s ease both;}
.hero-main-image{flex:2;}
.hero-side-images{flex:1;display:flex;flex-direction:column;gap:1rem;}
.hero-img-large{width:100%;height:auto;object-fit:cover;border-radius:20px;box-shadow:0 40px 100px rgba(0,0,0,.20);transition:transform 0.3s ease, box-shadow 0.3s ease;}
.hero-img-main{max-height:650px;}
.hero-img-side{max-height:300px;}
.hero-img-1{transform:rotate(-2deg);}
.hero-img-2{transform:rotate(1deg);}
.hero-img-3{transform:rotate(0deg);}
.hero-img-large:hover{transform:rotate(0deg) translateY(-10px);box-shadow:0 50px 120px rgba(0,0,0,.35);}
.hero h1{font-family:'Nunito',sans-serif;font-size:clamp(2.4rem,5vw,3.4rem);font-weight:900;color:var(--white);line-height:1.15;margin-bottom:1.25rem;opacity:0;animation:fadeUp .8s .3s ease both;}
.hero-sub{font-size:1rem;color:rgba(255,255,255,.82);line-height:1.8;margin-bottom:2rem;opacity:0;animation:fadeUp .8s .5s ease both;}
.hero-btn{display:inline-flex;align-items:center;gap:.6rem;background:var(--red);color:var(--white);padding:.85rem 2rem;border-radius:4px;font-weight:800;font-size:.92rem;text-decoration:none;opacity:0;animation:fadeUp .8s .7s ease both;transition:background .2s,transform .2s,box-shadow .2s;}
.hero-btn:hover{background:#e53e3e;transform:translateY(-2px);box-shadow:0 8px 30px rgba(250,82,82,.4);}
.mockup-card{background:var(--white);border-radius:16px;box-shadow:0 30px 80px rgba(0,0,0,.25);padding:1.5rem;position:relative;}
.mockup-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:1.25rem;}
.mockup-title{font-family:'Nunito',sans-serif;font-size:.95rem;font-weight:800;color:var(--text);}
.mockup-badge{background:var(--blue);color:#fff;font-size:.65rem;font-weight:700;padding:.2rem .6rem;border-radius:999px;}
.mockup-stat{display:flex;align-items:center;gap:1rem;margin-bottom:1rem;}
.mockup-circle{width:64px;height:64px;border-radius:50%;background:conic-gradient(var(--blue) 0% 68%,var(--border) 68% 100%);display:flex;align-items:center;justify-content:center;font-family:'Nunito',sans-serif;font-size:.82rem;font-weight:900;color:var(--blue);}
.mockup-rows{display:flex;flex-direction:column;gap:.5rem;flex:1;}
.mockup-row{height:8px;background:var(--border);border-radius:4px;overflow:hidden;}
.mockup-row-fill{height:100%;background:linear-gradient(90deg,var(--blue),var(--blue-light));border-radius:4px;}
.mockup-tags{display:flex;gap:.5rem;flex-wrap:wrap;margin-top:1rem;}
.mockup-tag{font-size:.7rem;font-weight:700;padding:.25rem .7rem;border-radius:999px;background:var(--off);color:var(--muted);}
.mockup-tag.active{background:rgba(59,91,219,.12);color:var(--blue);}
.mockup-mini{position:absolute;left:-90px;top:40%;background:var(--white);border-radius:12px;box-shadow:0 10px 40px rgba(0,0,0,.15);padding:1rem 1.25rem;min-width:190px;}
.mini-label{font-size:.7rem;color:var(--muted);font-weight:600;margin-bottom:.4rem;}
.mini-title{font-family:'Nunito',sans-serif;font-size:.92rem;font-weight:800;color:var(--text);margin-bottom:.4rem;}
.mini-bar-wrap{height:6px;background:var(--border);border-radius:3px;overflow:hidden;}
.mini-bar{height:100%;width:72%;background:var(--red);border-radius:3px;}
.services-section{padding:5rem 4rem;background:var(--white);}
.services-intro{display:grid;grid-template-columns:1fr 1fr;gap:5rem;align-items:start;}
.eyebrow{display:inline-block;font-size:.72rem;font-weight:700;color:var(--blue);letter-spacing:.18em;text-transform:uppercase;margin-bottom:1rem;}
.section-title{font-family:'Nunito',sans-serif;font-size:clamp(1.8rem,3.5vw,2.4rem);font-weight:900;color:var(--text);line-height:1.2;margin-bottom:1rem;}
.section-title span{color:var(--blue);}
.cards-grid{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;}
.svc-card{background:var(--white);border-radius:14px;padding:2rem;box-shadow:var(--card-sh);transition:transform .3s,box-shadow .3s;position:relative;overflow:hidden;}
.svc-card:hover{transform:translateY(-6px);box-shadow:var(--card-sh-h);}
.svc-card::before{content:'';position:absolute;top:0;left:0;width:3px;height:0;background:var(--blue);transition:height .4s ease;}
.svc-card:hover::before{height:100%;}
.svc-icon{width:44px;height:44px;border-radius:10px;background:rgba(59,91,219,.1);display:flex;align-items:center;justify-content:center;font-size:1.2rem;margin-bottom:1.25rem;}
.svc-card h3{font-family:'Nunito',sans-serif;font-size:1rem;font-weight:800;color:var(--text);margin-bottom:.6rem;}
.svc-card p{font-size:.87rem;color:var(--muted);line-height:1.7;margin-bottom:1rem;}
.read-more{font-size:.82rem;font-weight:700;color:var(--blue);text-decoration:none;display:inline-flex;align-items:center;gap:.4rem;transition:gap .2s;}
.read-more:hover{gap:.7rem;}
.diag-divider{height:80px;background:var(--off);clip-path:polygon(0 0,100% 40%,100% 100%,0 100%);}
.diag-divider-rev{height:80px;background:var(--white);clip-path:polygon(0 40%,100% 0,100% 100%,0 100%);}
.about-section{background:var(--off);padding:6rem 4rem;}
.about-grid{display:flex;align-items:center;gap:0;justify-content:space-between;}
.about-image{width:320px;height:320px;border-radius:360px;object-fit:cover;box-shadow:0 20px 60px rgba(59,91,219,.15);animation:floatUI 6s ease-in-out infinite;margin-right:0;flex-shrink:0;}
.about-content p{font-size:.95rem;color:var(--muted);line-height:1.85;margin-bottom:1rem;}
.about-actions{display:flex;align-items:center;gap:1.25rem;margin-top:2rem;flex-wrap:wrap;}
.about-btn{background:var(--red);color:var(--white);padding:.75rem 1.75rem;border-radius:4px;font-weight:800;font-size:.88rem;text-decoration:none;transition:background .2s,transform .2s;}
.about-btn:hover{background:#e53e3e;transform:translateY(-1px);}
.why-section{background:var(--white);padding:6rem 4rem;}
.why-grid{display:grid;grid-template-columns:1fr 1fr;gap:2.5rem;margin-top:4rem;}
.why-card{display:flex;gap:1.25rem;align-items:flex-start;}
.why-icon{width:52px;height:52px;border-radius:12px;background:var(--off);display:flex;align-items:center;justify-content:center;font-size:1.3rem;flex-shrink:0;transition:background .3s,transform .3s;}
.why-card:hover .why-icon{background:rgba(59,91,219,.1);transform:scale(1.08);}
.why-card h4{font-family:'Nunito',sans-serif;font-size:.98rem;font-weight:800;color:var(--text);margin-bottom:.5rem;}
.why-card p{font-size:.87rem;color:var(--muted);line-height:1.7;}
.jobs-section{background:var(--off);padding:6rem 4rem;}
.jobs-header{text-align:center;margin-bottom:3rem;}
.jobs-header p{color:var(--muted);font-size:.97rem;max-width:520px;margin:.75rem auto 0;line-height:1.75;}
.filter-bar{display:flex;gap:.75rem;justify-content:center;flex-wrap:wrap;margin-bottom:2.5rem;}
.filter-btn{padding:.5rem 1.25rem;border:2px solid var(--border);background:var(--white);color:var(--muted);border-radius:999px;font-size:.82rem;font-family:'Nunito Sans',sans-serif;font-weight:700;cursor:pointer;transition:all .25s;}
.filter-btn:hover,.filter-btn.active{border-color:var(--blue);color:var(--blue);background:rgba(59,91,219,.07);}
.jobs-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1.5rem;}
.job-card{background:var(--white);border-radius:14px;padding:1.75rem;box-shadow:var(--card-sh);transition:transform .3s,box-shadow .3s;}
.job-card:hover{transform:translateY(-5px);box-shadow:var(--card-sh-h);}
.job-card-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1rem;}
.dept-tag{font-size:.7rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--blue);background:rgba(59,91,219,.1);padding:.28rem .75rem;border-radius:999px;}
.type-tag{font-size:.7rem;font-weight:700;color:var(--muted);background:var(--off);padding:.28rem .75rem;border-radius:999px;}
.job-name{font-family:'Nunito',sans-serif;font-size:1.05rem;font-weight:800;margin-bottom:.6rem;color:var(--text);}
.job-blurb{font-size:.86rem;color:var(--muted);line-height:1.7;margin-bottom:1.25rem;}
.job-foot{display:flex;justify-content:space-between;align-items:center;padding-top:1rem;border-top:1px solid var(--border);}
.job-sal{font-size:.82rem;font-weight:700;color:#2f855a;}
.job-cta{display:inline-flex;align-items:center;gap:.4rem;font-size:.82rem;font-weight:700;color:var(--blue);text-decoration:none;transition:gap .2s;}
.job-cta:hover{gap:.7rem;}
.testi-section{background:var(--white);padding:6rem 4rem;}
.testi-grid{display:grid;grid-template-columns:1fr 1fr;gap:5rem;align-items:center;}
.avatar-cluster{position:relative;width:280px;height:280px;margin:0 auto;}
.av{position:absolute;width:68px;height:68px;border-radius:50%;border:3px solid var(--white);box-shadow:0 4px 20px rgba(0,0,0,.12);background:var(--off);display:flex;align-items:center;justify-content:center;font-size:1.7rem;}
.av-1{top:0;left:50%;transform:translateX(-50%)}.av-2{top:22%;left:0}.av-3{top:22%;right:0}.av-4{bottom:12%;left:12%}.av-5{bottom:12%;right:12%}.av-6{bottom:0;left:50%;transform:translateX(-50%)}
.active-av{border-color:var(--blue);box-shadow:0 0 0 4px rgba(59,91,219,.2);}
.testi-content blockquote{font-family:'Nunito',sans-serif;font-size:1.15rem;font-weight:700;color:var(--text);line-height:1.65;margin-bottom:1.5rem;font-style:italic;}
.testi-author{font-weight:700;color:var(--text);font-size:.9rem;}
.testi-author span{color:var(--muted);font-weight:400;}
.read-more-btn{display:inline-flex;align-items:center;gap:.5rem;background:var(--red);color:var(--white);padding:.7rem 1.6rem;border-radius:4px;font-weight:700;font-size:.85rem;text-decoration:none;margin-top:1.75rem;transition:background .2s,transform .2s;}
.read-more-btn:hover{background:#e53e3e;transform:translateY(-1px);}
.bottom-section{background:linear-gradient(135deg,var(--blue) 0%,var(--violet) 60%,#6b3fcf 100%);padding:6rem 4rem;position:relative;overflow:hidden;}
.bottom-section::before{content:'';position:absolute;top:-80px;left:0;right:0;height:120px;background:var(--white);clip-path:polygon(0 0,100% 60%,100% 100%,0 100%);}
.bottom-grid{display:grid;grid-template-columns:1fr 1fr;gap:5rem;position:relative;z-index:2;}
.newsletter h3{font-family:'Nunito',sans-serif;font-size:1.6rem;font-weight:900;color:var(--white);margin-bottom:.75rem;}
.newsletter p{color:rgba(255,255,255,.8);font-size:.95rem;line-height:1.75;margin-bottom:1.5rem;}
.nl-input{width:100%;padding:.8rem 1.1rem;border:none;border-radius:4px;font-size:.9rem;font-family:'Nunito Sans',sans-serif;margin-bottom:.75rem;background:rgba(255,255,255,.15);color:var(--white);}
.nl-input::placeholder{color:rgba(255,255,255,.5);}
.nl-input:focus{outline:none;background:rgba(255,255,255,.22);}
.nl-btn{background:var(--red);color:var(--white);border:none;padding:.8rem 2rem;border-radius:4px;font-weight:800;font-size:.9rem;cursor:pointer;transition:background .2s,transform .2s;font-family:'Nunito Sans',sans-serif;}
.nl-btn:hover{background:#e53e3e;transform:translateY(-1px);}
.contact-card{background:var(--white);border-radius:16px;padding:2.5rem;box-shadow:0 20px 60px rgba(0,0,0,.2);}
.contact-card h3{font-family:'Nunito',sans-serif;font-size:1.3rem;font-weight:900;color:var(--text);margin-bottom:1.5rem;}
.cf-input{width:100%;padding:.8rem 1rem;border:2px solid var(--border);border-radius:6px;font-size:.9rem;font-family:'Nunito Sans',sans-serif;margin-bottom:1rem;transition:border-color .25s;color:var(--text);}
.cf-input:focus{outline:none;border-color:var(--blue);}
.cf-input::placeholder{color:#b0b8c8;}
.cf-textarea{resize:vertical;min-height:90px;}
.cf-btn{background:var(--red);color:var(--white);border:none;padding:.8rem 2rem;border-radius:4px;font-weight:800;font-size:.9rem;cursor:pointer;width:100%;transition:background .2s,transform .2s;font-family:'Nunito Sans',sans-serif;}
.cf-btn:hover{background:#e53e3e;transform:translateY(-1px);}
.site-footer{background:#1a1f36;padding:3.5rem 4rem 2rem;color:rgba(255,255,255,.65);}
.footer-grid{display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1.5fr;gap:3rem;margin-bottom:3rem;}
.footer-brand-logo{font-family:'Nunito',sans-serif;font-size:1.3rem;font-weight:900;color:var(--white);text-decoration:none;display:flex;align-items:center;gap:.5rem;margin-bottom:1rem;}
.footer-brand-desc{font-size:.87rem;line-height:1.7;}
.footer-col h4{font-family:'Nunito',sans-serif;font-size:.88rem;font-weight:800;color:var(--white);margin-bottom:1rem;}
.footer-col ul{list-style:none;display:flex;flex-direction:column;gap:.6rem;}
.footer-col a{color:rgba(255,255,255,.6);text-decoration:none;font-size:.85rem;transition:color .2s;}
.footer-col a:hover{color:var(--white);}
.footer-addr{font-size:.85rem;line-height:1.9;}
.footer-addr a{color:rgba(255,255,255,.6);text-decoration:none;}
.footer-bottom{border-top:1px solid rgba(255,255,255,.1);padding-top:1.5rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;}
.footer-copy{font-size:.8rem;}
.social-links{display:flex;gap:.75rem;}
.social-links a{width:32px;height:32px;border-radius:50%;background:rgba(255,255,255,.1);display:flex;align-items:center;justify-content:center;font-size:.75rem;color:rgba(255,255,255,.7);text-decoration:none;transition:background .2s;}
.social-links a:hover{background:var(--blue);}
/* TRACKER */
.tracker-hero{padding:8rem 4rem 6rem;background:linear-gradient(135deg,var(--blue) 0%,var(--violet) 100%);position:relative;overflow:hidden;}
.tracker-hero::after{content:'';position:absolute;bottom:-2px;left:0;right:0;height:80px;background:var(--off);clip-path:polygon(0 60%,100% 0,100% 100%,0 100%);}
.tracker-hero h1{font-family:'Nunito',sans-serif;font-size:clamp(2rem,5vw,3rem);font-weight:900;color:var(--white);margin-bottom:.75rem;}
.tracker-hero p{color:rgba(255,255,255,.8);font-size:1rem;max-width:480px;line-height:1.75;}
.tracker-body{padding:4rem;background:var(--off);min-height:50vh;}
.tracker-form-card{background:var(--white);border-radius:16px;padding:2.5rem;box-shadow:var(--card-sh);max-width:600px;margin:0 auto;}
.tf-label{display:block;font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:.6rem;}
.tf-input{width:100%;padding:.85rem 1.1rem;border:2px solid var(--border);border-radius:6px;font-size:.9rem;font-family:'Nunito Sans',sans-serif;transition:border-color .25s;color:var(--text);margin-bottom:1rem;}
.tf-input:focus{outline:none;border-color:var(--blue);}
.tf-input::placeholder{color:#b0b8c8;}
.tf-btn{background:var(--blue);color:var(--white);border:none;padding:.85rem 2rem;border-radius:6px;font-weight:800;font-size:.9rem;cursor:pointer;transition:background .2s,transform .2s;font-family:'Nunito Sans',sans-serif;width:100%;}
.tf-btn:hover{background:var(--blue-dark);transform:translateY(-1px);}
.tf-btn:disabled{opacity:.6;cursor:not-allowed;transform:none;}
.result-card{background:var(--white);border-radius:14px;padding:2rem;margin-top:1.5rem;box-shadow:var(--card-sh);max-width:600px;margin-left:auto;margin-right:auto;}
.result-title{font-family:'Nunito',sans-serif;font-size:1.1rem;font-weight:800;color:var(--text);}
.result-meta{color:var(--muted);font-size:.82rem;margin-top:.25rem;}
.result-header{display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:.75rem;margin-bottom:1.25rem;}
.status-pill{display:inline-flex;padding:.3rem .9rem;border-radius:999px;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;}
.status-pending{background:#fff9e6;color:#b7791f;}
.status-reviewed{background:#ebf4ff;color:#2b6cb0;}
.status-shortlisted{background:#f0fff4;color:#276749;}
.status-rejected{background:#fff5f5;color:#c53030;}
.status-interview-passed{background:#e6fffa;color:#0f766e;}
.status-interview-failed{background:#fff1f2;color:#be123c;}
.status-hiring-approved{background:#ecfeff;color:#155e75;}
.status-offer-accepted{background:#ecfdf5;color:#166534;}
.status-offer-rejected{background:#fff1f2;color:#991b1b;}
.status-hired{background:#f3e8ff;color:#7e22ce;}
.score-section{margin-bottom:1.25rem;}
.score-label{font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:.5rem;}
.score-row{display:flex;align-items:center;gap:1rem;}
.score-bar-outer{height:6px;background:var(--border);border-radius:3px;overflow:hidden;flex:1;max-width:180px;}
.score-bar-inner{height:100%;background:linear-gradient(90deg,var(--blue),#7048e8);border-radius:3px;transition:width 1.2s ease;}
.score-val{font-size:.82rem;font-weight:700;color:var(--blue);}
.tl{position:relative;padding-left:1.4rem;margin-top:1.25rem;}
.tl::before{content:'';position:absolute;left:0;top:6px;bottom:6px;width:2px;background:var(--border);}
.tl-ev{position:relative;margin-bottom:.9rem;}
.tl-ev::before{content:'';position:absolute;left:-1.4rem;top:6px;width:8px;height:8px;border-radius:50%;background:var(--blue);border:2px solid var(--white);}
.tl-ev-title{font-size:.875rem;font-weight:700;color:var(--text);}
.tl-ev-date{font-size:.76rem;color:var(--muted);margin-top:.15rem;}
.offer-banner{background:#f0fff4;border:1px solid #9ae6b4;border-radius:10px;padding:1.25rem 1.5rem;margin-bottom:1.5rem;}
.offer-banner-title{font-family:'Nunito',sans-serif;font-size:1rem;font-weight:800;color:#276749;margin-bottom:.5rem;}
.offer-banner p{font-size:.875rem;color:#2f855a;line-height:1.7;}
.err-box{background:#fff9e6;border:1px solid #f6e05e;border-radius:10px;padding:1.25rem 1.5rem;margin-top:1.5rem;max-width:600px;margin-left:auto;margin-right:auto;}
.err-box h4{font-family:'Nunito',sans-serif;font-size:.92rem;font-weight:800;color:#744210;margin-bottom:.75rem;}
.err-box p{font-size:.82rem;color:#744210;line-height:1.7;margin-bottom:.4rem;}
.err-box code{background:#fef3c7;padding:.15rem .4rem;border-radius:3px;font-family:monospace;font-size:.78rem;}
@media(max-width:1000px){
  nav{padding:.9rem 1.5rem;}
  .nav-links-list{display:none;}
  .hero,.services-section,.about-section,.why-section,.jobs-section,.testi-section,.bottom-section,.tracker-hero,.tracker-body,.site-footer{padding-left:1.5rem;padding-right:1.5rem;}
  .hero-images{display:none;}
  .hero-left-image{display:none;}
  .services-intro,.about-grid,.testi-grid,.bottom-grid,.footer-grid{grid-template-columns:1fr;}
  .why-grid,.cards-grid{grid-template-columns:1fr;}
}
</style>"""

_NAV = """<nav>
  <a href="/" class="nav-logo"><span class="nav-logo-dot"></span> TalentFlow</a>
  <ul class="nav-links-list">
    <li><a href="/">Home</a></li>
    <li><a href="/#services">Service</a></li>
    <li><a href="/#about">About</a></li>
    <li><a href="/jobs">Jobs</a></li>
    <li><a href="/#contact">Contact</a></li>
  </ul>
  <a href="http://localhost:8003" class="nav-signin">Sign In</a>
  
</nav>"""

_FOOTER = """<div class="site-footer">
  <div class="footer-grid">
    <div class="footer-col">
      <a href="/" class="footer-brand-logo"><span style="color:var(--red);">&#9679;</span> TalentFlow</a>
      <p class="footer-brand-desc">The ServiceNow recruitment agency built exclusively for the ServiceNow community.</p>
    </div>
    <div class="footer-col"><h4>Company</h4><ul><li><a href="/#about">About Us</a></li><li><a href="/jobs">Careers</a></li><li><a href="/#contact">Contact</a></li></ul></div>
    <div class="footer-col"><h4>Services</h4><ul><li><a href="/#services">Permanent</a></li><li><a href="/#services">Contract</a></li><li><a href="/#services">Projects</a></li></ul></div>
    <div class="footer-col"><h4>Portal</h4><ul><li><a href="/jobs">Browse Jobs</a></li><li><a href="/track-application">Track App</a></li><li><a href="http://localhost:8003">HR Login</a></li></ul></div>
    <div class="footer-col footer-addr"><h4>Contact</h4>Kicukiro, Kigali, Rwanda<br><br><a href="tel:+250784466887">+250 7844 66887</a><br><a href="mailto:angel@talentflow.tech">angel@talentflow.tech</a></div>
  </div>
  <div class="footer-bottom">
    <div class="footer-copy">Copyright &copy; 2026 Talent Flow Recruitment &mdash; All Rights Reserved.</div>
    <div class="social-links"><a href="#">in</a><a href="#">tw</a><a href="#">fb</a></div>
  </div>
</div>
<script>
  var obs = new IntersectionObserver(function(entries){
    entries.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add('visible'); obs.unobserve(e.target); } });
  },{threshold:.12});
  document.querySelectorAll('.reveal').forEach(function(el){ obs.observe(el); });
</script>"""

# ─────────────────────────────────────────────────────────────────────────────
#  LANDING PAGE
# ─────────────────────────────────────────────────────────────────────────────
modern_landing_template = (
    """<!DOCTYPE html><html lang="en"><head>"""
    + _BASE_HEAD
    + """<title>TalentFlow &mdash; ServiceNow Recruitment Experts</title></head><body>
<div class="page-loader"><div class="loader-logo">TalentFlow</div><div class="loader-spin"></div></div>"""
+ _NAV
+ """
<section class="hero" id="home">
  <div class="hero-blob hero-blob-1"></div>
  <div class="hero-blob hero-blob-2"></div>
  <div class="hero-content" style="display:flex;flex-direction:row;align-items:center;justify-content:space-between;">
    <div class="hero-text" style="text-align:left;width:40%;margin-right:2rem;">
      <h1>TalentFlow lets your<br>career so easy.</h1>
      <p class="hero-sub">Talent Flow is a ServiceNow recruitment agency, created to look after the needs of the ServiceNow community. Permanent, contract, and project roles.</p>
      <a href="/jobs" class="hero-btn">Browse Available Jobs &rarr;</a>
    </div>
    <div class="hero-images">
      <div class="hero-main-image">
        <img src="/templates/a.jpeg" alt="TalentFlow Team" class="hero-img-large hero-img-main">
      </div>
      <div class="hero-side-images">
        <img src="/templates/c.jpeg" alt="Professional Team" class="hero-img-large hero-img-side">
        <img src="/templates/b.jpeg" alt="Recruitment Process" class="hero-img-large hero-img-side">
      </div>
    </div>
  </div>
</section>

<section class="services-section" id="services">
  <div class="services-intro">
    <div class="reveal">
      <span class="eyebrow">Our Services</span>
      <h2 class="section-title">Our Core <span>Featured</span> Service</h2>
<p style="color:var(--muted);font-size:.97rem;line-height:1.8;">Here at ZIBITECH, We specialise exclusively in the ServiceNow ecosystem — hiring the right people with differnt skills, and 
experience with the right roles, every time.<br><br>
Unlike standard automation tools, TalentFlow utilizes 
“Agentic AI” (intelligent automation) to perform tasks autonomously, without constant oversight. 
A recruiter can activate an AI agent that handles resume scorer — from candidate filtering to hiring.</p></div>
    <div class="cards-grid">
      <div class="svc-card reveal reveal-d1"><div class="svc-icon">&#128084;</div><h3>Permanent Recruitment</h3><p>Shortlist of prequalified, certified ServiceNow Specialists for your permanent positions.</p></div>
      <div class="svc-card reveal reveal-d2"><div class="svc-icon">&#9889;</div><h3>Contract Recruitment</h3><p>Certified ServiceNow Specialists available within 48hrs for your urgent contract needs.</p></div>
      <div class="svc-card reveal reveal-d3"><div class="svc-icon">&#128274;</div><h3>Project Privacy</h3><p>Complete discretion and confidentiality throughout every placement process.</p></div>
      <div class="svc-card reveal reveal-d4"><div class="svc-icon">&#128640;</div><h3>Project Delivery</h3><p>Outsource your ServiceNow project to our team of experienced professionals.</p></div>
    </div>
  </div>
</section>

<div class="diag-divider"></div>
<section class="about-section" id="about">
  <div class="about-grid">
    <div class="reveal"><img src="/templates/d.jpeg" alt="About TalentFlow" class="about-image"></div>
    <div class="reveal reveal-d1">
      <span class="eyebrow">Who We Are</span>
     <h2 class="section-title">We are the Best Online<br><span>Recruitment Firm</span> in the world</h2>
   <div class="about-content">
  <p>With over 10 years in Technology Recruitment and the last 5 years specifically devoted to the ServiceNow ecosystem, we bring unmatched specialist expertise, precision, and dedicated focus to every hire.</p>
  <p>We are not generalist recruiters — we deeply understand certifications, modules, release cycles, workflows, and what makes a ServiceNow professional truly exceptional, high-performing, and culture-fit.</p>
   </div>
<div class="about-actions"><a href="/#contact" class="about-btn">Contact Us for more information</a></div>
    </div>
  </div>
</section>

<div class="diag-divider-rev"></div>
<section class="why-section">
  <div style="text-align:center;" class="reveal">
    <span class="eyebrow">Why Choose Us</span>
    <h2 class="section-title">Why we are the <span>Best?</span></h2>
    <p style="color:var(--muted);max-width:500px;margin:.75rem auto 0;font-size:.95rem;line-height:1.75;">We are not measured by how many hours we work, but by the quality of talent we place.</p>
  </div>
  <div class="why-grid">
    <div class="why-card reveal reveal-d1"><div class="why-icon">&#9654;&#65039;</div><div><h4>Optimized for Speed &amp; Quality</h4><p>Contractors available within 48 hours. Permanent placements with a curated shortlist, delivered fast.</p></div></div>
    <div class="why-card reveal reveal-d2"><div class="why-icon">&#128273;</div><div><h4>Flexible Usability</h4><p>Whether permanent, contract or project &mdash; we adapt to your exact hiring model and timeline.</p></div></div>
    <div class="why-card reveal reveal-d3"><div class="why-icon">&#128101;</div><div><h4>24/7 Hours Support</h4><p>Angel and the team are always available. Your recruitment never stops because your business never stops.</p></div></div>
    <div class="why-card reveal reveal-d4"><div class="why-icon">&#127760;</div><div><h4>Worldwide Coverage</h4><p>Active across the UK, Europe, Africa and beyond &mdash; wherever ServiceNow talent is needed.</p></div></div>
  </div>
</section>

<section class="jobs-section" id="jobs">
  <div class="jobs-header reveal">
    <span class="eyebrow">Open Positions</span>
    <h2 class="section-title">&#127775; Featured <span>Opportunities</span></h2>
    <p>Currently recruiting active vacancies with both partners and end user organisations across all ServiceNow specialisms.</p>
  </div>
  <div class="filter-bar reveal">
    <button class="filter-btn active" onclick="filterJobs('all',this)">All Roles</button>
    
  </div>
  <div class="jobs-grid" id="jobsGrid">
    {% for job in jobs[:6] %}
    <div class="job-card" data-dept="{{ job.department }}" data-type="{{ job.job_type if job.job_type else '' }}">
      <div class="job-card-top">
        <span class="dept-tag">{{ job.department }}</span>
        <span class="type-tag">{{ job.job_type if job.job_type else 'Open' }}</span>
      </div>
      <div class="job-name">{{ job.title }}</div>
      <div class="job-blurb">{{ job.description[:110] }}{% if job.description|length > 110 %}...{% endif %}</div>
      <div class="job-foot">
        <span class="job-sal">{{ job.salary if job.salary else 'Competitive' }}</span>
        <a href="/jobs/{{ job.id }}" class="job-cta">View Details &rarr;</a>
      </div>
    </div>
    {% else %}
    <div style="grid-column:1/-1;text-align:center;padding:3rem;color:var(--muted);">
      <div style="font-family:'Nunito',sans-serif;font-size:1.2rem;font-weight:800;margin-bottom:.5rem;">No open roles right now</div>
      <div>Check back soon or <a href="#contact" style="color:var(--blue);">get in touch</a>.</div>
    </div>
    {% endfor %}
  </div>
</section>

<section class="testi-section">
  <div class="testi-grid">
    <div class="reveal">
      <div class="avatar-cluster">
        <div class="av av-1"><img src="/templates/a.jpeg" alt="Client 1" style="width:100%;height:100%;object-fit:cover;border-radius:50%;"></div>
        <div class="av av-2 active-av"><img src="/templates/b.jpeg" alt="Client 2" style="width:100%;height:100%;object-fit:cover;border-radius:50%;"></div>
        <div class="av av-3"><img src="/templates/c.jpeg" alt="Client 3" style="width:100%;height:100%;object-fit:cover;border-radius:50%;"></div>
        <div class="av av-4"><img src="/templates/d.jpeg" alt="Client 4" style="width:100%;height:100%;object-fit:cover;border-radius:50%;"></div>
        <div class="av av-5"><img src="/templates/a.jpeg" alt="Client 5" style="width:100%;height:100%;object-fit:cover;border-radius:50%;"></div>
        <div class="av av-6"><img src="/templates/b.jpeg" alt="Client 6" style="width:100%;height:100%;object-fit:cover;border-radius:50%;"></div>
      </div>
    </div>
    <div class="testi-content reveal reveal-d1">
      <span class="eyebrow">Client Feedback</span>
      <h2 class="section-title">Great stories from our <span>Clients</span></h2>
      <blockquote>&ldquo;I used TalentFlow to apply for my current position within 72 hours, i get to have my interview. The quality of candidates was exceptional and Angel truly understood our technical requirements.&rdquo;</blockquote>
      <div class="testi-author">Stiven N. <span>&mdash; ZIBITECH Data Analyst Ltd</span></div>
      <a href="/#jobs" class="read-more-btn">Browse Jobs &rarr;</a>
    </div>
  </div>
</section>

<div class="bottom-section" id="contact">
  <div class="bottom-grid">
    <div class="newsletter reveal">
      <h3>Your thoughts, feedback<br>and opinions Matters the most</h3>
      <p>they truly count and shape what we do.<br>
      Keep informed Stay,tuned with the newest, most up-to-date ServiceNow openings <br>
      positions, industry trends / market intelligence, and hiring advice / candidate tips from Angel.

      We would love to hear from you. Feel free to share a supportive note comment for the team —
      <br>your positive words make a difference.
      </p>
     
    </div>
    <div class="reveal reveal-d1">
      <div class="contact-card">
        <h3>Send us a Message</h3>
        <input type="email" class="cf-input" placeholder="Your email*">
        <input type="text" class="cf-input" placeholder="Subject*">
        <textarea class="cf-input cf-textarea" placeholder="Message"></textarea>
        <button class="cf-btn" onclick="this.textContent='Message Sent! \u2713'">Send Message</button>
      </div>
    </div>
  </div>
</div>
"""
    + _FOOTER
    + """
<script>
function filterJobs(term, btn) {
  document.querySelectorAll('.filter-btn').forEach(function(b){ b.classList.remove('active'); });
  btn.classList.add('active');
  document.querySelectorAll('#jobsGrid .job-card').forEach(function(card){
    var dept = card.dataset.dept || '';
    var type = card.dataset.type || '';
    var show = term === 'all' || dept.toLowerCase().indexOf(term.toLowerCase()) > -1 || type.toLowerCase().indexOf(term.toLowerCase()) > -1;
    card.style.display = show ? '' : 'none';
  });
}
</script>
</body></html>"""
)


# ─────────────────────────────────────────────────────────────────────────────
#  TRACKER PAGE  — built as a plain function, zero string concatenation
#  trackApps() is a plain global function — NOT inside any IIFE
# ─────────────────────────────────────────────────────────────────────────────
def build_tracker_page():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Nunito+Sans:wght@300;400;600&display=swap" rel="stylesheet">
<title>Track Your Application &mdash; TalentFlow</title>
<style>
:root{--blue:#3b5bdb;--blue-dark:#2846c4;--blue-light:#5c7cfa;--violet:#7048e8;--red:#fa5252;--white:#ffffff;--off:#f8f9fc;--text:#2d3748;--muted:#718096;--border:#e8edf5;--card-sh:0 8px 40px rgba(59,91,219,.10);}
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{font-family:'Nunito Sans',sans-serif;background:var(--white);color:var(--text);}
@keyframes slideDown{from{opacity:0;transform:translateY(-16px)}to{opacity:1;transform:translateY(0)}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes loaderOut{to{opacity:0;pointer-events:none}}
.page-loader{position:fixed;inset:0;background:var(--white);z-index:9999;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:1rem;animation:loaderOut .3s 1s ease both;}
.loader-logo{font-family:'Nunito',sans-serif;font-size:1.6rem;font-weight:900;color:var(--blue);}
.loader-spin{width:28px;height:28px;border:3px solid var(--border);border-top-color:var(--blue);border-radius:50%;animation:spin .7s linear infinite;}
nav{position:fixed;top:0;left:0;right:0;z-index:200;display:flex;align-items:center;justify-content:space-between;padding:.9rem 4rem;background:rgba(255,255,255,.96);backdrop-filter:blur(16px);box-shadow:0 2px 20px rgba(59,91,219,.08);animation:slideDown .5s ease both;}
.nav-logo{font-family:'Nunito',sans-serif;font-size:1.3rem;font-weight:900;color:var(--blue);text-decoration:none;display:flex;align-items:center;gap:.5rem;}
.nav-logo-dot{width:8px;height:8px;border-radius:50%;background:var(--red);display:inline-block;}
.nav-links-list{display:flex;align-items:center;gap:2.5rem;list-style:none;}
.nav-links-list a{color:var(--text);text-decoration:none;font-size:.88rem;font-weight:600;transition:color .2s;}
.nav-links-list a:hover{color:var(--blue);}
.nav-signin{background:var(--red);color:var(--white);padding:.55rem 1.5rem;border-radius:4px;font-weight:700;font-size:.88rem;text-decoration:none;}
.tracker-hero{padding:8rem 4rem 6rem;background:linear-gradient(135deg,#3b5bdb 0%,#7048e8 100%);position:relative;overflow:hidden;}
.tracker-hero::after{content:'';position:absolute;bottom:-2px;left:0;right:0;height:80px;background:var(--off);clip-path:polygon(0 60%,100% 0,100% 100%,0 100%);}
.tracker-hero h1{font-family:'Nunito',sans-serif;font-size:clamp(2rem,5vw,3rem);font-weight:900;color:#fff;margin-bottom:.75rem;}
.tracker-hero p{color:rgba(255,255,255,.8);font-size:1rem;max-width:480px;line-height:1.75;}
.tracker-body{padding:4rem;background:var(--off);min-height:50vh;}
.tracker-form-card{background:var(--white);border-radius:16px;padding:2.5rem;box-shadow:var(--card-sh);max-width:600px;margin:0 auto;}
.tf-label{display:block;font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:.6rem;}
.tf-input{width:100%;padding:.85rem 1.1rem;border:2px solid var(--border);border-radius:6px;font-size:.9rem;font-family:'Nunito Sans',sans-serif;transition:border-color .25s;color:var(--text);margin-bottom:1rem;display:block;}
.tf-input:focus{outline:none;border-color:#3b5bdb;}
.tf-input::placeholder{color:#b0b8c8;}
.tf-btn{background:#3b5bdb;color:#fff;border:none;padding:.85rem 2rem;border-radius:6px;font-weight:800;font-size:.9rem;cursor:pointer;font-family:'Nunito Sans',sans-serif;width:100%;transition:background .2s,transform .2s;}
.tf-btn:hover{background:#2846c4;transform:translateY(-1px);}
.tf-btn:disabled{opacity:.6;cursor:not-allowed;transform:none;}
.results-wrap{max-width:600px;margin:0 auto;padding-top:.5rem;}
.result-card{background:var(--white);border-radius:14px;padding:2rem;margin-top:1.5rem;box-shadow:var(--card-sh);}
.result-header{display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:.75rem;margin-bottom:1.25rem;}
.result-title{font-family:'Nunito',sans-serif;font-size:1.1rem;font-weight:800;color:var(--text);}
.result-meta{color:var(--muted);font-size:.82rem;margin-top:.25rem;}
.status-pill{display:inline-flex;padding:.3rem .9rem;border-radius:999px;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;}
.status-pending{background:#fff9e6;color:#b7791f;}
.status-reviewed{background:#ebf4ff;color:#2b6cb0;}
.status-shortlisted{background:#f0fff4;color:#276749;}
.status-rejected{background:#fff5f5;color:#c53030;}
.status-interview-passed{background:#e6fffa;color:#0f766e;}
.status-interview-failed{background:#fff1f2;color:#be123c;}
.status-hiring-approved{background:#ecfeff;color:#155e75;}
.status-offer-accepted{background:#ecfdf5;color:#166534;}
.status-offer-rejected{background:#fff1f2;color:#991b1b;}
.status-hired{background:#f3e8ff;color:#7e22ce;}
.score-section{margin-bottom:1.25rem;}
.score-label{font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:.5rem;}
.score-row{display:flex;align-items:center;gap:1rem;}
.score-bar-outer{height:6px;background:var(--border);border-radius:3px;overflow:hidden;flex:1;max-width:180px;}
.score-bar-inner{height:100%;background:linear-gradient(90deg,#3b5bdb,#7048e8);border-radius:3px;transition:width 1.2s ease;}
.score-val{font-size:.82rem;font-weight:700;color:#3b5bdb;}
.tl{position:relative;padding-left:1.4rem;margin-top:1.25rem;}
.tl::before{content:'';position:absolute;left:0;top:6px;bottom:6px;width:2px;background:var(--border);}
.tl-ev{position:relative;margin-bottom:.9rem;}
.tl-ev::before{content:'';position:absolute;left:-1.4rem;top:6px;width:8px;height:8px;border-radius:50%;background:#3b5bdb;border:2px solid #fff;}
.tl-ev-title{font-size:.875rem;font-weight:700;color:var(--text);}
.tl-ev-date{font-size:.76rem;color:var(--muted);margin-top:.15rem;}
.offer-banner{background:#f0fff4;border:1px solid #9ae6b4;border-radius:10px;padding:1.25rem 1.5rem;margin-bottom:1.5rem;}
.offer-banner-title{font-family:'Nunito',sans-serif;font-size:1rem;font-weight:800;color:#276749;margin-bottom:.5rem;}
.offer-banner p{font-size:.875rem;color:#2f855a;line-height:1.7;}
.err-box{background:#fff9e6;border:1px solid #f6e05e;border-radius:10px;padding:1.25rem 1.5rem;margin-top:1.5rem;}
.err-box h4{font-size:.92rem;font-weight:800;color:#744210;margin-bottom:.5rem;}
.err-box p{font-size:.82rem;color:#744210;line-height:1.7;}
.err-box code{background:#fef3c7;padding:.1rem .35rem;border-radius:3px;font-family:monospace;}
.site-footer{background:#1a1f36;padding:2.5rem 4rem;color:rgba(255,255,255,.65);margin-top:0;}
.footer-bottom{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;}
.footer-copy{font-size:.8rem;}
@media(max-width:768px){nav{padding:.9rem 1.5rem;}.nav-links-list{display:none;}.tracker-hero,.tracker-body{padding-left:1.5rem;padding-right:1.5rem;}}
</style>
</head>
<body>

<div class="page-loader"><div class="loader-logo">TalentFlow</div><div class="loader-spin"></div></div>

<nav>
  <a href="/" class="nav-logo"><span class="nav-logo-dot"></span> TalentFlow</a>
  <ul class="nav-links-list">
    <li><a href="/">Home</a></li>
    <li><a href="/#services">Service</a></li>
    <li><a href="/#about">About</a></li>
    <li><a href="/jobs">Jobs</a></li>
    <li><a href="/ai-dashboard">AI Dashboard</a></li>
    <li><a href="/#contact">Contact</a></li>
  </ul>
  <a href="http://localhost:8003" class="nav-signin">Sign In</a>
</nav>

<div class="tracker-hero">
  <a href="/" style="display:inline-flex;align-items:center;gap:.5rem;color:rgba(255,255,255,.75);text-decoration:none;font-size:.85rem;font-weight:600;margin-bottom:1.5rem;">&larr; Home</a>
  <h1>Track your Application</h1>
  <p>Enter the email address you used to apply and we'll show you exactly where you stand.</p>
</div>

<div class="tracker-body">
  <div class="tracker-form-card">
    <label class="tf-label" for="trackEmail">Your Email Address</label>
    <input type="email" id="trackEmail" class="tf-input" placeholder="your.email@example.com">
    <button id="trackBtn" class="tf-btn">Track Applications &rarr;</button>
  </div>
  <div class="results-wrap" id="trackerResults"></div>
</div>

<div class="site-footer">
  <div class="footer-bottom">
    <div class="footer-copy">Copyright &copy; 2026 Talent Flow Recruitment &mdash; All Rights Reserved.</div>
    <a href="/" style="color:rgba(255,255,255,.6);text-decoration:none;font-size:.85rem;">&larr; Back to Home</a>
  </div>
</div>

<script>
// trackApps is a plain global function — no IIFE, no wrapper
function trackApps() {
  var emailInput = document.getElementById('trackEmail');
  var btn        = document.getElementById('trackBtn');
  var el         = document.getElementById('trackerResults');
  var email      = emailInput.value.trim();

  if (!email) {
    emailInput.style.borderColor = '#fa5252';
    emailInput.focus();
    return;
  }
  emailInput.style.borderColor = '#e8edf5';

  btn.disabled    = true;
  btn.textContent = 'Searching...';
  el.innerHTML    = '<div style="text-align:center;padding:3rem;color:#718096;">Looking up your applications...</div>';

  fetch('/applications-by-email?email=' + encodeURIComponent(email))
    .then(function(res) {
      if (!res.ok) {
        return res.text().then(function(t) {
          try {
            var parsed = JSON.parse(t || '{}');
            throw new Error(parsed.error || ('Server error ' + res.status));
          } catch (_) {
            throw new Error('Server error ' + res.status + ': ' + (t || '').slice(0,200));
          }
        });
      }
      return res.json();
    })
    .then(function(data) {
      btn.disabled    = false;
      btn.textContent = 'Track Applications \u2192';

      if (data && !Array.isArray(data) && data.error) {
        throw new Error('DB error: ' + data.error);
      }
      if (!Array.isArray(data)) {
        throw new Error('Unexpected response: ' + JSON.stringify(data).slice(0,120));
      }
      if (data.length === 0) {
        el.innerHTML = '<div class="result-card" style="text-align:center;padding:2.5rem;">'
          + '<div style="font-size:2.5rem;margin-bottom:1rem;">&#128269;</div>'
          + '<div style="font-family:Nunito,sans-serif;font-size:1.1rem;font-weight:800;margin-bottom:.5rem;">No applications found</div>'
          + '<div style="color:#718096;font-size:.9rem;">No applications found for <strong>' + email + '</strong>.<br>Make sure you use the same email you applied with.</div>'
          + '</div>';
        return;
      }

      el.innerHTML = data.map(function(app) {
        var status = ((app.status || 'pending') + '').toLowerCase();

        var offerStatus = ((app.offer_status || '') + '').toLowerCase();
        var offerBanner = '';
        if (offerStatus === 'sent') {
          offerBanner = '<div class="offer-banner">'
            + '<div class="offer-banner-title">&#127881; Congratulations &mdash; You have an offer!</div>'
            + '<p><strong>Position:</strong> ' + (app.offer_position || app.job_title || 'N/A')
            + ' | <strong>Salary:</strong> ' + (app.offer_salary || 'TBD')
            + ' | <strong>Start:</strong> ' + (app.offer_start_date || 'TBD') + '</p>'
            + '</div>';
        } else if (offerStatus === 'accepted') {
          offerBanner = '<div class="offer-banner">'
            + '<div class="offer-banner-title">&#9989; Offer accepted successfully</div>'
            + '<p>Your offer response was received. HR will now complete final hiring steps.</p>'
            + '</div>';
        } else if (offerStatus === 'rejected') {
          offerBanner = '<div class="offer-banner" style="background:#fff5f5;border-color:#fecaca;">'
            + '<div class="offer-banner-title" style="color:#b91c1c;">Offer declined</div>'
            + '<p style="color:#991b1b;">You have declined this offer. Contact HR if this was a mistake.</p>'
            + '</div>';
        }

        var scoreHtml = '';
        if (app.resume_score) {
          var pct = Math.min(parseFloat(app.resume_score) || 0, 100);
          scoreHtml = '<div class="score-section">'
            + '<div class="score-label">Resume Score</div>'
            + '<div class="score-row">'
            + '<div class="score-bar-outer"><div class="score-bar-inner" style="width:' + pct + '%"></div></div>'
            + '<span class="score-val">' + pct.toFixed(1) + '/100</span>'
            + '</div></div>';
        }

        function fmt(d) {
          try { return new Date(d).toLocaleDateString('en-GB', {day:'numeric',month:'long',year:'numeric'}); }
          catch(e) { return d || ''; }
        }
        function fmtShort(d) {
          try { return new Date(d).toLocaleDateString('en-GB', {day:'numeric',month:'long'}); }
          catch(e) { return d || ''; }
        }

        var tl = '<div class="tl-ev"><div class="tl-ev-title">Application submitted</div>'
          + '<div class="tl-ev-date">' + (app.application_date ? fmt(app.application_date) : 'Unknown') + '</div></div>';

        if (app.resume_score) {
          tl += '<div class="tl-ev"><div class="tl-ev-title">Resume reviewed &amp; scored</div>'
            + '<div class="tl-ev-date">' + parseFloat(app.resume_score).toFixed(1) + ' / 100</div></div>';
        }
        if (app.interview_status) {
          tl += '<div class="tl-ev"><div class="tl-ev-title">Interview scheduled &mdash; ' + app.interview_status + '</div>'
            + '<div class="tl-ev-date">' + (app.scheduled_date ? fmtShort(app.scheduled_date) : '') + ' ' + (app.scheduled_time || '') + '</div></div>';
        }
        if (status === 'interview_failed') {
          tl += '<div class="tl-ev"><div class="tl-ev-title" style="color:#b91c1c;">Interview result: Not selected</div>'
            + '<div class="tl-ev-date">Thank you for your time and effort during the interview process.</div></div>';
        }
        if (app.overall_score) {
          tl += '<div class="tl-ev"><div class="tl-ev-title">Evaluation completed</div>'
            + '<div class="tl-ev-date">Score: ' + app.overall_score + '/10</div></div>';
        }
        if (app.offer_status) {
          tl += '<div class="tl-ev"><div class="tl-ev-title" style="color:#276749;">&#127881; Offer ' + app.offer_status + '</div>'
            + '<div class="tl-ev-date">' + (app.offer_salary || '') + ' | Starts ' + (app.offer_start_date || 'TBD') + '</div></div>';
        }

        var appliedStr = app.application_date ? 'Applied ' + new Date(app.application_date).toLocaleDateString('en-GB') : '';

        var actions = '';
        if (offerStatus === 'sent' && app.offer_id) {
          actions = '<div style="margin-top:1.5rem;display:flex;gap:1rem;">'
            + '<button onclick="respondToOffer(' + app.id + ', ' + app.offer_id + ', \\'accepted\\')" class="tf-btn" style="background:#276749;">Accept Offer</button>'
            + '<button onclick="respondToOffer(' + app.id + ', ' + app.offer_id + ', \\'rejected\\')" class="tf-btn" style="background:#fa5252;">Reject Offer</button>'
            + '</div>';
        }

        return '<div class="result-card">'
          + offerBanner
          + '<div class="result-header"><div>'
          + '<div class="result-title">' + (app.job_title || 'Application') + '</div>'
          + '<div class="result-meta">' + (app.department || '') + (app.department && appliedStr ? ' &middot; ' : '') + appliedStr + '</div>'
          + '</div><span class="status-pill status-' + status.replace(/_/g, '-') + '">' + status.replace(/_/g, ' ') + '</span></div>'
          + scoreHtml
          + '<div class="tl">' + tl + '</div>'
          + actions
          + '</div>';
      }).join('');
    })
    .catch(function(err) {
      btn.disabled    = false;
      btn.textContent = 'Track Applications \u2192';
      el.innerHTML = '<div class="err-box">'
        + '<h4>&#9888; Something went wrong</h4>'
        + '<p><strong>Error:</strong> ' + err.message + '</p>'
        + '<p style="margin-top:.5rem;">Open this URL in your browser to see the raw data:</p>'
        + '<p><code>/applications-by-email?email=' + encodeURIComponent(email) + '</code></p>'
        + '</div>';
    });
}

function respondToOffer(appId, offerId, response) {
  if (!confirm('Are you sure you want to ' + response + ' this offer?')) return;
  
  fetch('/api/respond-to-offer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ application_id: appId, offer_id: offerId, response: response })
  })
  .then(function(res) { return res.json(); })
  .then(function(data) {
    if (data.success) {
      alert('Your response has been recorded.');
      trackApps();
    } else {
      alert('Error: ' + data.error);
    }
  });
}

// Wire up button and Enter key after DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  var btn = document.getElementById('trackBtn');
  var inp = document.getElementById('trackEmail');
  if (btn) btn.addEventListener('click', trackApps);
  if (inp) inp.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') { e.preventDefault(); trackApps(); }
  });
});
</script>

</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def modern_landing_page(request: Request):
    jobs = db.get_all_jobs()
    from jinja2 import Template
    html = Template(modern_landing_template).render(jobs=jobs)
    return HTMLResponse(content=html)


@app.get("/jobs", response_class=HTMLResponse)
async def jobs_list(request: Request):
    jobs = db.get_all_jobs()
    from job_portal import job_portal_template
    from jinja2 import Template
    html = Template(job_portal_template).render(jobs=jobs, job=None)
    return HTMLResponse(content=html)


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
async def job_details(request: Request, job_id: int):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    from job_portal import job_portal_template
    from jinja2 import Template
    html = Template(job_portal_template).render(job=job, jobs=[])
    return HTMLResponse(content=html)


@app.get("/track-application", response_class=HTMLResponse)
async def track_application(request: Request):
    # Build fresh each time — no string concatenation, no template engine
    return HTMLResponse(content=build_tracker_page())


@app.get("/hr-login")
async def hr_login_redirect():
    return RedirectResponse(url="http://localhost:8003", status_code=302)

@app.get("/applications-by-email")
async def get_applications_by_email(email: str):
    try:
        applications = db.get_applications_by_email(email)
        statuses = {(a.get("status") or "").lower() for a in applications if isinstance(a, dict)}
        offer_statuses = {(a.get("offer_status") or "").lower() for a in applications if isinstance(a, dict)}
        if (
            "offer_accepted" in statuses
            or "offer_rejected" in statuses
            or "hired" in statuses
            or "accepted" in offer_statuses
            or "rejected" in offer_statuses
            or "hired" in offer_statuses
        ):
            return JSONResponse(
                content={
                    "error": "Tracking is closed because you already responded to the offer."
                },
                status_code=403
            )
        result = []
        for app in applications:
            if isinstance(app, dict):
                result.append(app)
            elif hasattr(app, '__dict__'):
                result.append({k: v for k, v in app.__dict__.items() if not k.startswith('_')})
            else:
                result.append(dict(app))
        return JSONResponse(content=result)
    except Exception as e:
        import traceback
        return JSONResponse(
            content={"error": str(e), "traceback": traceback.format_exc()},
            status_code=500
        )


@app.post("/api/ai-screen")
async def ai_screen_candidate(request: Request):
    """AI-powered candidate screening based on job requirements"""
    try:
        data = await request.json()
        resume_data = data.get('resume_data', {})
        job_requirements = data.get('job_requirements', {})
        
        # Perform AI screening
        screening_result = ai_agent.screen_candidate(resume_data, job_requirements)
        
        return JSONResponse(content={
            'success': True,
            'screening_result': screening_result
        })
        
    except Exception as e:
        return JSONResponse(content={
            'success': False,
            'error': str(e)
        }, status_code=500)

@app.post("/api/accept-for-assessment")
async def accept_for_assessment(request: Request):
    try:
        data = await request.json()
        application_id = int(data.get("application_id", 0))
        if not application_id:
            return JSONResponse(content={"success": False, "error": "Missing application_id"}, status_code=400)
        conn = __import__('sqlite3').connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE job_applications SET status = 'accepted_for_assessment' WHERE id = ?", (application_id,))
        conn.commit(); conn.close()
        return JSONResponse(content={"success": True, "message": "Candidate accepted for assessment"})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)

@app.post("/api/respond-to-offer")
async def respond_to_offer(request: Request):
    """Handle applicant accepting or rejecting an offer"""
    try:
        data = await request.json()
        application_id = int(data.get("application_id", 0))
        offer_id = int(data.get("offer_id", 0))
        response = data.get("response") # 'accepted' or 'rejected'
        
        if not application_id or not offer_id or response not in ['accepted', 'rejected']:
            return JSONResponse(content={"success": False, "error": "Invalid request"}, status_code=400)
        
        offer_status = 'accepted' if response == 'accepted' else 'rejected'
        new_status = 'offer_accepted' if response == 'accepted' else 'offer_rejected'
        db.update_offer_status(offer_id, offer_status)
        db.update_application_status(application_id, new_status)
        
        return JSONResponse(content={"success": True, "message": f"Offer {response} successfully"})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)

@app.post("/api/reject-application")
async def reject_application(request: Request):
    try:
        data = await request.json()
        application_id = int(data.get("application_id", 0))
        reason = data.get("reason", "Does not meet requirements")
        if not application_id:
            return JSONResponse(content={"success": False, "error": "Missing application_id"}, status_code=400)
        conn = __import__('sqlite3').connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE job_applications SET status = 'rejected' WHERE id = ?", (application_id,))
        conn.commit(); conn.close()
        return JSONResponse(content={"success": True, "message": "Candidate rejected"})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)



@app.post("/api/ai-generate-questions")
async def ai_generate_questions(request: Request):
    """Generate interview questions based on candidate and job"""
    try:
        data = await request.json()
        resume_data = data.get('resume_data', {})
        job_requirements = data.get('job_requirements', {})
        
        # Generate questions
        questions = ai_agent.generate_interview_questions(resume_data, job_requirements)
        
        return JSONResponse(content={
            'success': True,
            'questions': questions
        })
        
    except Exception as e:
        return JSONResponse(content={
            'success': False,
            'error': str(e)
        }, status_code=500)


@app.post("/api/ai-filter-candidates")
async def ai_filter_candidates(request: Request):
    """AI-powered candidate filtering and ranking"""
    try:
        data = await request.json()
        candidates = data.get('candidates', [])
        filters = data.get('filters', {})
        
        # Filter and rank candidates
        filtered_candidates = ai_agent.filter_candidates(candidates, filters)
        
        return JSONResponse(content={
            'success': True,
            'candidates': filtered_candidates
        })
        
    except Exception as e:
        return JSONResponse(content={
            'success': False,
            'error': str(e)
        }, status_code=500)


def normalize_spaced_text(text: str) -> str:
    """Detects and fixes spaced-out text (e.g. 'P r o d u c t')"""
    if not text: return ""
    sample = text[:500]
    # Check if a high percentage of 'words' are single characters
    words = sample.split()
    if not words: return text
    single_chars = [w for w in words if len(w) == 1 and w.isalnum()]
    if len(words) > 10 and len(single_chars) / len(words) > 0.6:
        # Step 1: Placeholder for double spaces (which denote real spaces)
        text = text.replace('  ', '|||')
        # Step 2: Remove all single spaces
        text = text.replace(' ', '')
        # Step 3: Restore double spaces as single spaces
        text = text.replace('|||', ' ')
        # Step 4: Handle multiple newlines or other debris
        text = re.sub(r'\n+', '\n', text)
    return text

def _extract_text_from_pdf(file: UploadFile) -> str:
    """Extract text from uploaded PDF file using pypdf"""
    try:
        pdf_reader = pypdf.PdfReader(file.file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return normalize_spaced_text(text.strip())
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""

@app.post("/apply/{job_id}")
async def submit_application(
    job_id: int,
    name: str = Form(...),
    email: str = Form(...),
    phone: Optional[str] = Form(None),
    position: Optional[str] = Form(""),
    cover_letter: Optional[str] = Form(""),
    resume_text: Optional[str] = Form(None),
    consent: bool = Form(False),
    resume: Optional[UploadFile] = File(None)
):
    """Handle job application submission with AI job-specific scoring"""
    try:
        # Get job details for AI scoring
        job = db.get_job(job_id)
        if not job:
            return JSONResponse(content={'success': False, 'error': 'Job not found'}, status_code=404)
        
        # Check for existing application
        existing_app = db.check_existing_application(email, job_id)
        if existing_app:
            return JSONResponse(content={
                'success': False,
                'error': 'You have already applied for this position.'
            }, status_code=400)

        # Extract resume text if file is provided
        if resume and resume.filename.endswith('.pdf'):
            extracted_text = _extract_text_from_pdf(resume)
            if extracted_text:
                resume_text = extracted_text
        
        # Normalize text even if pasted manually
        if resume_text:
            resume_text = normalize_spaced_text(resume_text)
        
        if not resume_text:
            return JSONResponse(content={'success': False, 'error': 'Resume text or PDF file is required'}, status_code=400)

        # Add applicant to database
        applicant_id = db.add_applicant(
            name=name,
            email=email,
            phone=phone,
            position=position or job['title'],
            consent=consent
        )
        
        # Parse resume data for AI scoring
        resume_data = {
            'id': applicant_id,
            'name': name,
            'email': email,
            'resume_text': resume_text,
            'experience_years': _extract_experience_years(resume_text),
            'skills': _extract_skills(resume_text),
            'certifications': _extract_certifications(resume_text),
            'education_level': _extract_education(resume_text)
        }
        
        # Build job requirements from job data
        job_requirements = {
            'id': job_id,
            'title': job['title'],
            'department': job['department'],
            'description': job['description'],
            'experience_years': _extract_job_experience_requirement(job['description']),
            'technical_skills': _extract_job_skills(job['description']),
            'certifications': _extract_job_certifications(job['description'])
        }
        
        # Perform AI screening
        ai_screening = ai_agent.screen_candidate(resume_data, job_requirements)
        
        # Generate interview questions
        interview_questions = ai_agent.generate_interview_questions(resume_data, job_requirements)
        
        # Also get traditional score for comparison
        traditional_result = scorer.score_resume(resume_text)
        
        # Save both scores
        db.save_resume_score(
            applicant_id=applicant_id,
            resume_text=resume_text,
            score=traditional_result['score'],
            features=traditional_result['features'],
            recommendations=traditional_result['recommendations']
        )
        
        # Save AI screening result
        db.save_ai_screening(
            applicant_id=applicant_id,
            job_id=job_id,
            ai_score=ai_screening['screening_score'],
            ai_status=ai_screening['status'],
            match_details=ai_screening['match_details'],
            interview_questions=interview_questions
        )
        
        # Create job application
        db.add_job_application(
            job_id=job_id,
            applicant_id=applicant_id,
            cover_letter=cover_letter
        )
        
        return JSONResponse(content={
            'success': True,
            'message': 'Application submitted successfully',
            'ai_screening': {
                'score': ai_screening['screening_score'],
                'status': ai_screening['status'],
                'match_details': ai_screening['match_details']
            },
            'traditional_score': traditional_result['score']
        })
        
    except Exception as e:
        return JSONResponse(content={
            'success': False,
            'error': str(e)
        }, status_code=500)


# Helper functions for extracting data from text
def _extract_experience_years(text: str) -> int:
    """Extract years of experience from resume text"""
    import re
    patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
        r'experience[:\s]*(\d+)\+?\s*years?',
        r'(\d+)\+?\s*years?\s*(?:of\s*)?work',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return int(match.group(1))
    return 0

def _extract_skills(text: str) -> List[str]:
    """Extract technical skills from resume text"""
    common_skills = [
        'javascript', 'servicenow', 'glide', 'flow designer', 'integration hub',
        'service portal', 'catalog', 'workflow', 'scripting', 'rest api',
        'gsoap', 'angular', 'react', 'html', 'css', 'sql', 'git'
    ]
    
    text_lower = text.lower()
    found_skills = []
    
    for skill in common_skills:
        if skill in text_lower:
            found_skills.append(skill)
    
    return found_skills

def _extract_certifications(text: str) -> List[str]:
    """Extract ServiceNow certifications from resume text"""
    certifications = [
        'CSA', 'CIS', 'CAD', 'CIS-EM', 'CSM', 'CSP', 'CIS-HR', 'CIS-SM'
    ]
    
    text_upper = text.upper()
    found_certs = []
    
    for cert in certifications:
        if cert in text_upper:
            found_certs.append(cert)
    
    return found_certs

def _extract_education(text: str) -> str:
    """Extract education level from resume text"""
    text_lower = text.lower()
    
    if 'phd' in text_lower or 'doctorate' in text_lower:
        return 'PhD'
    elif 'master' in text_lower or 'm.s.' in text_lower:
        return 'Master'
    elif 'bachelor' in text_lower or 'b.s.' in text_lower:
        return 'Bachelor'
    else:
        return 'Unknown'

def _extract_job_experience_requirement(description: str) -> int:
    """Extract required years of experience from job description"""
    return _extract_experience_years(description)

def _extract_job_skills(description: str) -> List[str]:
    """Extract required skills from job description"""
    return _extract_skills(description)

def _extract_job_certifications(description: str) -> List[str]:
    """Extract required certifications from job description"""
    return _extract_certifications(description)


# Register candidate assessment routes (take-assessment, submit-assessment)
from candidate_assessment import register_assessment_routes
register_assessment_routes(app)

# Mount static files for templates
app.mount("/templates", StaticFiles(directory="templates"), name="templates")

if __name__ == "__main__":
    import uvicorn
    print("Starting TalentFlow Portal...")
    print("Open http://localhost:8005 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8005)