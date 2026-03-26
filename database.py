import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

class ResumeDatabase:
    def __init__(self, db_path="resumes.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create applicants table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applicants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                position TEXT,
                department TEXT,
                application_date TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                department TEXT,
                location TEXT,
                salary TEXT,
                description TEXT,
                requirements TEXT,
                posted_date TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # Create job_applications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                applicant_id INTEGER,
                cover_letter TEXT,
                application_date TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (job_id) REFERENCES jobs (id),
                FOREIGN KEY (applicant_id) REFERENCES applicants (id)
            )
        ''')
        
        # Create resume_scores table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resume_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                applicant_id INTEGER,
                resume_text TEXT,
                score REAL,
                features TEXT,
                recommendations TEXT,
                filename TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (applicant_id) REFERENCES applicants (id)
            )
        ''')
        
        # Create documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                applicant_id INTEGER,
                document_type TEXT,
                filename TEXT,
                file_path TEXT,
                file_size INTEGER,
                upload_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (applicant_id) REFERENCES applicants (id)
            )
        ''')
        
        # Create interviews table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER,
                interview_type TEXT,
                scheduled_date TEXT,
                scheduled_time TEXT,
                duration INTEGER,
                interviewer_name TEXT,
                interview_mode TEXT,
                meeting_link TEXT,
                location TEXT,
                status TEXT DEFAULT 'scheduled',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (application_id) REFERENCES job_applications (id)
            )
        ''')
        
        # Create evaluations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER,
                interviewer_name TEXT,
                technical_score INTEGER,
                communication_score INTEGER,
                experience_score INTEGER,
                overall_score INTEGER,
                strengths TEXT,
                weaknesses TEXT,
                comments TEXT,
                recommendation TEXT,
                evaluation_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (application_id) REFERENCES job_applications (id)
            )
        ''')
        
        # Create communications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS communications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER,
                sender_type TEXT,
                recipient_email TEXT,
                subject TEXT,
                message TEXT,
                message_type TEXT,
                status TEXT DEFAULT 'sent',
                sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (application_id) REFERENCES job_applications (id)
            )
        ''')
        
        # Create offer_letters table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS offer_letters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER,
                offer_type TEXT,
                salary TEXT,
                start_date TEXT,
                position TEXT,
                department TEXT,
                reporting_to TEXT,
                benefits TEXT,
                terms TEXT,
                status TEXT DEFAULT 'draft',
                sent_date TEXT,
                response_date TEXT,
                response_status TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (application_id) REFERENCES job_applications (id)
            )
        ''')
        
        # Create job_offers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER,
                position_title TEXT,
                department TEXT,
                salary TEXT,
                start_date TEXT,
                location TEXT,
                reporting_to TEXT,
                offer_type TEXT,
                benefits TEXT,
                offer_details TEXT,
                response_deadline TEXT,
                status TEXT DEFAULT 'pending',
                created_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (application_id) REFERENCES job_applications (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_applicant(self, name: str, email: str = None, phone: str = None, 
                    position: str = None, department: str = None) -> int:
        """Add a new applicant"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO applicants (name, email, phone, position, department, application_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, email, phone, position, department, datetime.now().isoformat()))
        
        applicant_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return applicant_id
    
    def save_resume_score(self, applicant_id: int, resume_text: str, score: float, 
                        features: Dict, recommendations: List[str], filename: str = None) -> int:
        """Save resume score and analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO resume_scores 
            (applicant_id, resume_text, score, features, recommendations, filename)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (applicant_id, resume_text, score, json.dumps(features), 
               json.dumps(recommendations), filename))
        
        score_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return score_id
    
    def get_applicant_with_score(self, applicant_id: int) -> Optional[Dict]:
        """Get applicant details with their latest resume score"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, rs.score, rs.features, rs.recommendations, rs.filename, rs.created_at as score_date
            FROM applicants a
            LEFT JOIN resume_scores rs ON a.id = rs.applicant_id
            WHERE a.id = ?
            ORDER BY rs.created_at DESC
            LIMIT 1
        ''', (applicant_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = ['id', 'name', 'email', 'phone', 'position', 'department', 
                      'application_date', 'status', 'created_at', 'score', 'features', 
                      'recommendations', 'filename', 'score_date']
            
            applicant = dict(zip(columns, result))
            
            # Parse JSON fields
            if applicant['features']:
                applicant['features'] = json.loads(applicant['features'])
            if applicant['recommendations']:
                applicant['recommendations'] = json.loads(applicant['recommendations'])
            
            return applicant
        
        return None
    
    def get_all_applicants_with_scores(self) -> List[Dict]:
        """Get all applicants with their latest resume scores"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, rs.score, rs.filename, rs.created_at as score_date
            FROM applicants a
            LEFT JOIN resume_scores rs ON a.id = rs.applicant_id
            LEFT JOIN (
                SELECT applicant_id, MAX(created_at) as max_date
                FROM resume_scores
                GROUP BY applicant_id
            ) latest ON a.id = latest.applicant_id AND rs.created_at = latest.max_date
            ORDER BY rs.score DESC, a.application_date DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        applicants = []
        columns = ['id', 'name', 'email', 'phone', 'position', 'department', 
                  'application_date', 'status', 'created_at', 'score', 'filename', 'score_date']
        
        for result in results:
            applicant = dict(zip(columns, result))
            applicants.append(applicant)
        
        return applicants
    
    def update_applicant_status(self, applicant_id: int, status: str) -> bool:
        """Update applicant status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE applicants SET status = ? WHERE id = ?
        ''', (status, applicant_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def search_applicants(self, query: str) -> List[Dict]:
        """Search applicants by name, email, or position"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        search_pattern = f'%{query}%'
        
        cursor.execute('''
            SELECT a.*, rs.score, rs.filename, rs.created_at as score_date
            FROM applicants a
            LEFT JOIN resume_scores rs ON a.id = rs.applicant_id
            LEFT JOIN (
                SELECT applicant_id, MAX(created_at) as max_date
                FROM resume_scores
                GROUP BY applicant_id
            ) latest ON a.id = latest.applicant_id AND rs.created_at = latest.max_date
            WHERE a.name LIKE ? OR a.email LIKE ? OR a.position LIKE ?
            ORDER BY rs.score DESC, a.application_date DESC
        ''', (search_pattern, search_pattern, search_pattern))
        
        results = cursor.fetchall()
        conn.close()
        
        applicants = []
        columns = ['id', 'name', 'email', 'phone', 'position', 'department', 
                  'application_date', 'status', 'created_at', 'score', 'filename', 'score_date']
        
        for result in results:
            applicant = dict(zip(columns, result))
            applicants.append(applicant)
        
        return applicants
    
    def add_job(self, title: str, department: str, location: str = None, 
               salary: str = None, description: str = "", requirements: str = "") -> int:
        """Add a new job posting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO jobs (title, department, location, salary, description, requirements)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, department, location, salary, description, requirements))
        
        job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return job_id
    
    def get_all_jobs(self) -> List[Dict]:
        """Get all active jobs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM jobs WHERE status = 'active' ORDER BY posted_date DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'title', 'department', 'location', 'salary', 
                  'description', 'requirements', 'posted_date', 'status']
        
        jobs = []
        for result in results:
            job = dict(zip(columns, result))
            jobs.append(job)
        
        return jobs
    
    def get_job(self, job_id: int) -> Optional[Dict]:
        """Get a specific job"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = ['id', 'title', 'department', 'location', 'salary', 
                      'description', 'requirements', 'posted_date', 'status']
            return dict(zip(columns, result))
        
        return None
    
    def update_job(self, job_id: int, title: str = None, department: str = None, 
                   location: str = None, salary: str = None, description: str = None, 
                   requirements: str = None, status: str = None) -> bool:
        """Update an existing job"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if department is not None:
            updates.append("department = ?")
            params.append(department)
        if location is not None:
            updates.append("location = ?")
            params.append(location)
        if salary is not None:
            updates.append("salary = ?")
            params.append(salary)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if requirements is not None:
            updates.append("requirements = ?")
            params.append(requirements)
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        
        if updates:
            params.append(job_id)
            cursor.execute(f'''
                UPDATE jobs 
                SET {', '.join(updates)}
                WHERE id = ?
            ''', params)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_job(self, job_id: int) -> bool:
        """Delete a job (and related applications)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # First delete related applications
            cursor.execute('DELETE FROM job_applications WHERE job_id = ?', (job_id,))
            
            # Then delete the job
            cursor.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return success
        except Exception as e:
            conn.close()
            raise e

    def add_job_application(self, job_id: int, applicant_id: int, cover_letter: str = "") -> int:
        """Add a job application"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO job_applications (job_id, applicant_id, cover_letter)
            VALUES (?, ?, ?)
        ''', (job_id, applicant_id, cover_letter))
        
        application_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return application_id
    
    def get_all_applications(self) -> List[Dict]:
        """Get all job applications with job and applicant details"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                ja.*,
                j.title as job_title,
                j.department,
                a.name as applicant_name,
                a.email as applicant_email,
                rs.score as resume_score
            FROM job_applications ja
            JOIN jobs j ON ja.job_id = j.id
            JOIN applicants a ON ja.applicant_id = a.id
            LEFT JOIN resume_scores rs ON a.id = rs.applicant_id
            ORDER BY ja.application_date DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'job_id', 'applicant_id', 'cover_letter', 'application_date', 'status',
                  'job_title', 'department', 'applicant_name', 'applicant_email', 'resume_score']
        
        applications = []
        for result in results:
            app = dict(zip(columns, result))
            applications.append(app)
        
        return applications
    
    def update_application_status(self, application_id: int, status: str) -> bool:
        """Update application status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE job_applications SET status = ? WHERE id = ?
        ''', (status, application_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_statistics(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total applicants
        cursor.execute('SELECT COUNT(*) FROM applicants')
        total_applicants = cursor.fetchone()[0]
        
        # Applicants with scores
        cursor.execute('SELECT COUNT(DISTINCT applicant_id) FROM resume_scores')
        scored_applicants = cursor.fetchone()[0]
        
        # Average score
        cursor.execute('SELECT AVG(score) FROM resume_scores')
        avg_score = cursor.fetchone()[0] or 0
        
        # Score distribution
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN score >= 80 THEN 'Excellent'
                    WHEN score >= 60 THEN 'Good'
                    WHEN score >= 40 THEN 'Fair'
                    ELSE 'Poor'
                END as category,
                COUNT(*) as count
            FROM resume_scores
            GROUP BY category
        ''')
        
        score_distribution = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_applicants': total_applicants,
            'scored_applicants': scored_applicants,
            'average_score': round(avg_score, 1),
            'score_distribution': score_distribution
        }
    
    # Interview scheduling methods
    def add_interview(self, application_id: int, interview_type: str, scheduled_date: str, 
                     scheduled_time: str, duration: int, interviewer_name: str, 
                     interview_mode: str, meeting_link: str = None, location: str = None, 
                     notes: str = None) -> int:
        """Add a new interview"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO interviews 
            (application_id, interview_type, scheduled_date, scheduled_time, duration, 
             interviewer_name, interview_mode, meeting_link, location, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (application_id, interview_type, scheduled_date, scheduled_time, duration,
              interviewer_name, interview_mode, meeting_link, location, notes))
        
        interview_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return interview_id
    
    def schedule_interview(self, application_id: int, interview_type: str, interview_date: str, 
                          interview_time: str, duration: int, interviewer_name: str, 
                          interview_mode: str, meeting_link: str = None, location: str = None, 
                          notes: str = None) -> int:
        """Schedule a new interview (alias for add_interview)"""
        return self.add_interview(
            application_id=application_id,
            interview_type=interview_type,
            scheduled_date=interview_date,
            scheduled_time=interview_time,
            duration=duration,
            interviewer_name=interviewer_name,
            interview_mode=interview_mode,
            meeting_link=meeting_link,
            location=location,
            notes=notes
        )
    
    def get_interviews(self, application_id: int = None) -> List[Dict]:
        """Get interviews, optionally filtered by application_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if application_id:
            cursor.execute('''
                SELECT i.*, ja.applicant_id, a.name as applicant_name, a.email as applicant_email,
                       j.title as job_title
                FROM interviews i
                JOIN job_applications ja ON i.application_id = ja.id
                JOIN applicants a ON ja.applicant_id = a.id
                JOIN jobs j ON ja.job_id = j.id
                WHERE i.application_id = ?
                ORDER BY i.scheduled_date, i.scheduled_time
            ''', (application_id,))
        else:
            cursor.execute('''
                SELECT i.*, ja.applicant_id, a.name as applicant_name, a.email as applicant_email,
                       j.title as job_title
                FROM interviews i
                JOIN job_applications ja ON i.application_id = ja.id
                JOIN applicants a ON ja.applicant_id = a.id
                JOIN jobs j ON ja.job_id = j.id
                ORDER BY i.scheduled_date, i.scheduled_time
            ''')
        
        results = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'application_id', 'interview_type', 'scheduled_date', 'scheduled_time',
                  'duration', 'interviewer_name', 'interview_mode', 'meeting_link', 'location',
                  'status', 'notes', 'created_at', 'applicant_id', 'applicant_name', 
                  'applicant_email', 'job_title']
        
        interviews = []
        for result in results:
            interview = dict(zip(columns, result))
            interviews.append(interview)
        
        return interviews
    
    def update_interview_status(self, interview_id: int, status: str) -> bool:
        """Update interview status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE interviews SET status = ? WHERE id = ?
        ''', (status, interview_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def cancel_interview(self, interview_id: int) -> bool:
        """Cancel an interview (update status to cancelled)"""
        return self.update_interview_status(interview_id, 'cancelled')

    # Evaluation methods
    def add_evaluation(self, application_id: int, interviewer_name: str, technical_score: int,
                      communication_score: int, experience_score: int, overall_score: int,
                      strengths: str, weaknesses: str, comments: str, recommendation: str) -> int:
        """Add a candidate evaluation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO evaluations 
            (application_id, interviewer_name, technical_score, communication_score, 
             experience_score, overall_score, strengths, weaknesses, comments, recommendation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (application_id, interviewer_name, technical_score, communication_score,
              experience_score, overall_score, strengths, weaknesses, comments, recommendation))
        
        evaluation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return evaluation_id
    
    def get_evaluations(self, application_id: int = None) -> List[Dict]:
        """Get evaluations, optionally filtered by application_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if application_id:
            cursor.execute('''
                SELECT e.*, ja.applicant_id, a.name as applicant_name, a.email as applicant_email,
                       j.title as job_title
                FROM evaluations e
                JOIN job_applications ja ON e.application_id = ja.id
                JOIN applicants a ON ja.applicant_id = a.id
                JOIN jobs j ON ja.job_id = j.id
                WHERE e.application_id = ?
                ORDER BY e.evaluation_date DESC
            ''', (application_id,))
        else:
            cursor.execute('''
                SELECT e.*, ja.applicant_id, a.name as applicant_name, a.email as applicant_email,
                       j.title as job_title
                FROM evaluations e
                JOIN job_applications ja ON e.application_id = ja.id
                JOIN applicants a ON ja.applicant_id = a.id
                JOIN jobs j ON ja.job_id = j.id
                ORDER BY e.evaluation_date DESC
            ''')
        
        results = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'application_id', 'interviewer_name', 'technical_score', 'communication_score',
                  'experience_score', 'overall_score', 'strengths', 'weaknesses', 'comments',
                  'recommendation', 'evaluation_date', 'applicant_id', 'applicant_name',
                  'applicant_email', 'job_title']
        
        evaluations = []
        for result in results:
            evaluation = dict(zip(columns, result))
            evaluations.append(evaluation)
        
        return evaluations
    
    # Communication methods
    def add_communication(self, application_id: int, sender_type: str, recipient_email: str,
                         subject: str, message: str, message_type: str) -> int:
        """Add a communication record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO communications 
            (application_id, sender_type, recipient_email, subject, message, message_type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (application_id, sender_type, recipient_email, subject, message, message_type))
        
        comm_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return comm_id
    
    def get_communications(self, application_id: int = None) -> List[Dict]:
        """Get communications, optionally filtered by application_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if application_id:
                cursor.execute('''
                    SELECT c.*, ja.applicant_id, a.name as applicant_name, j.title as job_title
                    FROM communications c
                    LEFT JOIN job_applications ja ON c.application_id = ja.id
                    LEFT JOIN applicants a ON ja.applicant_id = a.id
                    LEFT JOIN jobs j ON ja.job_id = j.id
                    WHERE c.application_id = ?
                    ORDER BY c.sent_at DESC
                ''', (application_id,))
            else:
                cursor.execute('''
                    SELECT c.*, ja.applicant_id, a.name as applicant_name, j.title as job_title
                    FROM communications c
                    LEFT JOIN job_applications ja ON c.application_id = ja.id
                    LEFT JOIN applicants a ON ja.applicant_id = a.id
                    LEFT JOIN jobs j ON ja.job_id = j.id
                    ORDER BY c.sent_at DESC
                ''')
            
            results = cursor.fetchall()
            
            # If no results, return empty list
            if not results:
                return []
            
            columns = ['id', 'application_id', 'sender_type', 'recipient_email', 'subject',
                      'message', 'message_type', 'status', 'sent_at', 'applicant_id',
                      'applicant_name', 'job_title']
            
            communications = []
            for result in results:
                comm = dict(zip(columns, result))
                communications.append(comm)
            
            return communications
            
        except Exception as e:
            print(f"Database error in get_communications: {e}")
            return []
        finally:
            conn.close()
    
    # Offer letter methods
    def add_offer_letter(self, application_id: int, offer_type: str, salary: str, start_date: str,
                        position: str, department: str, reporting_to: str, benefits: str,
                        terms: str) -> int:
        """Add an offer letter"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO offer_letters 
            (application_id, offer_type, salary, start_date, position, department, 
             reporting_to, benefits, terms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (application_id, offer_type, salary, start_date, position, department,
              reporting_to, benefits, terms))
        
        offer_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return offer_id
    
    def get_offer_letters(self, application_id: int = None) -> List[Dict]:
        """Get offer letters, optionally filtered by application_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if application_id:
            cursor.execute('''
                SELECT o.*, ja.applicant_id, a.name as applicant_name, a.email as applicant_email,
                       j.title as job_title
                FROM offer_letters o
                JOIN job_applications ja ON o.application_id = ja.id
                JOIN applicants a ON ja.applicant_id = a.id
                JOIN jobs j ON ja.job_id = j.id
                WHERE o.application_id = ?
                ORDER BY o.created_at DESC
            ''', (application_id,))
        else:
            cursor.execute('''
                SELECT o.*, ja.applicant_id, a.name as applicant_name, a.email as applicant_email,
                       j.title as job_title
                FROM offer_letters o
                JOIN job_applications ja ON o.application_id = ja.id
                JOIN applicants a ON ja.applicant_id = a.id
                JOIN jobs j ON ja.job_id = j.id
                ORDER BY o.created_at DESC
            ''')
        
        results = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'application_id', 'offer_type', 'salary', 'start_date', 'position',
                  'department', 'reporting_to', 'benefits', 'terms', 'status', 'sent_date',
                  'response_date', 'response_status', 'created_at', 'applicant_id',
                  'applicant_name', 'applicant_email', 'job_title']
        
        offers = []
        for result in results:
            offer = dict(zip(columns, result))
            offers.append(offer)
        
        return offers
    
    def update_offer_status(self, offer_id: int, status: str, response_date: str = None,
                           response_status: str = None) -> bool:
        """Update offer letter status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE offer_letters 
            SET status = ?, sent_date = COALESCE(sent_date, ?), 
                response_date = ?, response_status = ?
            WHERE id = ?
        ''', (status, datetime.now().isoformat() if status == 'sent' else None,
              response_date, response_status, offer_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    # Application tracker for applicants
    def get_applications_by_email(self, email: str) -> List[Dict]:
        """Get all applications for a specific email"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                ja.*,
                j.title as job_title,
                j.department,
                j.location,
                j.salary as job_salary,
                rs.score as resume_score,
                i.id as interview_id,
                i.scheduled_date,
                i.scheduled_time,
                i.status as interview_status,
                e.id as evaluation_id,
                e.overall_score,
                o.id as offer_id,
                o.status as offer_status,
                o.offer_type,
                o.salary as offer_salary,
                o.start_date as offer_start_date,
                o.position as offer_position,
                o.department as offer_department
            FROM job_applications ja
            JOIN jobs j ON ja.job_id = j.id
            JOIN applicants a ON ja.applicant_id = a.id
            LEFT JOIN resume_scores rs ON a.id = rs.applicant_id
            LEFT JOIN interviews i ON ja.id = i.application_id
            LEFT JOIN evaluations e ON ja.id = e.application_id
            LEFT JOIN offer_letters o ON ja.id = o.application_id
            WHERE a.email = ?
            ORDER BY ja.application_date DESC
        ''', (email,))
        
        results = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'job_id', 'applicant_id', 'cover_letter', 'application_date', 'status',
                  'job_title', 'department', 'location', 'job_salary', 'resume_score',
                  'interview_id', 'scheduled_date', 'scheduled_time', 'interview_status',
                  'evaluation_id', 'overall_score', 'offer_id', 'offer_status', 'offer_type',
                  'offer_salary', 'offer_start_date', 'offer_position', 'offer_department']
        
        applications = []
        for result in results:
            app = dict(zip(columns, result))
            applications.append(app)
        
        return applications

    def get_application_by_id(self, application_id: int) -> Dict:
        """Get a single application by ID with applicant and job details"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                ja.*,
                j.title as job_title,
                j.department,
                a.name as applicant_name,
                a.email as applicant_email,
                rs.score as resume_score
            FROM job_applications ja
            JOIN jobs j ON ja.job_id = j.id
            JOIN applicants a ON ja.applicant_id = a.id
            LEFT JOIN resume_scores rs ON a.id = rs.applicant_id
            WHERE ja.id = ?
        ''', (application_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = ['id', 'job_id', 'applicant_id', 'cover_letter', 'application_date', 'status',
                      'job_title', 'department', 'applicant_name', 'applicant_email', 'resume_score']
            return dict(zip(columns, result))
        return None
    
    def get_application_details(self, application_id: int) -> Dict:
        """Get application details (alias for get_application_by_id)"""
        return self.get_application_by_id(application_id)
    
    def get_applicant_documents(self, applicant_id: int) -> List[Dict]:
        """Get all documents for an applicant"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM documents 
            WHERE applicant_id = ?
            ORDER BY upload_date DESC
        ''', (applicant_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        if results:
            columns = ['id', 'applicant_id', 'document_type', 'filename', 'file_path', 'file_size', 'upload_date']
            return [dict(zip(columns, result)) for result in results]
        
        return []
    
    def get_document_by_id(self, document_id: int) -> Dict:
        """Get a specific document by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM documents WHERE id = ?', (document_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = ['id', 'applicant_id', 'document_type', 'filename', 'file_path', 'file_size', 'upload_date']
            return dict(zip(columns, result))
        
        return None

    # Offers management methods for communications
    def update_communication(self, communication_id: int, subject: str = None, 
                           message: str = None, message_type: str = None) -> bool:
        """Update a communication"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if subject is not None:
            updates.append("subject = ?")
            params.append(subject)
        if message is not None:
            updates.append("message = ?")
            params.append(message)
        if message_type is not None:
            updates.append("message_type = ?")
            params.append(message_type)
        
        if updates:
            params.append(communication_id)
            cursor.execute(f'''
                UPDATE communications 
                SET {', '.join(updates)}
                WHERE id = ?
            ''', params)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_communication(self, communication_id: int) -> bool:
        """Delete a communication"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM communications WHERE id = ?', (communication_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success

    # Update and delete methods for offers
    def update_offer_letter(self, offer_id: int, offer_type: str = None, salary: str = None,
                          start_date: str = None, position: str = None, department: str = None,
                          reporting_to: str = None, benefits: str = None, terms: str = None) -> bool:
        """Update an offer letter"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if offer_type is not None:
            updates.append("offer_type = ?")
            params.append(offer_type)
        if salary is not None:
            updates.append("salary = ?")
            params.append(salary)
        if start_date is not None:
            updates.append("start_date = ?")
            params.append(start_date)
        if position is not None:
            updates.append("position = ?")
            params.append(position)
        if department is not None:
            updates.append("department = ?")
            params.append(department)
        if reporting_to is not None:
            updates.append("reporting_to = ?")
            params.append(reporting_to)
        if benefits is not None:
            updates.append("benefits = ?")
            params.append(benefits)
        if terms is not None:
            updates.append("terms = ?")
            params.append(terms)
        
        if updates:
            params.append(offer_id)
            cursor.execute(f'''
                UPDATE offer_letters 
                SET {', '.join(updates)}
                WHERE id = ?
            ''', params)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_offer_letter(self, offer_id: int) -> bool:
        """Delete an offer letter"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM offer_letters WHERE id = ?', (offer_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success

    # Update and delete methods for interviews
    def update_interview(self, interview_id: int, interview_type: str = None,
                        scheduled_date: str = None, scheduled_time: str = None,
                        duration: int = None, interviewer_name: str = None,
                        interview_mode: str = None, meeting_link: str = None,
                        location: str = None, notes: str = None) -> bool:
        """Update an interview"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if interview_type is not None:
            updates.append("interview_type = ?")
            params.append(interview_type)
        if scheduled_date is not None:
            updates.append("scheduled_date = ?")
            params.append(scheduled_date)
        if scheduled_time is not None:
            updates.append("scheduled_time = ?")
            params.append(scheduled_time)
        if duration is not None:
            updates.append("duration = ?")
            params.append(duration)
        if interviewer_name is not None:
            updates.append("interviewer_name = ?")
            params.append(interviewer_name)
        if interview_mode is not None:
            updates.append("interview_mode = ?")
            params.append(interview_mode)
        if meeting_link is not None:
            updates.append("meeting_link = ?")
            params.append(meeting_link)
        if location is not None:
            updates.append("location = ?")
            params.append(location)
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)
        
        if updates:
            params.append(interview_id)
            cursor.execute(f'''
                UPDATE interviews 
                SET {', '.join(updates)}
                WHERE id = ?
            ''', params)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_interview(self, interview_id: int) -> bool:
        """Delete an interview"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM interviews WHERE id = ?', (interview_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success

    # Update and delete methods for evaluations
    def update_evaluation(self, evaluation_id: int, interviewer_name: str = None,
                         technical_score: int = None, communication_score: int = None,
                         experience_score: int = None, overall_score: int = None,
                         strengths: str = None, weaknesses: str = None,
                         comments: str = None, recommendation: str = None) -> bool:
        """Update an evaluation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if interviewer_name is not None:
            updates.append("interviewer_name = ?")
            params.append(interviewer_name)
        if technical_score is not None:
            updates.append("technical_score = ?")
            params.append(technical_score)
        if communication_score is not None:
            updates.append("communication_score = ?")
            params.append(communication_score)
        if experience_score is not None:
            updates.append("experience_score = ?")
            params.append(experience_score)
        if overall_score is not None:
            updates.append("overall_score = ?")
            params.append(overall_score)
        if strengths is not None:
            updates.append("strengths = ?")
            params.append(strengths)
        if weaknesses is not None:
            updates.append("weaknesses = ?")
            params.append(weaknesses)
        if comments is not None:
            updates.append("comments = ?")
            params.append(comments)
        if recommendation is not None:
            updates.append("recommendation = ?")
            params.append(recommendation)
        
        if updates:
            params.append(evaluation_id)
            cursor.execute(f'''
                UPDATE evaluations 
                SET {', '.join(updates)}
                WHERE id = ?
            ''', params)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_evaluation(self, evaluation_id: int) -> bool:
        """Delete an evaluation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM evaluations WHERE id = ?', (evaluation_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    # Offers management methods
    def create_job_offer(self, application_id: int, position_title: str, department: str, 
                        salary: str, start_date: str, location: str, reporting_to: str, 
                        offer_type: str, benefits: str = "", offer_details: str = "", 
                        response_deadline: str = None, created_by: str = None) -> int:
        """Create a new job offer"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO job_offers (
                application_id, position_title, department, salary, start_date, location, 
                reporting_to, offer_type, benefits, offer_details, response_deadline, 
                status, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, CURRENT_TIMESTAMP)
        ''', (application_id, position_title, department, salary, start_date, location, 
              reporting_to, offer_type, benefits, offer_details, response_deadline, created_by))
        
        offer_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return offer_id
    
    def get_all_offers(self) -> List[Dict]:
        """Get all job offers"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT o.*, ja.applicant_id, a.name as applicant_name, a.email as applicant_email,
                   j.title as job_title
            FROM job_offers o
            JOIN job_applications ja ON o.application_id = ja.id
            JOIN applicants a ON ja.applicant_id = a.id
            JOIN jobs j ON ja.job_id = j.id
            ORDER BY o.created_at DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'application_id', 'position_title', 'department', 'salary', 'start_date', 
                  'location', 'reporting_to', 'offer_type', 'benefits', 'offer_details', 
                  'response_deadline', 'status', 'created_by', 'created_at', 'applicant_id', 
                  'applicant_name', 'applicant_email', 'job_title']
        
        offers = []
        for result in results:
            offer = dict(zip(columns, result))
            offers.append(offer)
        
        return offers
    
    def get_offer_details(self, offer_id: int) -> Dict:
        """Get specific offer details"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT o.*, ja.applicant_id, a.name as applicant_name, a.email as applicant_email,
                   j.title as job_title
            FROM job_offers o
            JOIN job_applications ja ON o.application_id = ja.id
            JOIN applicants a ON ja.applicant_id = a.id
            JOIN jobs j ON ja.job_id = j.id
            WHERE o.id = ?
        ''', (offer_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = ['id', 'application_id', 'position_title', 'department', 'salary', 'start_date', 
                      'location', 'reporting_to', 'offer_type', 'benefits', 'offer_details', 
                      'response_deadline', 'status', 'created_by', 'created_at', 'applicant_id', 
                      'applicant_name', 'applicant_email', 'job_title']
            return dict(zip(columns, result))
        
        return None
    
    def update_offer_status(self, offer_id: int, status: str) -> bool:
        """Update offer status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE job_offers SET status = ? WHERE id = ?', (status, offer_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success

# Initialize database
db = ResumeDatabase()
