import sqlite3
import os

def check_table_structure():
    db_path = 'app/app.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get table info
        cursor.execute("PRAGMA table_info(dipendente_competenza)")
        columns = cursor.fetchall()
        
        print("\nCurrent table structure:")
        for col in columns:
            print(f"Column: {col[1]}, Type: {col[2]}, NotNull: {col[3]}, DefaultValue: {col[4]}, PK: {col[5]}")
            
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    check_table_structure() 