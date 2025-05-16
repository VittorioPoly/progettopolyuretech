import sqlite3
import os
from datetime import datetime
import traceback

# Percorso del database
db_path = 'app/app.db'

# Backup dei dati esistenti
def backup_data():
    try:
        print(f"Connessione al database: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Recupera i dati esistenti
        print("Recupero dei dati esistenti...")
        cursor.execute("SELECT id, nome FROM dipendente")
        existing_data = cursor.fetchall()
        print(f"Dati recuperati: {existing_data}")
        
        conn.close()
        return existing_data
    except Exception as e:
        print(f"Errore durante il backup: {str(e)}")
        print(traceback.format_exc())
        raise

# Ricrea la tabella con la struttura corretta
def recreate_table():
    try:
        print("Connessione al database per ricreare la tabella...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Rimuovi la tabella esistente
        print("Rimozione della tabella esistente...")
        cursor.execute("DROP TABLE IF EXISTS dipendente")
        
        # Crea la nuova tabella con la struttura corretta
        print("Creazione della nuova tabella...")
        cursor.execute('''
        CREATE TABLE dipendente (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(100) NOT NULL,
            cognome VARCHAR(100) NOT NULL,
            anno_nascita INTEGER,
            luogo_nascita VARCHAR(100),
            provincia_nascita VARCHAR(2),
            codice_fiscale VARCHAR(16),
            email VARCHAR(100),
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
            archiviato BOOLEAN DEFAULT 0
        )
        ''')
        
        # Crea l'indice univoco sulla matricola
        print("Creazione dell'indice univoco...")
        cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS ix_dipendente_matricola ON dipendente (matricola)
        ''')
        
        conn.commit()
        conn.close()
        print("Tabella ricreata con successo!")
    except Exception as e:
        print(f"Errore durante la ricreazione della tabella: {str(e)}")
        print(traceback.format_exc())
        raise

# Ripristina i dati
def restore_data(existing_data):
    try:
        print("Connessione al database per ripristinare i dati...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"Ripristino di {len(existing_data)} record...")
        for id, nome in existing_data:
            print(f"Ripristino record: id={id}, nome={nome}")
            cursor.execute('''
            INSERT INTO dipendente (id, nome, cognome)
            VALUES (?, ?, ?)
            ''', (id, nome, ''))  # Aggiungiamo cognome vuoto per soddisfare il NOT NULL
        
        conn.commit()
        conn.close()
        print("Dati ripristinati con successo!")
    except Exception as e:
        print(f"Errore durante il ripristino dei dati: {str(e)}")
        print(traceback.format_exc())
        raise

def main():
    try:
        print("Inizio aggiornamento struttura tabella dipendente...")
        
        # Backup dei dati
        print("\n1. Backup dei dati esistenti...")
        existing_data = backup_data()
        
        # Ricrea la tabella
        print("\n2. Ricreazione della tabella con la nuova struttura...")
        recreate_table()
        
        # Ripristina i dati
        print("\n3. Ripristino dei dati...")
        restore_data(existing_data)
        
        print("\nAggiornamento completato con successo!")
    except Exception as e:
        print(f"\nErrore durante l'aggiornamento: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main() 