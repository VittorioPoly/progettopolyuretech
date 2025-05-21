import sqlite3
import os

# Percorso corretto del database (nella radice del progetto)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(PROJECT_ROOT, 'app.db')

ALTER_SQL = "ALTER TABLE dipendente_competenza ADD COLUMN percentuale INTEGER DEFAULT 0;"

# Funzione per controllare se la colonna esiste già
def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())

def main():
    print(f"Tentativo di connessione al database: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print(f"ERRORE: Database non trovato: {DB_PATH}")
        print("Assicurati che il file app.db esista nella cartella principale del progetto.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verifica se la tabella dipendente_competenza esiste
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dipendente_competenza';")
    if not cursor.fetchone():
        print(f"ERRORE: La tabella 'dipendente_competenza' non esiste nel database {DB_PATH}.")
        print("Potrebbe essere necessario inizializzare il database prima (es. con db.create_all() di Flask-SQLAlchemy).")
        conn.close()
        return

    if column_exists(cursor, 'dipendente_competenza', 'percentuale'):
        print("La colonna 'percentuale' esiste già nella tabella 'dipendente_competenza'. Nessuna modifica necessaria.")
    else:
        print("Aggiungo la colonna 'percentuale' alla tabella 'dipendente_competenza'...")
        try:
            cursor.execute(ALTER_SQL)
            conn.commit()
            print("Colonna 'percentuale' aggiunta con successo!")
        except sqlite3.Error as e:
            print(f"Errore SQLite durante l'aggiunta della colonna: {e}")
            print("Verifica che la tabella 'dipendente_competenza' esista e che il comando SQL sia corretto.")
            
    conn.close()

if __name__ == "__main__":
    main() 