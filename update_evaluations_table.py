#!/usr/bin/env python3
"""
Script to update the evaluations table with new columns
"""

import sqlite3
from database import db

def update_evaluations_table():
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='evaluations'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("Creating evaluations table...")
            cursor.execute('''
                CREATE TABLE evaluations (
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
        else:
            print("Updating existing evaluations table...")
            
            # Add new columns if they don't exist
            columns_to_add = [
                ('evaluator_id', 'INTEGER'),
                ('culture_score', 'REAL'),
                ('feedback', 'TEXT')
            ]
            
            for col_name, col_type in columns_to_add:
                try:
                    cursor.execute(f'ALTER TABLE evaluations ADD COLUMN {col_name} {col_type}')
                    print(f"Added column: {col_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"Column {col_name} already exists")
                    else:
                        print(f"Error adding {col_name}: {e}")
        
        conn.commit()
        print("Evaluations table updated successfully!")
        
        # Show final structure
        cursor.execute('PRAGMA table_info(evaluations)')
        columns = cursor.fetchall()
        print('\nFinal evaluations table structure:')
        for col in columns:
            print(f'  {col}')
            
    except Exception as e:
        print(f"Error updating table: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_evaluations_table()
