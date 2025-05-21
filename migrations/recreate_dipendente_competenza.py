import sqlite3
import os

def recreate_table():
    db_path = 'app/app.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Backup existing data
        cursor.execute("SELECT * FROM dipendente_competenza")
        existing_data = cursor.fetchall()
        
        # Drop the existing table
        cursor.execute("DROP TABLE IF EXISTS dipendente_competenza")
        
        # Create the table with the correct structure
        cursor.execute('''
        CREATE TABLE dipendente_competenza (
            dipendente_id INTEGER NOT NULL,
            competenza_id INTEGER NOT NULL,
            percentuale INTEGER DEFAULT 0,
            PRIMARY KEY (dipendente_id, competenza_id),
            FOREIGN KEY(dipendente_id) REFERENCES dipendente (id),
            FOREIGN KEY(competenza_id) REFERENCES competenza (id)
        )
        ''')
        
        # Restore the data
        if existing_data:
            # If old table had only dipendente_id and competenza_id
            if len(existing_data[0]) == 2:
                cursor.executemany(
                    "INSERT INTO dipendente_competenza (dipendente_id, competenza_id, percentuale) VALUES (?, ?, 0)",
                    [(row[0], row[1], 0) for row in existing_data]
                )
            # If old table already had percentuale column
            elif len(existing_data[0]) == 3:
                cursor.executemany(
                    "INSERT INTO dipendente_competenza (dipendente_id, competenza_id, percentuale) VALUES (?, ?, ?)",
                    existing_data
                )
        
        conn.commit()
        print("Successfully recreated dipendente_competenza table with percentuale column")
        
        # Verify the structure
        cursor.execute("PRAGMA table_info(dipendente_competenza)")
        columns = cursor.fetchall()
        print("\nNew table structure:")
        for col in columns:
            print(f"Column: {col[1]}, Type: {col[2]}, NotNull: {col[3]}, DefaultValue: {col[4]}, PK: {col[5]}")
            
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    recreate_table() 