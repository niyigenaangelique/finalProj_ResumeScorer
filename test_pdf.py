#!/usr/bin/env python3
"""Test PDF generation functionality"""

from pdf_generator import generate_pdf_report
from datetime import datetime

# Test data for different report types
test_data = {
    "applications": {
        "total_applications": 156,
        "by_status": {
            "Pending": 45,
            "Screened": 78,
            "Interviewed": 23,
            "Offered": 10
        },
        "statistics": {
            "avg_time_to_screen": 2.5,
            "conversion_rate": 0.15
        }
    },
    "interviews": {
        "total_interviews": 67,
        "by_type": {
            "Phone": 30,
            "Technical": 25,
            "Behavioral": 12
        },
        "completion_rates": {
            "completed": 59,
            "pending": 8,
            "completion_rate": 0.88
        }
    },
    "comprehensive": {
        "applications": 156,
        "interviews": 67,
        "offers": 18,
        "hired": 12,
        "statistics": {
            "avg_time_to_hire": 25.5,
            "offer_acceptance_rate": 0.67
        }
    }
}

def test_pdf_generation():
    """Test PDF generation for all report types"""
    print("Testing PDF generation...")
    
    for report_type, data in test_data.items():
        try:
            # Save test PDF
            filename = f"test_{report_type}_report.pdf"
            pdf_content = generate_pdf_report(
                report_data=data,
                report_type=report_type,
                filename=filename
            )
            
            with open(filename, "wb") as f:
                f.write(pdf_content)
            
            print(f"✅ {report_type} report PDF generated successfully ({len(pdf_content)} bytes)")
            
        except Exception as e:
            print(f"❌ Error generating {report_type} PDF: {e}")
    
    print("\nPDF generation test complete!")

if __name__ == "__main__":
    test_pdf_generation()
