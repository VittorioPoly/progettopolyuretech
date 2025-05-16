import sqlite3
import os

# Percorso del database
db_path = 'app/app.db'

# Se il database esiste, lo rimuovo per ricrearlo da zero
if os.path.exists(db_path):
    os.remove(db_path)

# Creo una nuova connessione al database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Creo la tabella dipendente con tutte le colonne necessarie
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

# Creo un indice univoco sulla colonna matricola
cursor.execute('''
CREATE UNIQUE INDEX ix_dipendente_matricola ON dipendente (matricola)
''')

# Commit delle modifiche
conn.commit()

# Chiudo la connessione
conn.close()

print("Tabella dipendente ricreata con successo.") 