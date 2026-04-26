"""
Clear all applicant/application/communication/evaluation/interview data
while preserving jobs, assessments, and assessment questions.
"""
import sqlite3

DB = "resumes.db"
conn = sqlite3.connect(DB, timeout=10)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA busy_timeout=5000")

tables_to_clear = [
    "ai_screening_results",
    "communications",
    "documents",
    "evaluations",
    "interviews",
    "job_offers",
    "offer_letters",
    "resume_scores",
    "assessment_invites",
    "assessment_results",
    "contact_messages",
    "job_applications",
    "applicants",
    "reports",
    "scheduled_reports",
]

print("Clearing tables...")
for table in tables_to_clear:
    try:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        conn.execute(f"DELETE FROM {table}")
        print(f"  [OK] {table}: removed {count} rows")
    except Exception as e:
        print(f"  [ERROR] {table}: {e}")

conn.commit()

# Verify kept data
jobs = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
assessments = conn.execute("SELECT COUNT(*) FROM assessments").fetchone()[0]
questions = conn.execute("SELECT COUNT(*) FROM assessment_questions").fetchone()[0]
applicants = conn.execute("SELECT COUNT(*) FROM applicants").fetchone()[0]
applications = conn.execute("SELECT COUNT(*) FROM job_applications").fetchone()[0]

conn.close()

print("\n[SUCCESS] Cleanup complete!")
print(f"   Jobs kept:                {jobs}")
print(f"   Assessments kept:         {assessments}")
print(f"   Assessment questions kept: {questions}")
print(f"   Applicants remaining:     {applicants}")
print(f"   Applications remaining:   {applications}")
