import sqlite3
import os

def migrate():
    db_path = 'app/app.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Drop existing tables if they exist
        cursor.execute('DROP TABLE IF EXISTS corso_formazione')
        cursor.execute('DROP TABLE IF EXISTS partecipazione_corso')
        cursor.execute('DROP TABLE IF EXISTS corso_sicurezza')
        cursor.execute('DROP TABLE IF EXISTS dipendente_corso_sicurezza')

        # Creazione della nuova tabella corso_formazione
        cursor.execute('''
        CREATE TABLE corso_formazione (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titolo VARCHAR(100) NOT NULL,
            descrizione TEXT,
            durata_ore INTEGER,
            data_inizio DATE,
            is_obbligatorio BOOLEAN DEFAULT 0,
            archiviato BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Creazione della nuova tabella partecipazione_corso
        cursor.execute('''
        CREATE TABLE partecipazione_corso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dipendente_id INTEGER NOT NULL,
            corso_id INTEGER NOT NULL,
            stato VARCHAR(20) DEFAULT 'da_iniziare',
            data_iscrizione DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_completamento DATETIME,
            valutazione INTEGER,
            FOREIGN KEY (dipendente_id) REFERENCES dipendente (id),
            FOREIGN KEY (corso_id) REFERENCES corso_formazione (id)
        )
        ''')

        # Creazione della nuova tabella corso_sicurezza
        cursor.execute('''
        CREATE TABLE corso_sicurezza (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titolo VARCHAR(100) NOT NULL,
            descrizione TEXT,
            durata_ore INTEGER,
            data_scadenza DATE,
            is_completato BOOLEAN DEFAULT 0,
            data_completamento DATETIME,
            archiviato BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Creazione della tabella di associazione dipendente_corso_sicurezza
        cursor.execute('''
        CREATE TABLE dipendente_corso_sicurezza (
            dipendente_id INTEGER NOT NULL,
            corso_id INTEGER NOT NULL,
            PRIMARY KEY (dipendente_id, corso_id),
            FOREIGN KEY (dipendente_id) REFERENCES dipendente (id),
            FOREIGN KEY (corso_id) REFERENCES corso_sicurezza (id)
        )
        ''')

        conn.commit()
        print("Migrazione completata con successo")
    except sqlite3.Error as e:
        print(f"Errore durante la migrazione: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
