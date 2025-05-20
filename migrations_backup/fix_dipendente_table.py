import sqlite3
import os

def fix_table():
    db_path = 'app/app.db'
    
    # Create a backup of the database
    backup_path = f'{db_path}.backup'
    if os.path.exists(db_path):
        with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        print(f"Database backed up to {backup_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the current table structure
        cursor.execute("PRAGMA table_info(dipendente)")
        columns = cursor.fetchall()
        print("Current table structure:")
        for col in columns:
            print(col)
        
        # Create a new table with the correct structure
        print("\nCreating new table with correct structure...")
        cursor.execute('''
        CREATE TABLE dipendente_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(100) NOT NULL,
            cognome VARCHAR(100) NOT NULL,
            data_nascita DATE NOT NULL,
            luogo_nascita VARCHAR(100) NOT NULL,
            provincia_nascita VARCHAR(2) NOT NULL,
            codice_fiscale VARCHAR(16),
            email VARCHAR(120),
            telefono VARCHAR(20),
            matricola VARCHAR(20) UNIQUE,
            reparto VARCHAR(100),
            ruolo VARCHAR(100),
            data_assunzione_somministrazione DATE,
            agenzia_somministrazione VARCHAR(100),
            data_assunzione_indeterminato DATE,
            legge_104 BOOLEAN DEFAULT 0,
            donatore_avis BOOLEAN DEFAULT 0,
            indirizzo_residenza VARCHAR(200),
            citta_residenza VARCHAR(100),
            provincia_residenza VARCHAR(2),
            cap_residenza VARCHAR(5),
            data_cessazione DATE,
            note TEXT,
            archiviato BOOLEAN DEFAULT 0,
            created_by_id INTEGER,
            FOREIGN KEY (created_by_id) REFERENCES users (id)
        )
        ''')
        
        # Copy data from old table to new table
        print("\nCopying data to new table...")
        cursor.execute('''
        INSERT INTO dipendente_new (
            id, nome, cognome, luogo_nascita, provincia_nascita, 
            codice_fiscale, email, telefono, matricola, reparto, 
            ruolo, data_assunzione_somministrazione, agenzia_somministrazione,
            data_assunzione_indeterminato, legge_104, donatore_avis,
            indirizzo_residenza, citta_residenza, provincia_residenza,
            cap_residenza, data_cessazione, note, archiviato, created_by_id
        )
        SELECT 
            id, nome, cognome, luogo_nascita, provincia_nascita,
            codice_fiscale, email, telefono, matricola, reparto,
            ruolo, data_assunzione_somministrazione, agenzia_somministrazione,
            data_assunzione_indeterminato, legge_104, donatore_avis,
            indirizzo_residenza, citta_residenza, provincia_residenza,
            cap_residenza, data_cessazione, note, archiviato, created_by_id
        FROM dipendente
        ''')
        
        # Drop the old table and rename the new one
        print("\nReplacing old table with new one...")
        cursor.execute("DROP TABLE dipendente")
        cursor.execute("ALTER TABLE dipendente_new RENAME TO dipendente")
        
        # Create the unique index
        print("\nCreating unique index...")
        cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS ix_dipendente_matricola 
        ON dipendente (matricola)
        ''')
        
        # Commit the changes
        conn.commit()
        print("\nTable structure updated successfully!")
        
    except Exception as e:
        print(f"\nError during table update: {str(e)}")
        # Restore from backup if something went wrong
        if os.path.exists(backup_path):
            with open(backup_path, 'rb') as src, open(db_path, 'wb') as dst:
                dst.write(src.read())
            print("Database restored from backup")
        raise
    finally:
        conn.close()
        # Remove backup file if everything went well
        if os.path.exists(backup_path):
            os.remove(backup_path)

if __name__ == '__main__':
    fix_table() 