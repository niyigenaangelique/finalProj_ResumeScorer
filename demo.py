import pandas as pd
import numpy as np
from data_preprocessor import ResumePreprocessor
from model_trainer import ResumeModelTrainer
import os

def create_sample_data():
    """Create sample resume data for demonstration"""
    
    sample_resumes = [
        {
            'resume_text': '''
            John Doe
            Senior Software Engineer
            
            Experience:
            - 5+ years of experience in software development
            - Led team of 5 developers on multiple projects
            - Expert in Python, Java, and JavaScript
            - Experience with AWS, Docker, and Kubernetes
            - Master's degree in Computer Science
            
            Skills:
            Python, Java, SQL, Machine Learning, Data Analysis, Project Management, Leadership
            '''
        },
        {
            'resume_text': '''
            Jane Smith
            Data Analyst
            
            Experience:
            - 3 years of data analysis experience
            - Proficient in SQL, Excel, and Tableau
            - Bachelor's degree in Statistics
            - Experience with data visualization and reporting
            
            Skills:
            SQL, Excel, Tableau, Data Analysis, Communication, Teamwork
            '''
        },
        {
            'resume_text': '''
            Mike Johnson
            Entry Level Developer
            
            Education:
            - Bachelor's degree in Computer Science
            - Recent graduate with internship experience
            
            Skills:
            Python, Java, HTML, CSS, Git
            '''
        }
    ]
    
    # Duplicate samples to have enough data for cross-validation
    sample_resumes = sample_resumes * 10
    
    df = pd.DataFrame(sample_resumes)
    return df

def demo_pipeline():
    """Run a complete demo of the resume scoring system"""
    
    print("=== Resume Scoring System Demo ===\n")
    
    # Step 1: Create sample data
    print("1. Creating sample resume data...")
    df = create_sample_data()
    print(f"Created {len(df)} sample resumes")
    
    # Save sample data
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/sample_resumes.csv", index=False)
    print("Sample data saved to data/sample_resumes.csv")
    
    # Step 2: Preprocess data and extract features
    print("\n2. Preprocessing data and extracting features...")
    preprocessor = ResumePreprocessor()
    X, y, processed_df = preprocessor.load_and_process_data("data/sample_resumes.csv")
    print(f"Features extracted: {X.shape[1]} features")
    print(f"Target scores range: {y.min():.1f} - {y.max():.1f}")
    
    # Step 3: Train models
    print("\n3. Training machine learning models...")
    trainer = ResumeModelTrainer()
    results, X_test, y_test = trainer.train_models(X, y)
    
    # Step 4: Save the best model
    print("\n4. Saving the best model...")
    trainer.save_model()
    
    # Step 5: Test the scoring system
    print("\n5. Testing the scoring system...")
    
    # Load the model
    trainer.load_model()
    
    # Test with sample resumes
    for i, resume in enumerate(sample_resumes):
        print(f"\nResume {i+1}:")
        print(f"Text preview: {resume['resume_text'][:100]}...")
        
        # Create DataFrame for prediction
        test_df = pd.DataFrame({'resume_text': [resume['resume_text']]})
        features, _ = preprocessor.extract_features(test_df)
        
        # Ensure features match
        if features.shape[1] != trainer.best_model.n_features_in_:
            # Pad with zeros if needed
            for j in range(features.shape[1], trainer.best_model.n_features_in_):
                features[f'pad_{j}'] = 0
            features = features.iloc[:, :trainer.best_model.n_features_in_]
        
        # Predict score
        score = trainer.best_model.predict(features)[0]
        score = max(0, min(100, score))
        
        print(f"Predicted Score: {score:.1f}/100")
        
        # Provide interpretation
        if score >= 80:
            print("Rating: Excellent - Strong candidate")
        elif score >= 60:
            print("Rating: Good - Qualified candidate")
        elif score >= 40:
            print("Rating: Fair - May need additional review")
        else:
            print("Rating: Poor - May not meet requirements")
    
    print("\n=== Demo Complete ===")
    print("\nTo run the web interface:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Run the API server: python app.py")
    print("3. Open browser to: http://localhost:8000")
    
    print("\nAPI Endpoints:")
    print("- POST /score - Score resume from text")
    print("- POST /score-file - Score resume from file")
    print("- POST /score-batch - Score multiple resumes")
    print("- GET /model-info - Get model information")
    print("- GET /health - Health check")

if __name__ == "__main__":
    demo_pipeline()
