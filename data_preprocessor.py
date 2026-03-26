import pandas as pd
import numpy as np
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
import os

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        nltk.download('punkt_tab')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

class ResumePreprocessor:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.scaler = StandardScaler()
        
    def clean_text(self, text):
        """Clean and preprocess text data"""
        if pd.isna(text):
            return ""
        
        # Convert to lowercase
        text = str(text).lower()
        
        # Remove special characters and digits
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def tokenize_and_lemmatize(self, text):
        """Tokenize and lemmatize text"""
        tokens = word_tokenize(text)
        
        # Remove stopwords and lemmatize
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens 
                 if token not in self.stop_words and len(token) > 2]
        
        return ' '.join(tokens)
    
    def extract_features(self, df):
        """Extract features from resume data"""
        features = pd.DataFrame()
        
        # Text features
        if 'resume_text' in df.columns:
            df['cleaned_text'] = df['resume_text'].apply(self.clean_text)
            df['processed_text'] = df['cleaned_text'].apply(self.tokenize_and_lemmatize)
            
            # Text length features
            features['text_length'] = df['cleaned_text'].str.len()
            features['word_count'] = df['cleaned_text'].str.split().str.len()
            
            # TF-IDF features
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(df['processed_text'])
            tfidf_df = pd.DataFrame(tfidf_matrix.toarray(), 
                                   columns=self.tfidf_vectorizer.get_feature_names_out())
            features = pd.concat([features, tfidf_df], axis=1)
        
        # Skills-related features
        skills_keywords = [
            'python', 'java', 'javascript', 'sql', 'machine learning', 'data analysis',
            'project management', 'leadership', 'communication', 'teamwork',
            'excel', 'powerpoint', 'tableau', 'aws', 'docker', 'git'
        ]
        
        for skill in skills_keywords:
            if 'resume_text' in df.columns:
                features[f'has_{skill.replace(" ", "_")}'] = df['resume_text'].str.lower().str.contains(skill.lower()).astype(int)
        
        # Experience-related features
        experience_patterns = [
            r'\d+\+?\s*years?', r'\d+\s*-\s*\d+\s*years?', 
            r'experience', 'experienced', 'senior', 'junior', 'lead'
        ]
        
        if 'resume_text' in df.columns:
            features['has_experience_info'] = 0
            for pattern in experience_patterns:
                features['has_experience_info'] += df['resume_text'].str.lower().str.contains(pattern, regex=True).astype(int)
        
        # Education-related features
        education_keywords = ['bachelor', 'master', 'phd', 'degree', 'university', 'college']
        
        if 'resume_text' in df.columns:
            features['education_score'] = 0
            for keyword in education_keywords:
                features['education_score'] += df['resume_text'].str.lower().str.contains(keyword).astype(int)
        
        return features, df
    
    def create_target_variable(self, df):
        """Create a target variable for training (resume quality score)"""
        # This is a simplified scoring system
        # In a real scenario, you'd have human-labeled scores
        
        score = np.zeros(len(df))
        
        # Base score
        score += 30
        
        # Text length contribution
        if 'text_length' in df.columns:
            score += np.minimum(df['text_length'] / 100, 20)
        
        # Skills contribution
        skill_columns = [col for col in df.columns if col.startswith('has_')]
        if skill_columns:
            score += df[skill_columns].sum(axis=1) * 3
        
        # Experience contribution
        if 'has_experience_info' in df.columns:
            score += np.minimum(df['has_experience_info'] * 5, 20)
        
        # Education contribution
        if 'education_score' in df.columns:
            score += np.minimum(df['education_score'] * 2, 10)
        
        # Normalize to 0-100 scale
        score = np.clip(score, 0, 100)
        
        return score
    
    def load_and_process_data(self, file_path):
        """Load and process resume dataset"""
        # Try different file formats
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif file_path.endswith('.json'):
            df = pd.read_json(file_path)
        else:
            raise ValueError("Unsupported file format")
        
        print(f"Dataset shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        
        # Extract features
        features, processed_df = self.extract_features(df)
        
        # Create target variable
        target = self.create_target_variable(features)
        
        return features, target, processed_df
