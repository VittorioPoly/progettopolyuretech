import sqlite3
import os

# Modifica qui se il percorso del tuo database è diverso
DB_PATH = 'app/app.db'

# Crea una nuova connessione al database
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Elimina tutte le tabelle correlate
print("Eliminazione delle tabelle...")
c.execute("DROP TABLE IF EXISTS dipendente_competenza")
c.execute("DROP TABLE IF EXISTS timbratura")
c.execute("DROP TABLE IF EXISTS prelievo_vestiario")
c.execute("DROP TABLE IF EXISTS dipendente")

# Ricrea la tabella dipendente con la struttura corretta
print("Ricreazione della tabella dipendente...")
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

# Ricrea la tabella dipendente_competenza
print("Ricreazione della tabella dipendente_competenza...")
c.execute('''
CREATE TABLE dipendente_competenza (
    dipendente_id INTEGER,
    competenza_id INTEGER,
    PRIMARY KEY (dipendente_id, competenza_id),
    FOREIGN KEY (dipendente_id) REFERENCES dipendente (id),
    FOREIGN KEY (competenza_id) REFERENCES competenza (id)
)
''')

conn.commit()
conn.close()

print("Database pulito e ricreato con successo.") 