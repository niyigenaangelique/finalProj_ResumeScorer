import os
import kaggle
from kaggle.api.kaggle_api_extended import KaggleApi
import pandas as pd
import zipfile

def download_resume_dataset():
    """Download the resume dataset from Kaggle"""
    
    # Try different popular resume datasets
    datasets = [
        "gauravduttakiit/resume-dataset",
        "snehaanbhawal/resume-dataset",
        "dataturks/resume-entities",
        "akash14/resume-dataset"
    ]
    
    api = KaggleApi()
    api.authenticate()
    
    for dataset in datasets:
        try:
            print(f"Trying to download: {dataset}")
            api.dataset_download_files(dataset, path="./data", unzip=True)
            print(f"Successfully downloaded: {dataset}")
            return True
        except Exception as e:
            print(f"Failed to download {dataset}: {e}")
            continue
    
    print("Could not download any dataset. Please check your Kaggle API credentials.")
    return False

def check_data_files():
    """Check what data files are available"""
    if os.path.exists("./data"):
        files = os.listdir("./data")
        print("Available files:")
        for file in files:
            print(f"  - {file}")
        return files
    else:
        print("No data directory found")
        return []

if __name__ == "__main__":
    # Create data directory
    os.makedirs("./data", exist_ok=True)
    
    # Download dataset
    if download_resume_dataset():
        # Check what was downloaded
        check_data_files()
