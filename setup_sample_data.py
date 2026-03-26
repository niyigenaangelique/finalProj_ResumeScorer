from database import ResumeDatabase

def setup_sample_data():
    """Create sample job postings"""
    db = ResumeDatabase()
    
    # Add sample jobs
    jobs = [
        {
            'title': 'Senior Software Engineer',
            'department': 'Engineering',
            'location': 'San Francisco, CA',
            'salary': '$120,000 - $150,000',
            'description': 'We are looking for a Senior Software Engineer to join our growing engineering team. You will be responsible for developing scalable web applications, mentoring junior developers, and contributing to technical architecture decisions.',
            'requirements': '5+ years of experience in software development, proficiency in Python, JavaScript, and cloud technologies. Experience with microservices architecture preferred.'
        },
        {
            'title': 'Data Analyst',
            'department': 'Analytics',
            'location': 'New York, NY',
            'salary': '$80,000 - $100,000',
            'description': 'Join our data analytics team to help drive business insights through data analysis and visualization. You will work with large datasets and create reports for stakeholders.',
            'requirements': '3+ years of experience in data analysis, strong SQL skills, experience with Tableau or Power BI, and excellent communication skills.'
        },
        {
            'title': 'Product Manager',
            'department': 'Product',
            'location': 'Remote',
            'salary': '$110,000 - $140,000',
            'description': 'We are seeking a Product Manager to lead product strategy and development. You will work closely with engineering, design, and marketing teams to deliver exceptional products.',
            'requirements': '4+ years of product management experience, strong analytical skills, experience with agile methodologies, and excellent leadership abilities.'
        },
        {
            'title': 'UX Designer',
            'department': 'Design',
            'location': 'Austin, TX',
            'salary': '$90,000 - $120,000',
            'description': 'Create beautiful and intuitive user experiences for our web and mobile applications. You will work with product managers and engineers to bring designs to life.',
            'requirements': '3+ years of UX design experience, proficiency in Figma and Adobe Creative Suite, strong portfolio demonstrating user-centered design process.'
        },
        {
            'title': 'DevOps Engineer',
            'department': 'Engineering',
            'location': 'Seattle, WA',
            'salary': '$100,000 - $130,000',
            'description': 'Help us build and maintain our cloud infrastructure. You will be responsible for CI/CD pipelines, monitoring, and ensuring high availability of our services.',
            'requirements': '4+ years of DevOps experience, strong knowledge of AWS/Azure/GCP, experience with Docker and Kubernetes, and scripting skills.'
        }
    ]
    
    print("Adding sample jobs...")
    for job in jobs:
        job_id = db.add_job(**job)
        print(f"Added job: {job['title']} (ID: {job_id})")
    
    print(f"\nTotal jobs added: {len(jobs)}")
    print("\nJob portal is ready with sample data!")

if __name__ == "__main__":
    setup_sample_data()
