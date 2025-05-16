import sqlite3
import os
import traceback

def recreate_database():
    # Get the base directory path
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    db_path = os.path.join(basedir, 'app.db')
    
    # Rimuovi il database esistente se presente
    if os.path.exists(db_path):
        print(f"Rimuovo il database esistente: {db_path}")
        os.remove(db_path)
    
    print("Creo un nuovo database...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Crea la tabella users
        print("\nCreo la tabella users...")
        cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(64) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(128) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'user',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            is_active BOOLEAN DEFAULT 1
        )
        ''')
        
        # Verifica che la tabella users sia stata creata
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            print("Tabella users creata con successo!")
            
            # Verifica la struttura della tabella
            print("\nStruttura della tabella users:")
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"- {col[1]} ({col[2]})")
        else:
            print("ERRORE: La tabella users non è stata creata!")
        
        # Crea la tabella dipendente
        print("\nCreo la tabella dipendente...")
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
        
        # Verifica che la tabella sia stata creata
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dipendente'")
        if cursor.fetchone():
            print("Tabella dipendente creata con successo!")
            
            # Verifica la struttura della tabella
            print("\nStruttura della tabella dipendente:")
            cursor.execute("PRAGMA table_info(dipendente)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"- {col[1]} ({col[2]})")
        else:
            print("ERRORE: La tabella dipendente non è stata creata!")
        
        # Crea la tabella competenza
        print("\nCreo la tabella competenza...")
        cursor.execute('''
        CREATE TABLE competenza (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(64) NOT NULL,
            descrizione TEXT,
            livello VARCHAR(20),
            area VARCHAR(64),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_by_id INTEGER
        )
        ''')
        
        # Crea la tabella dipendente_competenza (tabella di join)
        print("Creo la tabella dipendente_competenza...")
        cursor.execute('''
        CREATE TABLE dipendente_competenza (
            dipendente_id INTEGER,
            competenza_id INTEGER,
            PRIMARY KEY (dipendente_id, competenza_id),
            FOREIGN KEY (dipendente_id) REFERENCES dipendente (id),
            FOREIGN KEY (competenza_id) REFERENCES competenza (id)
        )
        ''')
        
        # Crea la tabella inventory (vestiario)
        print("Creo la tabella inventory...")
        cursor.execute('''
        CREATE TABLE inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(128) NOT NULL,
            taglia VARCHAR(64),
            quantita INTEGER DEFAULT 0
        )
        ''')
        
        # Crea la tabella prelievi_vestiario
        print("Creo la tabella prelievi_vestiario...")
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
        
        # Crea la tabella timbrature
        print("Creo la tabella timbrature...")
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
        print("Creo gli indici...")
        cursor.execute('CREATE UNIQUE INDEX ix_users_username ON users (username)')
        cursor.execute('CREATE UNIQUE INDEX ix_users_email ON users (email)')
        cursor.execute('CREATE UNIQUE INDEX ix_dipendente_matricola ON dipendente (matricola)')
        cursor.execute('CREATE INDEX ix_dipendente_nome ON dipendente (nome)')
        cursor.execute('CREATE INDEX ix_dipendente_cognome ON dipendente (cognome)')
        cursor.execute('CREATE INDEX ix_competenza_nome ON competenza (nome)')
        cursor.execute('CREATE INDEX ix_inventory_nome ON inventory (nome)')
        
        # Commit delle modifiche
        conn.commit()
        
        # Verifica finale
        print("\nVerifica finale delle tabelle:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            print(f"- {table[0]}")
        
        conn.close()
        print("\nDatabase ricreato con successo!")
        
    except Exception as e:
        print(f"\nERRORE durante la creazione del database: {str(e)}")
        print(traceback.format_exc())
        raise

if __name__ == "__main__":
    recreate_database() 