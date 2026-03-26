from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
import pandas as pd
import numpy as np
import joblib
import os
import io
from typing import Optional
import json
from data_preprocessor import ResumePreprocessor
import re

app = FastAPI(title="Resume Scoring API", description="API for scoring resumes in recruitment process")

# Create directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Setup templates
templates = Jinja2Templates(directory="templates")

# Load the trained model
model_path = "models/resume_model.pkl"
model_data = None
preprocessor = None

def load_model():
    """Load the trained model"""
    global model_data, preprocessor
    try:
        if os.path.exists(model_path):
            model_data = joblib.load(model_path)
            preprocessor = model_data['preprocessor']
            return True
        else:
            print("Model not found. Please train the model first.")
            return False
    except Exception as e:
        print(f"Error loading model: {e}")
        return False

# Try to load model on startup
load_model()

class ResumeScorer:
    def __init__(self):
        self.preprocessor = ResumePreprocessor()
        
    def extract_text_from_file(self, file_content: bytes, filename: str):
        """Extract text from uploaded file"""
        # This is a simplified version - in production, you'd use proper parsers
        # for PDF, DOCX, etc.
        
        try:
            # Try to decode as text first
            text = file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                # Try different encodings
                text = file_content.decode('latin-1')
            except:
                # For binary files (PDF, DOCX), return placeholder
                text = f"Binary file uploaded: {filename}. Please provide text content."
        
        return text
    
    def score_resume(self, resume_text: str):
        """Score a single resume"""
        if model_data is None:
            raise HTTPException(status_code=500, detail="Model not loaded")
        
        # Create a DataFrame with the resume text
        df = pd.DataFrame({'resume_text': [resume_text]})
        
        # Extract features
        features, _ = self.preprocessor.extract_features(df)
        
        # Ensure features match training data
        expected_features = model_data['model'].n_features_in_
        if features.shape[1] != expected_features:
            # Pad or truncate features to match expected size
            if features.shape[1] < expected_features:
                # Add missing columns with zeros
                for i in range(features.shape[1], expected_features):
                    features[f'missing_feature_{i}'] = 0
            else:
                # Truncate extra features
                features = features.iloc[:, :expected_features]
        
        # Make prediction
        score = model_data['model'].predict(features)[0]
        
        # Ensure score is in valid range
        score = max(0, min(100, score))
        
        # Get feature contributions (simplified)
        feature_contributions = {}
        if hasattr(model_data['model'], 'feature_importances_'):
            importances = model_data['model'].feature_importances_
            for i, (feature, importance) in enumerate(zip(features.columns, importances)):
                if importance > 0.01:  # Only include important features
                    feature_contributions[feature] = float(importance * 100)
        
        return {
            'score': float(round(score, 2)),
            'feature_contributions': feature_contributions,
            'recommendations': self.get_recommendations(score, resume_text)
        }
    
    def get_recommendations(self, score: float, resume_text: str):
        """Generate recommendations based on score and content"""
        recommendations = []
        
        if score < 40:
            recommendations.append("Consider adding more specific skills and experiences")
            recommendations.append("Include quantifiable achievements")
        elif score < 60:
            recommendations.append("Add more details about your work experience")
            recommendations.append("Highlight relevant technical skills")
        elif score < 80:
            recommendations.append("Good resume! Consider adding more specific metrics")
            recommendations.append("Include leadership or project management experience")
        
        # Check for missing common skills
        common_skills = ['python', 'java', 'sql', 'machine learning', 'data analysis']
        missing_skills = [skill for skill in common_skills 
                         if skill.lower() not in resume_text.lower()]
        
        if missing_skills and len(missing_skills) < 3:
            recommendations.append(f"Consider mentioning: {', '.join(missing_skills[:3])}")
        
        return recommendations

# Initialize scorer
scorer = ResumeScorer()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with upload form"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/score")
async def score_resume_text(resume_text: str = Form(...)):
    """Score resume from text input"""
    try:
        result = scorer.score_resume(resume_text)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/score-file")
async def score_resume_file(file: UploadFile = File(...)):
    """Score resume from uploaded file"""
    try:
        # Read file content
        content = await file.read()
        
        # Extract text
        resume_text = scorer.extract_text_from_file(content, file.filename)
        
        # Score the resume
        result = scorer.score_resume(resume_text)
        
        # Add file info
        result['filename'] = file.filename
        result['extracted_text_length'] = len(resume_text)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/score-batch")
async def score_multiple_resumes(files: list[UploadFile] = File(...)):
    """Score multiple resumes"""
    try:
        results = []
        
        for file in files:
            content = await file.read()
            resume_text = scorer.extract_text_from_file(content, file.filename)
            result = scorer.score_resume(resume_text)
            result['filename'] = file.filename
            results.append(result)
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return JSONResponse(content={
            'total_resumes': len(results),
            'results': results
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/model-info")
async def get_model_info():
    """Get information about the loaded model"""
    if model_data is None:
        raise HTTPException(status_code=404, detail="Model not loaded")
    
    return {
        'model_name': model_data['model_name'],
        'model_type': type(model_data['model']).__name__,
        'features_count': model_data['model'].n_features_in_ if hasattr(model_data['model'], 'n_features_in_') else 'Unknown'
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'model_loaded': model_data is not None
    }

# Create HTML template
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
            color: #007bff;
            margin-bottom: 10px;
        }
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
    </style>
</head>
<body>
    <div class="container">
        <h1>Resume Scoring System</h1>
        
        <div class="form-group">
            <label for="resumeText">Paste Resume Text:</label>
            <textarea id="resumeText" placeholder="Paste the resume text here..."></textarea>
        </div>
        
        <div class="form-group">
            <label for="resumeFile">Or Upload Resume File:</label>
            <input type="file" id="resumeFile" accept=".txt,.pdf,.doc,.docx">
        </div>
        
        <button onclick="scoreResume()">Score Resume</button>
        
        <div class="loading" id="loading">
            <p>Scoring resume... Please wait.</p>
        </div>
        
        <div id="result"></div>
    </div>

    <script>
        async function scoreResume() {
            const resumeText = document.getElementById('resumeText').value;
            const resumeFile = document.getElementById('resumeFile').files[0];
            
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
                    response = await fetch('/score-file', {
                        method: 'POST',
                        body: formData
                    });
                } else {
                    const formData = new FormData();
                    formData.append('resume_text', resumeText);
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
        
        function displayResult(result) {
            const scoreColor = result.score >= 80 ? '#28a745' : 
                             result.score >= 60 ? '#ffc107' : '#dc3545';
            
            let html = `
                <div class="result">
                    <div class="score" style="color: ${scoreColor}">
                        Resume Score: ${result.score}/100
                    </div>
            `;
            
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

# Write the HTML template
with open("templates/index.html", "w") as f:
    f.write(html_template)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
