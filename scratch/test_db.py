
import sqlite3
from datetime import datetime

db_path = "resumes.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Try a dummy insert
    cursor.execute('''
        INSERT INTO evaluations (
            application_id, evaluator_id, technical_score, experience_score,
            communication_score, culture_score, overall_score, feedback, evaluation_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        999999, 1, 5.0, 5.0, 5.0, 5.0, 5.0, "Test feedback", datetime.now().isoformat()
    ))
    conn.commit()
    print("Insert successful")
    # Clean up
    cursor.execute("DELETE FROM evaluations WHERE application_id = 999999")
    conn.commit()
except Exception as e:
    print(f"Insert failed: {e}")
finally:
    conn.close()
