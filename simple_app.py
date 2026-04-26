from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Request
import re
import os
from database import ResumeDatabase

app = FastAPI(title="Resume Scoring System", description="Simple resume scoring without ML dependencies")

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
        
    def extract_features(self, text):
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
        features = self.extract_features(resume_text)
        score = self.calculate_score(features)
        recommendations = self.get_recommendations(score, features)
        
        return {
            'score': score,
            'features': features,
            'recommendations': recommendations
        }

# Initialize scorer and database
scorer = SimpleResumeScorer()
db = ResumeDatabase()

html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resume Scoring System</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #555;
        }
        textarea, input[type="file"] {
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        textarea {
            height: 200px;
            resize: vertical;
        }
        button {
            background-color: #007bff;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
        }
        button:hover {
            background-color: #0056b3;
        }
        .result {
            margin-top: 30px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 5px;
            border-left: 4px solid #007bff;
        }
        .score {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .score.excellent { color: #28a745; }
        .score.good { color: #ffc107; }
        .score.fair { color: #fd7e14; }
        .score.poor { color: #dc3545; }
        .recommendations {
            margin-top: 15px;
        }
        .recommendations ul {
            margin: 10px 0;
            padding-left: 20px;
        }
        .recommendations li {
            margin-bottom: 5px;
        }
        .loading {
            display: none;
            text-align: center;
            margin: 20px 0;
        }
        .error {
            color: #dc3545;
            background-color: #f8d7da;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
        }
        .features {
            margin-top: 15px;
            padding: 15px;
            background-color: #e9ecef;
            border-radius: 5px;
        }
        .feature-item {
            display: inline-block;
            margin: 5px 10px;
            padding: 5px 10px;
            background-color: #007bff;
            color: white;
            border-radius: 15px;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Resume Scoring System</h1>
        <p style="text-align: center; color: #666; margin-bottom: 30px;">
            Get instant resume scoring and personalized recommendations
        </p>
        
        <div class="form-group">
            <label for="applicantName">Applicant Name (Optional):</label>
            <input type="text" id="applicantName" placeholder="John Doe">
        </div>
        
        <div class="form-group">
            <label for="email">Email (Optional):</label>
            <input type="email" id="email" placeholder="john.doe@email.com">
        </div>
        
        <div class="form-group">
            <label for="position">Position (Optional):</label>
            <input type="text" id="position" placeholder="Software Engineer">
        </div>
        
        <div class="form-group">
            <label for="resumeText">Paste Resume Text:</label>
            <textarea id="resumeText" placeholder="Paste resume text here..."></textarea>
        </div>
        
        <div class="form-group">
            <label for="resumeFile">Or Upload Resume File:</label>
            <input type="file" id="resumeFile" accept=".txt,.pdf,.doc,.docx">
        </div>
        
        <button onclick="scoreResume()">Score Resume</button>
        <button onclick="loadSample()" style="background-color: #6c757d;">Load Sample</button>
        
        <div class="loading" id="loading">
            <p>Scoring resume... Please wait.</p>
        </div>
        
        <div id="result"></div>
    </div>

    <script>
        function loadSample() {
            const sampleText = `John Doe
Senior Software Engineer

Email: john.doe@email.com | Phone: 555-123-4567

EXPERIENCE
Senior Software Engineer | Tech Corp | 2018-Present (5+ years)
- Led team of 5 developers on cloud migration project using AWS and Docker
- Developed RESTful APIs using Python and Node.js
- Implemented machine learning models for data analysis
- Managed AWS infrastructure and Docker containers

Software Engineer | StartupXYZ | 2016-2018 (2 years)
- Built web applications using JavaScript and React
- Worked with SQL databases and API development

SKILLS
Technical: Python, Java, JavaScript, SQL, AWS, Docker, Git, Machine Learning, React, Node.js
Soft: Leadership, Project Management, Communication, Teamwork, Problem Solving

EDUCATION
Master of Computer Science - Stanford University
Bachelor of Engineering - MIT`;
            
            document.getElementById('resumeText').value = sampleText;
        }
        
        async function scoreResume() {
            const resumeText = document.getElementById('resumeText').value;
            const resumeFile = document.getElementById('resumeFile').files[0];
            const applicantName = document.getElementById('applicantName').value;
            const email = document.getElementById('email').value;
            const position = document.getElementById('position').value;
            
            if (!resumeText && !resumeFile) {
                showError('Please provide resume text or upload a file');
                return;
            }
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').innerHTML = '';
            
            try {
                let response;
                
                if (resumeFile) {
                    const formData = new FormData();
                    formData.append('file', resumeFile);
                    if (applicantName) formData.append('applicant_name', applicantName);
                    if (email) formData.append('email', email);
                    if (position) formData.append('position', position);
                    response = await fetch('/score-file', {
                        method: 'POST',
                        body: formData
                    });
                } else {
                    const formData = new FormData();
                    formData.append('resume_text', resumeText);
                    if (applicantName) formData.append('applicant_name', applicantName);
                    if (email) formData.append('email', email);
                    if (position) formData.append('position', position);
                    response = await fetch('/score', {
                        method: 'POST',
                        body: formData
                    });
                }
                
                if (!response.ok) {
                    throw new Error('Scoring failed');
                }
                
                const result = await response.json();
                displayResult(result);
                
            } catch (error) {
                showError('Error scoring resume: ' + error.message);
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }
        
        function getScoreClass(score) {
            if (score >= 80) return 'excellent';
            if (score >= 60) return 'good';
            if (score >= 40) return 'fair';
            return 'poor';
        }
        
        function getRating(score) {
            if (score >= 80) return 'Excellent - Strong candidate';
            if (score >= 60) return 'Good - Qualified candidate';
            if (score >= 40) return 'Fair - May need additional review';
            return 'Poor - May not meet requirements';
        }
        
        function displayResult(result) {
            const scoreClass = getScoreClass(result.score);
            
            let html = `
                <div class="result">
                    <div class="score ${scoreClass}">
                        Resume Score: ${result.score}/100
                    </div>
                    <div style="font-size: 18px; margin-bottom: 15px;">
                        ${getRating(result.score)}
                    </div>
            `;
            
            // Features
            if (result.features) {
                html += `
                    <div class="features">
                        <strong>Key Features:</strong><br>
                        <span class="feature-item">Tech Skills: ${result.features.technical_skills}</span>
                        <span class="feature-item">Soft Skills: ${result.features.soft_skills}</span>
                        <span class="feature-item">Experience: ${result.features.experience_years} years</span>
                        <span class="feature-item">Education: ${result.features.education_terms}</span>
                        <span class="feature-item">Words: ${result.features.word_count}</span>
                    </div>
                `;
            }
            
            // Recommendations
            if (result.recommendations && result.recommendations.length > 0) {
                html += `
                    <div class="recommendations">
                        <h3>Recommendations:</h3>
                        <ul>
                `;
                result.recommendations.forEach(rec => {
                    html += `<li>${rec}</li>`;
                });
                html += `</ul></div>`;
            }
            
            if (result.filename) {
                html += `<p><strong>File:</strong> ${result.filename}</p>`;
            }
            
            html += '</div>';
            document.getElementById('result').innerHTML = html;
        }
        
        function showError(message) {
            document.getElementById('result').innerHTML = 
                `<div class="error">${message}</div>`;
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with upload form"""
    return HTMLResponse(content=html_template)

def normalize_spaced_text(text: str) -> str:
    """Detects and fixes spaced-out text (e.g. 'P r o d u c t')"""
    if not text: return ""
    sample = text[:500]
    words = sample.split()
    if not words: return text
    single_chars = [w for w in words if len(w) == 1 and w.isalnum()]
    if len(words) > 10 and len(single_chars) / len(words) > 0.6:
        text = text.replace('  ', '|||').replace(' ', '').replace('|||', ' ')
        text = re.sub(r'\n+', '\n', text)
    return text

@app.post("/score")
async def score_resume_text(resume_text: str = Form(...), applicant_name: str = Form(None), 
                         email: str = Form(None), position: str = Form(None)):
    """Score resume from text input"""
    try:
        resume_text = normalize_spaced_text(resume_text)
        result = scorer.score_resume(resume_text)
        
        # Save to database if applicant info provided
        applicant_id = None
        if applicant_name:
            applicant_id = db.add_applicant(
                name=applicant_name,
                email=email,
                position=position
            )
            
            db.save_resume_score(
                applicant_id=applicant_id,
                resume_text=resume_text,
                score=result['score'],
                features=result['features'],
                recommendations=result['recommendations']
            )
            
            result['applicant_id'] = applicant_id
        
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/score-file")
async def score_resume_file(file: UploadFile = File(...), applicant_name: str = Form(None),
                         email: str = Form(None), position: str = Form(None)):
    """Score resume from uploaded file"""
    try:
        # Read file content
        content = await file.read()
        
        # Try to decode as text
        try:
            resume_text = content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                resume_text = content.decode('latin-1')
            except:
                resume_text = f"Binary file uploaded: {file.filename}. Please provide text content."
        
        # Normalize text
        resume_text = normalize_spaced_text(resume_text)

        # Score the resume
        result = scorer.score_resume(resume_text)
        
        # Save to database if applicant info provided
        applicant_id = None
        if applicant_name:
            applicant_id = db.add_applicant(
                name=applicant_name,
                email=email,
                position=position
            )
            
            db.save_resume_score(
                applicant_id=applicant_id,
                resume_text=resume_text,
                score=result['score'],
                features=result['features'],
                recommendations=result['recommendations'],
                filename=file.filename
            )
            
            result['applicant_id'] = applicant_id
        
        # Add file info
        result['filename'] = file.filename
        result['extracted_text_length'] = len(resume_text)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'system': 'Simple Resume Scorer (No ML Dependencies)'
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting Resume Scoring System...")
    print("Open http://localhost:8000 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8000)
