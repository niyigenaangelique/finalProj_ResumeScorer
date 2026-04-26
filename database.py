import sqlite3
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional
import urllib.request
import json

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
                consent_to_store_cv BOOLEAN DEFAULT 0,
                consent_date TEXT,
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
                match_summary TEXT,
                matched_skills TEXT,
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
                evaluator_id INTEGER,
                technical_score REAL,
                communication_score REAL,
                experience_score REAL,
                culture_score REAL,
                overall_score REAL,
                feedback TEXT,
                evaluation_date TEXT DEFAULT CURRENT_TIMESTAMP,
                interviewer_name TEXT,
                strengths TEXT,
                weaknesses TEXT,
                comments TEXT,
                recommendation TEXT,
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
        
        # Create contact_messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contact_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT DEFAULT 'unread',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create ai_screening_results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_screening_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                applicant_id INTEGER,
                job_id INTEGER,
                ai_score REAL,
                ai_status TEXT,
                match_details TEXT,
                interview_questions TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (applicant_id) REFERENCES applicants (id),
                FOREIGN KEY (job_id) REFERENCES jobs (id)
            )
        ''')
        
        # Create assessments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                job_id INTEGER,
                description TEXT,
                time_limit_minutes INTEGER DEFAULT 30,
                passing_score REAL DEFAULT 70.0,
                created_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (job_id) REFERENCES jobs(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assessment_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id INTEGER,
                question_text TEXT NOT NULL,
                question_type TEXT DEFAULT 'multiple_choice',
                options TEXT,
                correct_answer TEXT,
                points INTEGER DEFAULT 10,
                order_num INTEGER DEFAULT 0,
                FOREIGN KEY (assessment_id) REFERENCES assessments(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assessment_invites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id INTEGER UNIQUE,
                assessment_id INTEGER,
                token TEXT UNIQUE NOT NULL,
                invited_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (application_id) REFERENCES job_applications(id),
                FOREIGN KEY (assessment_id) REFERENCES assessments(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assessment_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invite_id INTEGER UNIQUE,
                application_id INTEGER,
                assessment_id INTEGER,
                score REAL DEFAULT 0,
                max_score REAL DEFAULT 0,
                percentage REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                started_at TEXT,
                completed_at TEXT,
                answers TEXT,
                cheating_flags TEXT,
                tab_switch_count INTEGER DEFAULT 0,
                passed INTEGER DEFAULT 0,
                FOREIGN KEY (invite_id) REFERENCES assessment_invites(id)
            )
        ''')
        
        conn.commit()
        conn.close()

    # ── ASSESSMENT METHODS ─────────────────────────────────────────────────────

    def create_assessment(self, title: str, job_id: int, description: str = '', 
                          time_limit: int = 30, passing_score: float = 70.0,
                          created_by: str = None) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO assessments (title, job_id, description, time_limit_minutes, passing_score, created_by)
                          VALUES (?, ?, ?, ?, ?, ?)''',
                       (title, job_id, description, time_limit, passing_score, created_by))
        aid = cursor.lastrowid
        conn.commit(); conn.close()
        return aid

    def add_assessment_question(self, assessment_id: int, question_text: str, question_type: str = 'multiple_choice',
                                options: list = None, correct_answer: str = None, points: int = 10, order_num: int = 0) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO assessment_questions (assessment_id, question_text, question_type, options, correct_answer, points, order_num)
                          VALUES (?, ?, ?, ?, ?, ?, ?)''',
                       (assessment_id, question_text, question_type, json.dumps(options or []), correct_answer, points, order_num))
        qid = cursor.lastrowid
        conn.commit(); conn.close()
        return qid

    def get_assessment(self, assessment_id: int) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM assessments WHERE id = ?', (assessment_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        cols = ['id','title','job_id','description','time_limit_minutes','passing_score','created_by','created_at','is_active']
        return dict(zip(cols, row))

    def get_assessment_questions(self, assessment_id: int) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM assessment_questions WHERE assessment_id = ? ORDER BY order_num', (assessment_id,))
        rows = cursor.fetchall(); conn.close()
        cols = ['id','assessment_id','question_text','question_type','options','correct_answer','points','order_num']
        questions = []
        for row in rows:
            q = dict(zip(cols, row))
            try: q['options'] = json.loads(q['options'] or '[]')
            except: q['options'] = []
            questions.append(q)
        return questions

    def update_assessment_question(self, question_id: int, question_text: str,
                                   question_type: str = 'multiple_choice', options: list = None,
                                   correct_answer: str = None, points: int = 10) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''UPDATE assessment_questions
                          SET question_text = ?, question_type = ?, options = ?, correct_answer = ?, points = ?
                          WHERE id = ?''',
                       (question_text, question_type, json.dumps(options or []), correct_answer, points, question_id))
        success = cursor.rowcount > 0
        conn.commit(); conn.close()
        return success

    def delete_assessment_question(self, question_id: int) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM assessment_questions WHERE id = ?', (question_id,))
        success = cursor.rowcount > 0
        conn.commit(); conn.close()
        return success

    def get_all_assessments(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''SELECT a.*, j.title as job_title,
                          (SELECT COUNT(*) FROM assessment_questions WHERE assessment_id=a.id) as question_count,
                          (SELECT COUNT(*) FROM assessment_invites WHERE assessment_id=a.id) as invite_count
                          FROM assessments a LEFT JOIN jobs j ON a.job_id=j.id ORDER BY a.created_at DESC''')
        rows = cursor.fetchall(); conn.close()
        cols = ['id','title','job_id','description','time_limit_minutes','passing_score','created_by','created_at','is_active','job_title','question_count','invite_count']
        return [dict(zip(cols, r)) for r in rows]

    def create_assessment_invite(self, application_id: int, assessment_id: int, token: str, expires_at: str = None) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''INSERT OR REPLACE INTO assessment_invites (application_id, assessment_id, token, expires_at)
                              VALUES (?, ?, ?, ?)''',
                           (application_id, assessment_id, token, expires_at))
            iid = cursor.lastrowid
            conn.commit()
        except Exception as e:
            conn.close(); raise e
        conn.close()
        return iid

    def get_invite_by_token(self, token: str) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''SELECT i.*, a.name as applicant_name, a.email as applicant_email,
                          j.title as job_title, ai.title as assessment_title, ai.time_limit_minutes, ai.passing_score
                          FROM assessment_invites i
                          JOIN job_applications ja ON i.application_id = ja.id
                          JOIN applicants a ON ja.applicant_id = a.id
                          JOIN jobs j ON ja.job_id = j.id
                          JOIN assessments ai ON i.assessment_id = ai.id
                          WHERE i.token = ?''', (token,))
        row = cursor.fetchone(); conn.close()
        if not row: return None
        cols = ['id','application_id','assessment_id','token','invited_at','expires_at','status',
                'applicant_name','applicant_email','job_title','assessment_title','time_limit_minutes','passing_score']
        return dict(zip(cols, row))

    def save_assessment_result(self, invite_id: int, application_id: int, assessment_id: int,
                               score: float, max_score: float, answers: dict, 
                               tab_switch_count: int = 0, cheating_flags: list = None) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        percentage = (score / max_score * 100) if max_score > 0 else 0
        cursor.execute('SELECT passing_score FROM assessments WHERE id = ?', (assessment_id,))
        row = cursor.fetchone()
        passing = row[0] if row else 70.0
        passed = 1 if percentage >= passing else 0
        cursor.execute('''INSERT OR REPLACE INTO assessment_results 
                          (invite_id, application_id, assessment_id, score, max_score, percentage, status, completed_at, answers, cheating_flags, tab_switch_count, passed)
                          VALUES (?, ?, ?, ?, ?, ?, 'completed', ?, ?, ?, ?, ?)''',
                       (invite_id, application_id, assessment_id, score, max_score, percentage,
                        datetime.now().isoformat(), json.dumps(answers),
                        json.dumps(cheating_flags or []), tab_switch_count, passed))
        # Mark invite as completed
        cursor.execute('UPDATE assessment_invites SET status = ? WHERE id = ?',
                       ('completed' if passed else 'failed', invite_id))
        rid = cursor.lastrowid
        conn.commit(); conn.close()
        return rid

    def get_assessment_result_for_application(self, application_id: int) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''SELECT ar.*, ai.assessment_title
                          FROM assessment_results ar
                          LEFT JOIN assessment_invites ai ON ar.invite_id = ai.id
                          WHERE ar.application_id = ?
                          ORDER BY ar.completed_at DESC LIMIT 1''', (application_id,))
        row = cursor.fetchone(); conn.close()
        if not row: return None
        cols = ['id','invite_id','application_id','assessment_id','score','max_score','percentage',
                'status','started_at','completed_at','answers','cheating_flags','tab_switch_count','passed','assessment_title']
        return dict(zip(cols, row))

    def get_all_assessment_results(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''SELECT ar.*, a.name as applicant_name, a.email as applicant_email,
                          j.title as job_title, ass.title as assessment_title
                          FROM assessment_results ar
                          JOIN job_applications ja ON ar.application_id = ja.id
                          JOIN applicants a ON ja.applicant_id = a.id
                          JOIN jobs j ON ja.job_id = j.id
                          JOIN assessments ass ON ar.assessment_id = ass.id
                          ORDER BY ar.completed_at DESC''')
        rows = cursor.fetchall(); conn.close()
        cols = ['id','invite_id','application_id','assessment_id','score','max_score','percentage',
                'status','started_at','completed_at','answers','cheating_flags','tab_switch_count','passed',
                'applicant_name','applicant_email','job_title','assessment_title']
        return [dict(zip(cols, r)) for r in rows]

    def add_applicant(self, name: str, email: str = None, phone: str = None, 
                    position: str = None, department: str = None, consent: bool = False) -> int:
        """Add a new applicant"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO applicants (name, email, phone, position, department, application_date, consent_to_store_cv, consent_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, phone, position, department, datetime.now().isoformat(), consent, datetime.now().isoformat() if consent else None))
        
        applicant_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return applicant_id
    
    def save_resume_score(self, applicant_id: int, resume_text: str, score: float, 
                        features: Dict, recommendations: List[str], filename: str = None,
                        match_summary: str = None, matched_skills: str = None) -> int:
        """Save resume score and analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO resume_scores 
            (applicant_id, resume_text, score, features, recommendations, match_summary, matched_skills, filename)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (applicant_id, resume_text, score, json.dumps(features), json.dumps(recommendations), match_summary, matched_skills, filename))
        
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
            if applicant['features'] and isinstance(applicant['features'], str):
                try:
                    applicant['features'] = json.loads(applicant['features'])
                except:
                    applicant['features'] = {}
            elif not isinstance(applicant['features'], dict):
                applicant['features'] = {}

            if applicant['recommendations'] and isinstance(applicant['recommendations'], str):
                try:
                    applicant['recommendations'] = json.loads(applicant['recommendations'])
                except:
                    applicant['recommendations'] = []
            elif not isinstance(applicant['recommendations'], list):
                applicant['recommendations'] = []
            
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
    
    def create_job(self, title: str, department: str, employment_type: str = None, 
                   experience_level: str = None, location: str = None, work_mode: str = None,
                   salary_min: str = None, salary_max: str = None, job_description: str = None, 
                   requirements: str = None, nice_to_have: str = None, benefits: str = None,
                   application_deadline: str = None, hiring_manager: str = None, 
                   team_size: int = None, featured_job: bool = False, urgent_hiring: bool = False) -> int:
        """Create a new job with extended fields"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if jobs table has the new columns, add them if not
        cursor.execute("PRAGMA table_info(jobs)")
        columns = [row[1] for row in cursor.fetchall()]
        
        new_columns = []
        if 'employment_type' not in columns:
            new_columns.append("ALTER TABLE jobs ADD COLUMN employment_type TEXT")
        if 'experience_level' not in columns:
            new_columns.append("ALTER TABLE jobs ADD COLUMN experience_level TEXT")
        if 'work_mode' not in columns:
            new_columns.append("ALTER TABLE jobs ADD COLUMN work_mode TEXT")
        if 'salary_min' not in columns:
            new_columns.append("ALTER TABLE jobs ADD COLUMN salary_min TEXT")
        if 'salary_max' not in columns:
            new_columns.append("ALTER TABLE jobs ADD COLUMN salary_max TEXT")
        if 'featured_job' not in columns:
            new_columns.append("ALTER TABLE jobs ADD COLUMN featured_job BOOLEAN DEFAULT 0")
        if 'urgent_hiring' not in columns:
            new_columns.append("ALTER TABLE jobs ADD COLUMN urgent_hiring BOOLEAN DEFAULT 0")
        if 'application_deadline' not in columns:
            new_columns.append("ALTER TABLE jobs ADD COLUMN application_deadline TEXT")
        if 'hiring_manager' not in columns:
            new_columns.append("ALTER TABLE jobs ADD COLUMN hiring_manager TEXT")
        if 'team_size' not in columns:
            new_columns.append("ALTER TABLE jobs ADD COLUMN team_size INTEGER")
        
        for alter_sql in new_columns:
            cursor.execute(alter_sql)
        
        # Insert the job with all fields
        cursor.execute('''
            INSERT INTO jobs 
            (title, department, location, salary, description, requirements, 
             employment_type, experience_level, work_mode, salary_min, salary_max,
             featured_job, urgent_hiring, application_deadline, hiring_manager, team_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, department, location, 
              f"{salary_min or ''} - {salary_max or ''}" if salary_min or salary_max else None,
              job_description, requirements, employment_type, experience_level, work_mode,
              salary_min, salary_max, featured_job, urgent_hiring, application_deadline, 
              hiring_manager, team_size))
        
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
        colnames = [d[0] for d in (cursor.description or [])]
        conn.close()
        return [dict(zip(colnames, row)) for row in results] if results and colnames else []
    
    def get_job(self, job_id: int) -> Optional[Dict]:
        """Get a specific job"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
        result = cursor.fetchone()
        colnames = [d[0] for d in (cursor.description or [])]
        conn.close()
        
        if result and colnames:
            return dict(zip(colnames, result))
        
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
                a.phone as applicant_phone,
                rs.score as resume_score,
                ai.ai_score,
                ai.ai_status
            FROM job_applications ja
            JOIN jobs j ON ja.job_id = j.id
            JOIN applicants a ON ja.applicant_id = a.id
            LEFT JOIN resume_scores rs ON a.id = rs.applicant_id
            LEFT JOIN ai_screening_results ai ON (ja.applicant_id = ai.applicant_id AND ja.job_id = ai.job_id)
            ORDER BY rs.score DESC, ja.application_date DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'job_id', 'applicant_id', 'cover_letter', 'application_date', 'status',
                  'job_title', 'department', 'applicant_name', 'applicant_email', 'applicant_phone', 
                  'resume_score', 'ai_score', 'ai_status']
        
        applications = []
        for result in results:
            app = dict(zip(columns, result))
            applications.append(app)
        
        return applications

    def check_existing_application(self, email: str, job_id: int) -> Optional[Dict]:
        """Check if an applicant with this email has already applied for this job"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ja.* 
            FROM job_applications ja
            JOIN applicants a ON ja.applicant_id = a.id
            WHERE a.email = ? AND ja.job_id = ?
        ''', (email, job_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = ['id', 'job_id', 'applicant_id', 'cover_letter', 'application_date', 'status']
            return dict(zip(columns, result))
        
        return None
    
    def update_application_status(self, application_id: int, status: str, strict_sync: bool = False) -> bool:
        """Update application status and sync with TalentFlow HRMS if hired.
        
        If strict_sync=True and HRMS sync fails, an exception is raised so
        callers can rollback their own state transitions.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE job_applications SET status = ? WHERE id = ?
            ''', (status, application_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            
            if success and status.lower() == 'hired':
                try:
                    self._sync_hired_to_talentflow(application_id)
                except Exception as e:
                    print(f"[SYNC ERROR] Failed to push to Laravel: {e}")
                    if strict_sync:
                        raise
                    # Non-strict mode keeps local status even if external sync fails.
                
            return success
        finally:
            conn.close()

    def _sync_hired_to_talentflow(self, application_id: int):
        """Internal helper to push hired employee to Laravel HRMS"""
        try:
            # 1. Fetch full details
            app = self.get_application_by_id(application_id)
            if not app:
                return

            # 2. Prepare payload
            name_parts = (app.get('applicant_name') or 'Hired Employee').split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else 'Employee'
            latest_offer = self.get_latest_offer_by_application(application_id) or {}

            raw_gender = (app.get('gender') or '').strip().lower()
            if raw_gender not in ('male', 'female'):
                raw_gender = os.getenv("TALENTFLOW_HRMS_DEFAULT_GENDER", "female").strip().lower()
                if raw_gender not in ('male', 'female'):
                    raw_gender = 'female'

            def parse_salary_value(salary_text: str) -> float:
                if not salary_text:
                    return 0.0
                nums = re.findall(r'\d+(?:\.\d+)?', salary_text.replace(',', ''))
                if not nums:
                    return 0.0
                values = [float(n) for n in nums]
                return values[0]

            position_title = (
                latest_offer.get('position_title')
                or app.get('job_title')
                or app.get('position')
            )
            department_name = latest_offer.get('department') or app.get('department')
            salary_value = parse_salary_value(latest_offer.get('salary') or "")

            payload = {
                "first_name": first_name,
                "last_name": last_name,
                "email": app.get('applicant_email'),
                "phone_number": app.get('phone'),
                "gender": raw_gender,
                "birth_date": app.get('birth_date'),
                "basic_salary": salary_value,
                "join_date": datetime.now().strftime("%Y-%m-%d")
            }
            if position_title:
                payload["position_title"] = position_title
            if department_name:
                payload["department_name"] = department_name
            # Remove empty/null values that can fail strict Laravel validation.
            payload = {k: v for k, v in payload.items() if v not in (None, "")}

            # 3. API Config (overridable via environment variables)
            # Useful when Laravel runs on a different host/port or secret token.
            url = os.getenv("TALENTFLOW_HRMS_URL", "http://localhost:8000/api/external-recruitment/hire")
            token = os.getenv("TALENTFLOW_HRMS_TOKEN", "talentflow_secret_token_123")

            req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={
                "X-Recruitment-Token": token,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }, method="POST")

            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = json.loads(response.read().decode())
                print(f"[TALENTFLOW SYNC] Successfully pushed {app.get('applicant_email')}")
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            try:
                error_json = json.loads(error_body)
                error_msg = error_json.get('message', str(e))
                if error_json.get('error'):
                    error_msg += f" | {error_json.get('error')}"
                if 'errors' in error_json:
                    error_msg += " " + str(error_json['errors'])
            except:
                error_msg = error_body or str(e)
            print(f"[TALENTFLOW SYNC ERROR] Failed to push hired employee: {error_msg}")
            print(f"[TALENTFLOW SYNC ERROR] Payload: {payload}")
            raise Exception(f"HRMS Sync Failed: {error_msg}")
        except Exception as e:
            print(f"[TALENTFLOW SYNC ERROR] Failed to push hired employee: {str(e)}")
            print(f"[TALENTFLOW SYNC ERROR] Payload: {payload}")
            raise Exception(f"HRMS Sync Failed: {str(e)}")
    
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
        
        # Update application status
        cursor.execute('''
            UPDATE job_applications SET status = 'interview_scheduled' WHERE id = ?
        ''', (application_id,))
        
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
                o.position_title as offer_position,
                o.department as offer_department
            FROM job_applications ja
            JOIN jobs j ON ja.job_id = j.id
            JOIN applicants a ON ja.applicant_id = a.id
            LEFT JOIN resume_scores rs ON a.id = rs.applicant_id
            LEFT JOIN interviews i ON ja.id = i.application_id
            LEFT JOIN evaluations e ON ja.id = e.application_id
            LEFT JOIN job_offers o ON ja.id = o.application_id
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
                a.phone,
                rs.score as resume_score,
                rs.resume_text
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
                      'job_title', 'department', 'applicant_name', 'applicant_email', 'phone', 'resume_score', 'resume_text']
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

    def add_document(self, applicant_id: int, document_type: str, filename: str, file_path: str, file_size: int = 0) -> int:
        """Add a document record for an applicant. Returns new document id."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO documents (applicant_id, document_type, filename, file_path, file_size)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (int(applicant_id), str(document_type or "document"), str(filename or ""), str(file_path or ""), int(file_size or 0)),
        )
        doc_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return doc_id

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

    def get_latest_offer_by_application(self, application_id: int) -> Optional[Dict]:
        """Get the most recent job offer for one application."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, application_id, position_title, department, salary, start_date,
                   location, reporting_to, offer_type, benefits, offer_details,
                   response_deadline, status, created_by, created_at
            FROM job_offers
            WHERE application_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
        ''', (application_id,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            return None

        columns = ['id', 'application_id', 'position_title', 'department', 'salary', 'start_date',
                   'location', 'reporting_to', 'offer_type', 'benefits', 'offer_details',
                   'response_deadline', 'status', 'created_by', 'created_at']
        return dict(zip(columns, result))
    
    def update_offer_status(self, offer_id: int, status: str) -> bool:
        """Update offer status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE job_offers SET status = ? WHERE id = ?', (status, offer_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    # Report methods
    def save_report(self, report_type: str, report_data: Dict, format: str, generated_by: str,
                   start_date: str = None, end_date: str = None, department_filter: str = None) -> str:
        """Save a generated report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create reports table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                report_type TEXT,
                report_data TEXT,
                format TEXT,
                generated_by TEXT,
                start_date TEXT,
                end_date TEXT,
                department_filter TEXT,
                generated_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        import uuid
        report_id = str(uuid.uuid4())
        
        cursor.execute('''
            INSERT INTO reports 
            (id, report_type, report_data, format, generated_by, start_date, end_date, department_filter)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (report_id, report_type, json.dumps(report_data), format, generated_by, 
              start_date, end_date, department_filter))
        
        conn.commit()
        conn.close()
        
        return report_id
    
    def get_report(self, report_id: str) -> Optional[Dict]:
        """Get a specific report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM reports WHERE id = ?', (report_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = ['id', 'report_type', 'report_data', 'format', 'generated_by', 
                      'start_date', 'end_date', 'department_filter', 'generated_date']
            report = dict(zip(columns, result))
            
            # Parse JSON data
            if report['report_data']:
                report['report_data'] = json.loads(report['report_data'])
            
            return report
        
        return None
    
    def get_recent_reports(self, limit: int = 10) -> List[Dict]:
        """Get recent reports"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, report_type, format, generated_date, start_date, end_date
            FROM reports 
            ORDER BY generated_date DESC 
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'report_type', 'format', 'generated_date', 'start_date', 'end_date']
        reports = []
        
        for result in results:
            report = dict(zip(columns, result))
            reports.append(report)
        
        return reports
    
    def create_scheduled_report(self, name: str, report_type: str, frequency: str, 
                               email_recipients: str, created_by: str) -> str:
        """Create a scheduled report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create scheduled_reports table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_reports (
                id TEXT PRIMARY KEY,
                name TEXT,
                report_type TEXT,
                frequency TEXT,
                email_recipients TEXT,
                created_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                next_run TEXT
            )
        ''')
        
        import uuid
        schedule_id = str(uuid.uuid4())
        
        cursor.execute('''
            INSERT INTO scheduled_reports 
            (id, name, report_type, frequency, email_recipients, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (schedule_id, name, report_type, frequency, email_recipients, created_by))
        
        conn.commit()
        conn.close()
        
        return schedule_id
    
    def get_scheduled_reports(self) -> List[Dict]:
        """Get all scheduled reports"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, report_type, frequency, email_recipients, created_at, next_run
            FROM scheduled_reports 
            ORDER BY created_at DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'name', 'report_type', 'frequency', 'email_recipients', 
                  'created_at', 'next_run']
        reports = []
        
        for result in results:
            report = dict(zip(columns, result))
            reports.append(report)
        
        return reports
    
    def delete_scheduled_report(self, schedule_id: str) -> bool:
        """Delete a scheduled report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM scheduled_reports WHERE id = ?', (schedule_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    # HR Evaluation Portal Methods
    def get_applicants_for_evaluation(self) -> List[Dict]:
        """Get applicants who have submitted applications and need evaluation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT
                a.id as applicant_id,
                a.name,
                a.email,
                a.phone,
                a.position,
                ja.id as application_id,
                ja.application_date,
                ja.status,
                j.title as job_title,
                j.department,
                j.location,
                rs.score as resume_score,
                rs.features as resume_features,
                rs.recommendations as resume_recommendations
            FROM applicants a
            JOIN job_applications ja ON a.id = ja.applicant_id
            JOIN jobs j ON ja.job_id = j.id
            LEFT JOIN resume_scores rs ON a.id = rs.applicant_id
            WHERE ja.status IN ('interview_passed')
            ORDER BY ja.application_date DESC
        ''')
        
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        applicants = []
        for result in results:
            app_dict = dict(zip(columns, result))
            # Parse resume features if available
            if app_dict.get('resume_features'):
                try:
                    app_dict['resume_features'] = json.loads(app_dict['resume_features'])
                except:
                    app_dict['resume_features'] = {}
            applicants.append(app_dict)
        
        conn.close()
        return applicants
    
    def save_evaluation(self, application_id: int, evaluator_id: int, 
                       scores: Dict, feedback: str, overall_score: float) -> bool:
        """Save evaluation for an applicant"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if evaluation already exists
            cursor.execute('''
                SELECT id FROM evaluations WHERE application_id = ?
            ''', (application_id,))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing evaluation
                cursor.execute('''
                    UPDATE evaluations SET
                        evaluator_id = ?,
                        technical_score = ?,
                        experience_score = ?,
                        communication_score = ?,
                        culture_score = ?,
                        overall_score = ?,
                        feedback = ?,
                        evaluation_date = ?
                    WHERE application_id = ?
                ''', (
                    evaluator_id,
                    scores.get('technical', 0),
                    scores.get('experience', 0),
                    scores.get('communication', 0),
                    scores.get('culture', 0),
                    overall_score,
                    feedback,
                    datetime.now().isoformat(),
                    application_id
                ))
            else:
                # Insert new evaluation
                cursor.execute('''
                    INSERT INTO evaluations (
                        application_id, evaluator_id, technical_score, experience_score,
                        communication_score, culture_score, overall_score, feedback, evaluation_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    application_id, evaluator_id,
                    scores.get('technical', 0),
                    scores.get('experience', 0),
                    scores.get('communication', 0),
                    scores.get('culture', 0),
                    overall_score, feedback, datetime.now().isoformat()
                ))
            
            # Status update is handled by the caller or by separate update_application_status
            
            conn.commit()
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            # Log to a file we can read
            log_path = os.path.join(os.path.dirname(__file__), "db_error.log")
            with open(log_path, "a") as f:
                f.write(f"[{datetime.now().isoformat()}] save_evaluation FAILED for app {application_id}: {str(e)}\n")
            print(f"[DB ERROR] save_evaluation failed: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_evaluation_by_application(self, application_id: int) -> Optional[Dict]:
        """Get existing evaluation for an application"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e.*, e.interviewer_name as evaluator_name
            FROM evaluations e
            WHERE e.application_id = ?
        ''', (application_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
        return None
    
    # Contact Messages Methods
    def save_contact_message(self, name: str, email: str, subject: str, message: str) -> bool:
        """Save a new contact message"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO contact_messages (name, email, subject, message)
                VALUES (?, ?, ?, ?)
            ''', (name, email, subject, message))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving contact message: {e}")
            return False
        finally:
            conn.close()
    
    def get_contact_messages(self, status: str = None) -> List[Dict]:
        """Get contact messages, optionally filtered by status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status:
            cursor.execute('''
                SELECT * FROM contact_messages 
                WHERE status = ? 
                ORDER BY created_at DESC
            ''', (status,))
        else:
            cursor.execute('''
                SELECT * FROM contact_messages 
                ORDER BY created_at DESC
            ''')
        
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        
        return [dict(zip(columns, result)) for result in results]
    
    def mark_contact_message_read(self, message_id: int) -> bool:
        """Mark a contact message as read"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE contact_messages 
                SET status = 'read' 
                WHERE id = ?
            ''', (message_id,))
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error marking message as read: {e}")
            return False
        finally:
            conn.close()
    
    def get_unread_contact_count(self) -> int:
        """Get count of unread contact messages"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM contact_messages 
            WHERE status = 'unread'
        ''')
        
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def save_ai_screening(self, applicant_id: int, job_id: int, ai_score: float, 
                         ai_status: str, match_details: Dict, interview_questions: List[Dict]) -> bool:
        """Save AI screening results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO ai_screening_results 
                (applicant_id, job_id, ai_score, ai_status, match_details, interview_questions, created_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (applicant_id, job_id, ai_score, ai_status, 
                  json.dumps(match_details), json.dumps(interview_questions)))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving AI screening: {e}")
            return False
        finally:
            conn.close()
    
    def get_ai_screening_results(self, applicant_id: int = None, job_id: int = None) -> List[Dict]:
        """Get AI screening results, optionally filtered by applicant or job"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if applicant_id:
            cursor.execute('''
                SELECT * FROM ai_screening_results 
                WHERE applicant_id = ? 
                ORDER BY created_at DESC
            ''', (applicant_id,))
        elif job_id:
            cursor.execute('''
                SELECT * FROM ai_screening_results 
                WHERE job_id = ? 
                ORDER BY created_at DESC
            ''', (job_id,))
        else:
            cursor.execute('''
                SELECT * FROM ai_screening_results 
                ORDER BY created_at DESC
            ''')
        
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        
        formatted_results = []
        for result in results:
            row_dict = dict(zip(columns, result))
            # Parse JSON fields
            if row_dict.get('match_details'):
                try:
                    row_dict['match_details'] = json.loads(row_dict['match_details'])
                except:
                    pass
            if row_dict.get('interview_questions'):
                try:
                    row_dict['interview_questions'] = json.loads(row_dict['interview_questions'])
                except:
                    pass
            formatted_results.append(row_dict)
        
        return formatted_results

# Initialize database
db = ResumeDatabase()
