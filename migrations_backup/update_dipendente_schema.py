import sqlite3
import os

# Path to the database
db_path = 'app/app.db'

# Create a new connection
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get existing columns
cursor.execute("PRAGMA table_info(dipendente)")
existing_columns = [column[1] for column in cursor.fetchall()]

# Define new columns to add
new_columns = {
    'anno_nascita': 'INTEGER',
    'luogo_nascita': 'VARCHAR(100)',
    'provincia_nascita': 'VARCHAR(2)',
    'codice_fiscale': 'VARCHAR(16)',
    'telefono': 'VARCHAR(20)',
    'matricola': 'VARCHAR(20)',
    'reparto': 'VARCHAR(100)',
    'ruolo': 'VARCHAR(100)',
    'data_assunzione_somministrazione': 'DATE',
    'agenzia_somministrazione': 'VARCHAR(100)',
    'data_assunzione_indeterminato': 'DATE',
    'legge_104': 'BOOLEAN DEFAULT 0',
    'donatore_avis': 'BOOLEAN DEFAULT 0',
    'indirizzo_residenza': 'VARCHAR(200)',
    'citta_residenza': 'VARCHAR(100)',
    'provincia_residenza': 'VARCHAR(2)',
    'cap_residenza': 'VARCHAR(5)',
    'data_cessazione': 'DATE',
    'note': 'TEXT',
    'archiviato': 'BOOLEAN DEFAULT 0'
}

# Add missing columns
for column_name, column_type in new_columns.items():
    if column_name not in existing_columns:
        try:
            cursor.execute(f'''
            ALTER TABLE dipendente ADD COLUMN {column_name} {column_type};
            ''')
            print(f"Added column: {column_name}")
        except sqlite3.OperationalError as e:
            print(f"Error adding column {column_name}: {e}")

# Create unique index on matricola if it doesn't exist
try:
    cursor.execute('''
    CREATE UNIQUE INDEX IF NOT EXISTS ix_dipendente_matricola ON dipendente (matricola);
    ''')
    print("Created unique index on matricola")
except sqlite3.OperationalError as e:
    print(f"Error creating index: {e}")

# Commit the changes
conn.commit()

# Close the connection
conn.close()

print("Database schema update completed.") 