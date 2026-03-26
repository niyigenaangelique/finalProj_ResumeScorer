# Resume Scoring System - Setup Guide

## Quick Start

### Option 1: Simple Demo (No Dependencies)
```bash
cd resume_scorer
python simple_demo.py
```

This runs a basic scoring system without requiring any external packages.

### Option 2: Full ML System

#### 1. Install Dependencies
```bash
cd resume_scorer
pip install -r requirements.txt
```

#### 2. Download Dataset (Optional)
```bash
python download_data.py
```
*Note: Requires Kaggle API credentials*

#### 3. Train Model
```bash
python demo.py
```

#### 4. Start Web Server
```bash
python app.py
```

#### 5. Open Browser
Navigate to: http://localhost:8000

## Features

### Scoring Algorithm
- **Technical Skills**: Python, Java, SQL, AWS, Docker, etc.
- **Soft Skills**: Leadership, Communication, Teamwork, etc.
- **Experience**: Years of professional experience
- **Education**: Degrees and certifications
- **Contact Info**: Email and phone presence
- **Text Quality**: Length and completeness

### Score Breakdown
- **80-100**: Excellent - Strong candidate
- **60-79**: Good - Qualified candidate
- **40-59**: Fair - May need additional review
- **0-39**: Poor - May not meet requirements

### API Endpoints
- `POST /score` - Score resume from text
- `POST /score-file` - Score resume from file upload
- `POST /score-batch` - Score multiple resumes
- `GET /model-info` - Get model information
- `GET /health` - Health check

### Web Interface
- Clean, responsive design
- File upload support
- Real-time scoring
- Detailed recommendations
- Batch processing capability

## File Structure
```
resume_scorer/
├── app.py                 # FastAPI web server
├── demo.py               # ML training pipeline
├── simple_demo.py        # Basic demo (no dependencies)
├── download_data.py      # Kaggle dataset downloader
├── data_preprocessor.py  # Text preprocessing and feature extraction
├── model_trainer.py      # ML model training and evaluation
├── requirements.txt      # Python dependencies
├── README.md            # Project documentation
├── SETUP.md             # This setup guide
├── data/                # Dataset directory
├── models/              # Trained models
├── uploads/             # File uploads
├── templates/           # HTML templates
└── static/              # Static files
```

## Usage Examples

### Python API Usage
```python
import requests

# Score resume text
response = requests.post('http://localhost:8000/score', 
                        data={'resume_text': 'Your resume text here...'})
result = response.json()
print(f"Score: {result['score']}/100")

# Score resume file
with open('resume.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/score-file', files=files)
    result = response.json()
    print(f"Score: {result['score']}/100")
```

### Command Line Usage
```bash
# Run simple demo
python simple_demo.py

# Train full ML model
python demo.py

# Start web server
python app.py
```

## Customization

### Adding New Skills
Edit `data_preprocessor.py` to add new skill keywords:
```python
skills_keywords = [
    'python', 'java', 'javascript', 'sql', 
    'your_new_skill', 'another_skill'
]
```

### Adjusting Scoring Weights
Modify the scoring logic in `simple_demo.py` or the ML model training in `model_trainer.py`.

### Custom Training Data
Replace the sample data in `demo.py` with your own labeled resume dataset.

## Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
- `MODEL_PATH`: Path to trained model file
- `DATA_PATH`: Path to training data
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)

## Troubleshooting

### Common Issues
1. **ModuleNotFoundError**: Install dependencies with `pip install -r requirements.txt`
2. **Model not found**: Run `python demo.py` to train and save a model
3. **Port already in use**: Change port in `app.py` or kill existing process
4. **Kaggle API errors**: Set up Kaggle API credentials in `~/.kaggle/kaggle.json`

### Performance Tips
- Use GPU for training large datasets
- Implement caching for frequent requests
- Add rate limiting for API endpoints
- Use Redis for session management

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the code comments
3. Test with the simple demo first
4. Ensure all dependencies are installed

## License

This project is provided as-is for educational and development purposes.
