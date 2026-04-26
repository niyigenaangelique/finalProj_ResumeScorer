import pypdf
import sys

def test_extraction(pdf_path):
    try:
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        print("--- START TEXT ---")
        print(text[:500])
        print("--- END TEXT ---")
        
        # Check for keywords
        keywords = ['python', 'experience', 'education']
        for k in keywords:
            print(f"Contains '{k}': {k in text.lower()}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_extraction('generated_cvs/1_senior_software_engineer_SCORE_85_HIGH.pdf')
