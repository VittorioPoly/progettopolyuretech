import sqlite3
import os

# Modifica qui se il percorso del tuo database è diverso
DB_PATH = 'app/app.db'

# Elimina completamente il file del database
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"Database esistente rimosso: {DB_PATH}")

# Crea una nuova connessione al database
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Crea la tabella competenza (necessaria per le foreign key)
print("Creazione tabella competenza...")
c.execute('''
CREATE TABLE competenza (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    descrizione TEXT,
    livello TEXT,
    area TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER
)
''')

# Crea la tabella dipendente
print("Creazione tabella dipendente...")
c.execute('''
CREATE TABLE dipendente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cognome TEXT NOT NULL,
    email TEXT,
    telefono TEXT,
    data_assunzione DATE NOT NULL,
    data_cessazione DATE,
    reparto TEXT,
    ruolo TEXT,
    note TEXT,
    archiviato BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER
)
''')

# Crea la tabella dipendente_competenza
print("Creazione tabella dipendente_competenza...")
c.execute('''
CREATE TABLE dipendente_competenza (
    dipendente_id INTEGER,
    competenza_id INTEGER,
    PRIMARY KEY (dipendente_id, competenza_id),
    FOREIGN KEY (dipendente_id) REFERENCES dipendente (id),
    FOREIGN KEY (competenza_id) REFERENCES competenza (id)
)
''')

# Crea la tabella timbratura
print("Creazione tabella timbratura...")
c.execute('''
CREATE TABLE timbratura (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dipendente_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dipendente_id) REFERENCES dipendente (id)
)
''')

# Crea la tabella prelievo_vestiario
print("Creazione tabella prelievo_vestiario...")
c.execute('''
CREATE TABLE prelievo_vestiario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dipendente_id INTEGER NOT NULL,
    data_prelievo DATE NOT NULL,
    FOREIGN KEY (dipendente_id) REFERENCES dipendente (id)
)
''')

conn.commit()
conn.close()

print("Database ricreato con successo.") 