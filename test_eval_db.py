import sqlite3
from database import ResumeDatabase

# Test the database connection and query
db = ResumeDatabase()
try:
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    # Check if evaluations table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='evaluations'")
    table_exists = cursor.fetchone()
    print(f'Evaluations table exists: {table_exists is not None}')
    
    if table_exists:
        # Check table structure
        cursor.execute('PRAGMA table_info(evaluations)')
        columns = cursor.fetchall()
        print('Table columns:')
        for col in columns:
            print(f'  {col}')
        
        # Test the query
        cursor.execute('''
            SELECT 
                e.*,
                a.name as applicant_name,
                a.email as applicant_email,
                j.title as job_title,
                ja.application_date
            FROM evaluations e
            JOIN job_applications ja ON e.application_id = ja.id
            JOIN applicants a ON ja.applicant_id = a.id
            JOIN jobs j ON ja.job_id = j.id
            WHERE e.overall_score IS NOT NULL
            ORDER BY e.evaluation_date DESC
            LIMIT 5
        ''')
        
        results = cursor.fetchall()
        print(f'Query returned {len(results)} results')
        if results:
            columns = [desc[0] for desc in cursor.description]
            print('Sample result:')
            for i, result in enumerate(results[:1]):
                print(f'  {dict(zip(columns, result))}')
    
    conn.close()
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
