import sqlite3
import os

DB_PATH = "history.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"{DB_PATH} does not exist. No migration needed.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(chapters)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "is_completed" not in columns:
            print("Adding 'is_completed' column to 'chapters' table...")
            cursor.execute("ALTER TABLE chapters ADD COLUMN is_completed INTEGER DEFAULT 0")
            conn.commit()
            print("Migration successful.")
        else:
            print("'is_completed' column already exists.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
