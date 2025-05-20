import sqlite3
import os
import traceback

def reset_dipendenti():
    db_path = 'app/app.db'
    
    print(f"Connessione al database: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Elimina tutte le tabelle correlate
        print("\nElimino le tabelle esistenti...")
        cursor.execute("DROP TABLE IF EXISTS prelievi_vestiario")
        cursor.execute("DROP TABLE IF EXISTS timbrature")
        cursor.execute("DROP TABLE IF EXISTS dipendente_competenza")
        cursor.execute("DROP TABLE IF EXISTS dipendente")
        
        # Ricrea la tabella dipendente
        print("\nRicreo la tabella dipendente...")
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
        
        # Ricrea la tabella dipendente_competenza
        print("Ricreo la tabella dipendente_competenza...")
        cursor.execute('''
        CREATE TABLE dipendente_competenza (
            dipendente_id INTEGER,
            competenza_id INTEGER,
            PRIMARY KEY (dipendente_id, competenza_id),
            FOREIGN KEY (dipendente_id) REFERENCES dipendente (id),
            FOREIGN KEY (competenza_id) REFERENCES competenza (id)
        )
        ''')
        
        # Ricrea la tabella prelievi_vestiario
        print("Ricreo la tabella prelievi_vestiario...")
        cursor.execute('''
        CREATE TABLE prelievi_vestiario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dipendente_id INTEGER,
            item_id INTEGER,
            quantita INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dipendente_id) REFERENCES dipendente (id),
            FOREIGN KEY (item_id) REFERENCES inventory (id)
        )
        ''')
        
        # Ricrea la tabella timbrature
        print("Ricreo la tabella timbrature...")
        cursor.execute('''
        CREATE TABLE timbrature (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dipendente_id INTEGER,
            tipo VARCHAR(20),
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dipendente_id) REFERENCES dipendente (id)
        )
        ''')
        
        # Crea gli indici
        print("\nCreo gli indici...")
        cursor.execute('CREATE UNIQUE INDEX ix_dipendente_matricola ON dipendente (matricola)')
        cursor.execute('CREATE INDEX ix_dipendente_nome ON dipendente (nome)')
        cursor.execute('CREATE INDEX ix_dipendente_cognome ON dipendente (cognome)')
        
        # Commit delle modifiche
        conn.commit()
        
        # Verifica finale
        print("\nVerifica finale della struttura:")
        cursor.execute("PRAGMA table_info(dipendente)")
        columns = cursor.fetchall()
        print("\nColonne della tabella dipendente:")
        for col in columns:
            print(f"- {col[1]} ({col[2]})")
        
        conn.close()
        print("\nReset completato con successo!")
        
    except Exception as e:
        print(f"\nERRORE durante il reset: {str(e)}")
        print(traceback.format_exc())
        raise

if __name__ == "__main__":
    reset_dipendenti() 