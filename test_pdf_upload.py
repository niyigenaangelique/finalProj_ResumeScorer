import os
import requests
from fastapi.testclient import TestClient
from modern_portal import app as modern_app
from job_portal import app as job_app

def test_pdf_upload(app_to_test, job_id):
    client = TestClient(app_to_test)
    
    # Path to one of the generated PDFs
    pdf_path = 'generated_cvs/1_senior_software_engineer_SCORE_85_HIGH.pdf'
    
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found. Run generation script first.")
        return

    with open(pdf_path, 'rb') as f:
        files = {'resume': (os.path.basename(pdf_path), f, 'application/pdf')}
        data = {
            'name': 'Test PDF Candidate',
            'email': f'test_pdf_{secrets.token_hex(4)}@example.com',
            'phone': '123456789',
            'cover_letter': 'I am testing PDF upload.',
            'consent': 'true'
        }
        
        print(f"Testing PDF upload to /apply/{job_id}...")
        response = client.post(f"/apply/{job_id}", data=data, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Response: {result}")
            if 'ai_screening' in result:
                print(f"AI Score: {result['ai_screening']['score']}")
        else:
            print(f"Failed! Status: {response.status_code}, Body: {response.text}")

import secrets
if __name__ == "__main__":
    # Test both apps
    print("--- Testing Modern Portal ---")
    test_pdf_upload(modern_app, 1)
    print("\n--- Testing Job Portal ---")
    test_pdf_upload(job_app, 1)
