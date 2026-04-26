from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os

class ResumeCVGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup professional resume styles"""
        # Name style
        if 'NameStyle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='NameStyle',
                parent=self.styles['Heading1'],
                fontSize=24,
                spaceAfter=10,
                textColor=colors.HexColor("#2D3748"),
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ))
        
        # Contact info style
        if 'ContactStyle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='ContactStyle',
                parent=self.styles['Normal'],
                fontSize=10,
                spaceAfter=20,
                textColor=colors.HexColor("#718096"),
                alignment=TA_CENTER
            ))
        
        # Section Header style
        if 'SectionHeader' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SectionHeader',
                parent=self.styles['Heading2'],
                fontSize=14,
                spaceBefore=15,
                spaceAfter=10,
                textColor=colors.HexColor("#3B5BDB"),
                borderWidth=0,
                borderBottomWidth=1,
                borderColor=colors.HexColor("#E2E8F0")
            ))
        
        # Job Title style
        if 'JobTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='JobTitle',
                parent=self.styles['Heading3'],
                fontSize=12,
                textColor=colors.HexColor("#2D3748"),
                fontName='Helvetica-Bold'
            ))
        
        # Normal Text style
        if 'BodyText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='BodyText',
                parent=self.styles['Normal'],
                fontSize=10,
                leading=14,
                textColor=colors.HexColor("#4A5568")
            ))

    def generate_resume(self, data, output_path, score=None):
        """
        data = { ... }
        score = float (e.g. 85.5)
        """
        doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
        story = []
        
        # Header
        story.append(Paragraph(data['name'], self.styles['NameStyle']))
        story.append(Paragraph(data['contact'], self.styles['ContactStyle']))
        
        # Score Badge (if provided)
        if score is not None:
            score_color = "#27AE60" if score >= 70 else "#EB5757"
            score_html = f'<font color="{score_color}" size="14"><b>EXPECTED AI SCORE: {score:.1f}/100</b></font>'
            story.append(Paragraph(score_html, ParagraphStyle(name='ScoreStyle', parent=self.styles['Normal'], alignment=TA_CENTER, spaceAfter=20)))

        # Professional Summary
        story.append(Paragraph("PROFESSIONAL SUMMARY", self.styles['SectionHeader']))
        story.append(Paragraph(data['summary'], self.styles['BodyText']))
        
        # Core Skills
        story.append(Paragraph("TECHNICAL SKILLS", self.styles['SectionHeader']))
        skills_text = ", ".join(data['skills'])
        story.append(Paragraph(skills_text, self.styles['BodyText']))
        
        # Experience
        story.append(Paragraph("WORK EXPERIENCE", self.styles['SectionHeader']))
        for exp in data['experience']:
            story.append(Paragraph(f"<b>{exp['title']}</b> | {exp['company']}", self.styles['JobTitle']))
            story.append(Paragraph(f"<i>{exp['period']}</i>", self.styles['BodyText']))
            story.append(Paragraph(exp['desc'], self.styles['BodyText']))
            story.append(Spacer(1, 10))
            
        # Certifications
        if data.get('certifications'):
            story.append(Paragraph("CERTIFICATIONS", self.styles['SectionHeader']))
            cert_text = " • " + " • ".join(data['certifications'])
            story.append(Paragraph(cert_text, self.styles['BodyText']))
            
        # Education
        story.append(Paragraph("EDUCATION", self.styles['SectionHeader']))
        for edu in data['education']:
            story.append(Paragraph(f"<b>{edu['degree']}</b>, {edu['school']}", self.styles['BodyText']))
            story.append(Paragraph(f"{edu['year']}", self.styles['BodyText']))
            story.append(Spacer(1, 5))
            
        doc.build(story)
        return output_path

if __name__ == "__main__":
    # Test generation
    generator = ResumeCVGenerator()
    test_data = {
        'name': 'Alex Johnson',
        'contact': 'alex.j@example.com | +44 7700 900000 | London, UK',
        'summary': 'Highly skilled Software Engineer with over 8 years of experience in full-stack development. Expert in Python, JavaScript, and Cloud Architecture.',
        'skills': ['Python', 'JavaScript', 'React', 'Node.js', 'AWS', 'Docker', 'SQL'],
        'experience': [
            {
                'title': 'Senior Software Engineer',
                'company': 'CloudScale Solutions',
                'period': '2020 - Present',
                'desc': 'Architected and implemented scalable microservices using Python and AWS. Reduced latency by 40% through database optimization.'
            },
            {
                'title': 'Software Developer',
                'company': 'DataStream Inc.',
                'period': '2016 - 2020',
                'desc': 'Developed real-time data processing pipelines. Collaborated with cross-functional teams to deliver high-quality software.'
            }
        ],
        'education': [
            {'degree': 'Master of Science in Computer Science', 'school': 'University of Oxford', 'year': '2016'}
        ],
        'certifications': ['AWS Solutions Architect Professional', 'ServiceNow Certified System Administrator (CSA)']
    }
    
    os.makedirs('generated_cvs', exist_ok=True)
    generator.generate_resume(test_data, 'generated_cvs/test_resume.pdf')
    print("Test resume generated successfully!")
