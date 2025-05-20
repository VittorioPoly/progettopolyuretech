import sqlite3
import os

# Rimuovi il database esistente
db_path = 'app/app.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Database rimosso: {db_path}")

# Crea una nuova connessione al database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Crea la tabella dipendente con i nuovi campi
cursor.execute('''
CREATE TABLE dipendente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL,
    cognome VARCHAR(100) NOT NULL,
    anno_nascita INTEGER NOT NULL,
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
    archiviato BOOLEAN DEFAULT 0
)
''')

# Crea la tabella competenza
cursor.execute('''
CREATE TABLE competenza (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL,
    descrizione TEXT
)
''')

# Crea la tabella dipendente_competenza
cursor.execute('''
CREATE TABLE dipendente_competenza (
    dipendente_id INTEGER,
    competenza_id INTEGER,
    PRIMARY KEY (dipendente_id, competenza_id),
    FOREIGN KEY (dipendente_id) REFERENCES dipendente (id),
    FOREIGN KEY (competenza_id) REFERENCES competenza (id)
)
''')

# Crea la tabella vestiario
cursor.execute('''
CREATE TABLE vestiario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL,
    descrizione TEXT,
    taglia VARCHAR(10),
    quantita INTEGER DEFAULT 0
)
''')

# Crea la tabella prelievo_vestiario
cursor.execute('''
CREATE TABLE prelievo_vestiario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dipendente_id INTEGER,
    vestiario_id INTEGER,
    data_prelievo DATETIME NOT NULL,
    FOREIGN KEY (dipendente_id) REFERENCES dipendente (id),
    FOREIGN KEY (vestiario_id) REFERENCES vestiario (id)
)
''')

# Inserisci alcuni dati di esempio per le competenze
cursor.execute('''
INSERT INTO competenza (nome, descrizione) VALUES
('Saldatura', 'Competenza nella saldatura di materiali'),
('Tornitura', 'Competenza nell''uso del tornio'),
('Fresatura', 'Competenza nell''uso della fresa'),
('Montaggio', 'Competenza nel montaggio di componenti'),
('Controllo Qualità', 'Competenza nel controllo qualità dei prodotti')
''')

# Inserisci alcuni dati di esempio per il vestiario
cursor.execute('''
INSERT INTO vestiario (nome, descrizione, taglia, quantita) VALUES
('Tuta da lavoro', 'Tuta protettiva per lavori in officina', 'M', 50),
('Scarpe antinfortunistiche', 'Scarpe di sicurezza con puntale in acciaio', '42', 30),
('Guanti protettivi', 'Guanti in pelle per lavori pesanti', 'L', 100),
('Casco protettivo', 'Casco di sicurezza per lavori in altezza', 'UNI', 20),
('Occhiali protettivi', 'Occhiali di sicurezza antiurto', 'UNI', 50)
''')

# Commit delle modifiche e chiusura della connessione
conn.commit()
conn.close()

print("Database aggiornato con successo!") 