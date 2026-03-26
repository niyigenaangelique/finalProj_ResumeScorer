from database import ResumeDatabase

# Initialize database
db = ResumeDatabase()

# Sample jobs data
sample_jobs = [
    {
        "title": "Senior Software Engineer",
        "department": "Engineering",
        "location": "San Francisco, CA",
        "salary": "$120,000 - $150,000",
        "job_type": "Full-time",
        "description": "We are looking for an experienced Senior Software Engineer to join our growing team. You will be responsible for developing and maintaining high-quality software solutions, mentoring junior engineers, and contributing to technical architecture decisions. The ideal candidate has strong experience in modern web technologies and a passion for building scalable applications.",
        "requirements": "5+ years of software development experience, proficiency in Python/JavaScript, experience with cloud platforms, strong problem-solving skills, and excellent communication abilities."
    },
    {
        "title": "Product Manager",
        "department": "Product",
        "location": "New York, NY",
        "salary": "$100,000 - $130,000",
        "job_type": "Full-time",
        "description": "Join our Product team as a Product Manager where you'll drive product strategy and development. You'll work closely with engineering, design, and marketing teams to deliver innovative products that delight our customers. This role requires strong analytical skills, business acumen, and the ability to translate user needs into product requirements.",
        "requirements": "3+ years of product management experience, strong analytical and communication skills, experience with agile development, and a track record of shipping successful products."
    },
    {
        "title": "UX Designer",
        "department": "Design",
        "location": "Remote",
        "salary": "$80,000 - $110,000",
        "job_type": "Full-time",
        "description": "We're seeking a talented UX Designer to create intuitive and beautiful user experiences. You'll be responsible for user research, wireframing, prototyping, and working with developers to bring designs to life. The ideal candidate has a strong portfolio and experience with modern design tools.",
        "requirements": "3+ years of UX design experience, proficiency in Figma/Sketch, strong understanding of user-centered design principles, and excellent collaboration skills."
    },
    {
        "title": "Data Analyst",
        "department": "Analytics",
        "location": "Boston, MA",
        "salary": "$70,000 - $95,000",
        "job_type": "Full-time",
        "description": "Looking for a detail-oriented Data Analyst to help us make data-driven decisions. You'll analyze complex datasets, create reports and dashboards, and work with stakeholders to provide actionable insights. Experience with SQL and data visualization tools is essential.",
        "requirements": "2+ years of data analysis experience, strong SQL skills, experience with Tableau/Power BI, and the ability to communicate complex findings to non-technical audiences."
    },
    {
        "title": "Marketing Manager",
        "department": "Marketing",
        "location": "Los Angeles, CA",
        "salary": "$85,000 - $115,000",
        "job_type": "Full-time",
        "description": "We need a creative Marketing Manager to develop and execute marketing strategies that drive growth. You'll oversee digital marketing campaigns, manage marketing budgets, and collaborate with sales and product teams. Strong experience with digital marketing channels and analytics is required.",
        "requirements": "4+ years of marketing experience, expertise in digital marketing, strong analytical skills, and experience with marketing automation tools."
    },
    {
        "title": "DevOps Engineer",
        "department": "Engineering",
        "location": "Seattle, WA",
        "salary": "$110,000 - $140,000",
        "job_type": "Full-time",
        "description": "Join our infrastructure team as a DevOps Engineer to build and maintain scalable systems. You'll work with cloud infrastructure, CI/CD pipelines, and automation tools. The role requires strong technical skills and the ability to ensure high availability and performance of our services.",
        "requirements": "3+ years of DevOps experience, strong knowledge of AWS/Azure, experience with Docker/Kubernetes, and proficiency in scripting languages."
    }
]

print("Adding sample jobs to the database...")

# Add each job to the database
for i, job_data in enumerate(sample_jobs, 1):
    try:
        job_id = db.add_job(
            title=job_data["title"],
            department=job_data["department"],
            location=job_data["location"],
            salary=job_data["salary"],
            description=job_data["description"],
            requirements=job_data["requirements"]
        )
        print(f"✅ Added job {i}: {job_data['title']} (ID: {job_id})")
    except Exception as e:
        print(f"❌ Error adding job {i}: {e}")

print("\nJob population completed!")

# Verify the jobs were added
jobs = db.get_all_jobs()
print(f"\nTotal jobs in database: {len(jobs)}")
for job in jobs:
    print(f"- {job['title']} ({job['department']})")
