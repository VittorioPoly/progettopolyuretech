import sqlite3

# Modifica qui se il percorso del tuo database è diverso
DB_PATH = 'app/app.db'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Crea la tabella 'dipendente'
c.execute('''
CREATE TABLE IF NOT EXISTS dipendente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cognome TEXT NOT NULL,
    email TEXT UNIQUE,
    data_assunzione DATE,
    data_cessazione DATE,
    archiviato BOOLEAN DEFAULT 0
)
''')

# Crea altre tabelle necessarie (es. dipendente_competenza, timbratura, prelievo_vestiario, ecc.)
# Esempio:
c.execute('''
CREATE TABLE IF NOT EXISTS dipendente_competenza (
    dipendente_id INTEGER,
    competenza_id INTEGER,
    FOREIGN KEY (dipendente_id) REFERENCES dipendente (id),
    FOREIGN KEY (competenza_id) REFERENCES competenza (id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS timbratura (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dipendente_id INTEGER,
    data_ora TIMESTAMP,
    tipo TEXT,
    FOREIGN KEY (dipendente_id) REFERENCES dipendente (id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS prelievo_vestiario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dipendente_id INTEGER,
    data_prelievo DATE,
    FOREIGN KEY (dipendente_id) REFERENCES dipendente (id)
)
''')

conn.commit()
conn.close()

print("Tabelle create con successo.") 