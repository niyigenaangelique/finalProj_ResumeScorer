# Simple Resume Scoring Demo (without ML dependencies)
# This demonstrates the concept without requiring pandas/scikit-learn

import re
import math

class SimpleResumeScorer:
    def __init__(self):
        self.skills_keywords = {
            'technical': [
                'python', 'java', 'javascript', 'sql', 'html', 'css', 'react', 'nodejs',
                'aws', 'docker', 'git', 'linux', 'machine learning', 'data analysis',
                'tableau', 'excel', 'powerpoint', 'api', 'database', 'cloud'
            ],
            'soft': [
                'leadership', 'communication', 'teamwork', 'project management',
                'problem solving', 'critical thinking', 'collaboration', 'time management'
            ],
            'education': [
                'bachelor', 'master', 'phd', 'degree', 'university', 'college',
                'computer science', 'engineering', 'business', 'statistics'
            ]
        }
        
    def extract_text_features(self, text):
        """Extract basic features from resume text"""
        text_lower = text.lower()
        
        features = {
            'text_length': len(text),
            'word_count': len(text.split()),
            'technical_skills': 0,
            'soft_skills': 0,
            'education_terms': 0,
            'experience_years': 0,
            'has_numbers': bool(re.search(r'\d+', text)),
            'has_email': bool(re.search(r'\S+@\S+\.\S+', text)),
            'has_phone': bool(re.search(r'\d{3}[-.]?\d{3}[-.]?\d{4}', text))
        }
        
        # Count skills
        for skill in self.skills_keywords['technical']:
            if skill in text_lower:
                features['technical_skills'] += 1
                
        for skill in self.skills_keywords['soft']:
            if skill in text_lower:
                features['soft_skills'] += 1
                
        for term in self.skills_keywords['education']:
            if term in text_lower:
                features['education_terms'] += 1
        
        # Extract years of experience
        year_patterns = [
            r'(\d+)\+?\s*years?',
            r'(\d+)\s*-\s*(\d+)\s*years?'
        ]
        
        for pattern in year_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                if isinstance(match, tuple):
                    years = max(int(match[0]), int(match[1]))
                else:
                    years = int(match)
                features['experience_years'] = max(features['experience_years'], years)
        
        return features
    
    def calculate_score(self, features):
        """Calculate resume score based on features"""
        score = 0
        
        # Base score
        score += 20
        
        # Text length contribution (max 15 points)
        length_score = min(features['word_count'] / 10, 15)
        score += length_score
        
        # Technical skills contribution (max 25 points)
        tech_score = min(features['technical_skills'] * 2, 25)
        score += tech_score
        
        # Soft skills contribution (max 15 points)
        soft_score = min(features['soft_skills'] * 1.5, 15)
        score += soft_score
        
        # Education contribution (max 10 points)
        edu_score = min(features['education_terms'] * 2, 10)
        score += edu_score
        
        # Experience contribution (max 15 points)
        exp_score = min(features['experience_years'] * 2, 15)
        score += exp_score
        
        # Contact information (max 5 points)
        contact_score = 0
        if features['has_email']:
            contact_score += 2.5
        if features['has_phone']:
            contact_score += 2.5
        score += contact_score
        
        # Normalize to 0-100
        score = max(0, min(100, score))
        
        return round(score, 1)
    
    def get_recommendations(self, score, features):
        """Generate recommendations based on score and features"""
        recommendations = []
        
        if score < 40:
            recommendations.append("Add more details about your skills and experience")
            recommendations.append("Include specific achievements with metrics")
        elif score < 60:
            recommendations.append("Highlight more technical skills")
            recommendations.append("Add quantifiable achievements")
        elif score < 80:
            recommendations.append("Good resume! Consider adding leadership experience")
            recommendations.append("Include more specific project details")
        
        if features['technical_skills'] < 3:
            recommendations.append("Add more technical skills and technologies")
        
        if features['experience_years'] < 2:
            recommendations.append("Specify years of experience for each role")
        
        if not features['has_email'] or not features['has_phone']:
            recommendations.append("Ensure contact information is complete")
        
        return recommendations
    
    def score_resume(self, resume_text):
        """Score a complete resume"""
        features = self.extract_text_features(resume_text)
        score = self.calculate_score(features)
        recommendations = self.get_recommendations(score, features)
        
        return {
            'score': score,
            'features': features,
            'recommendations': recommendations
        }

def demo():
    """Run the demo"""
    print("=== Simple Resume Scoring Demo ===\n")
    
    scorer = SimpleResumeScorer()
    
    sample_resumes = [
        {
            'name': 'Senior Developer',
            'text': '''
            John Doe
            Email: john.doe@email.com | Phone: 555-123-4567
            
            EXPERIENCE
            Senior Software Engineer | Tech Corp | 2018-Present (5+ years)
            - Led team of 5 developers on cloud migration project
            - Developed RESTful APIs using Python and Node.js
            - Implemented machine learning models for data analysis
            - Managed AWS infrastructure and Docker containers
            
            SKILLS
            Technical: Python, Java, JavaScript, SQL, AWS, Docker, Git, Machine Learning
            Soft: Leadership, Project Management, Communication, Teamwork
            
            EDUCATION
            Master of Computer Science - Stanford University
            Bachelor of Engineering - MIT
            '''
        },
        {
            'name': 'Data Analyst',
            'text': '''
            Jane Smith
            Email: jane.smith@email.com | Phone: 555-987-6543
            
            EXPERIENCE
            Data Analyst | Data Corp | 2021-Present (3 years)
            - Analyzed large datasets using SQL and Python
            - Created dashboards and reports using Tableau
            - Collaborated with cross-functional teams
            
            SKILLS
            Technical: SQL, Python, Excel, Tableau, Data Analysis
            Soft: Communication, Teamwork, Problem Solving
            
            EDUCATION
            Bachelor of Statistics - State University
            '''
        },
        {
            'name': 'Entry Level',
            'text': '''
            Mike Johnson
            Email: mike.j@email.com
            
            EDUCATION
            Bachelor of Computer Science - Local University
            
            SKILLS
            Python, Java, HTML, CSS, Git
            
            PROJECTS
            - Built a web application for class project
            - Contributed to open source projects
            '''
        }
    ]
    
    for i, resume in enumerate(sample_resumes, 1):
        print(f"Resume {i}: {resume['name']}")
        print("-" * 50)
        
        result = scorer.score_resume(resume['text'])
        
        print(f"Score: {result['score']}/100")
        
        # Rating
        if result['score'] >= 80:
            rating = "Excellent - Strong candidate"
        elif result['score'] >= 60:
            rating = "Good - Qualified candidate"
        elif result['score'] >= 40:
            rating = "Fair - May need additional review"
        else:
            rating = "Poor - May not meet requirements"
        
        print(f"Rating: {rating}")
        
        print("\nKey Features:")
        print(f"  Technical Skills: {result['features']['technical_skills']}")
        print(f"  Soft Skills: {result['features']['soft_skills']}")
        print(f"  Experience Years: {result['features']['experience_years']}")
        print(f"  Word Count: {result['features']['word_count']}")
        
        if result['recommendations']:
            print("\nRecommendations:")
            for rec in result['recommendations']:
                print(f"  • {rec}")
        
        print("\n" + "="*60 + "\n")
    
    print("Demo completed!")
    print("\nTo use with real ML models:")
    print("1. Install dependencies: pip install pandas scikit-learn nltk fastapi uvicorn")
    print("2. Run: python demo.py")
    print("3. Start web server: python app.py")
    print("4. Open: http://localhost:8000")

if __name__ == "__main__":
    demo()
