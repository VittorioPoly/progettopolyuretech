import sqlite3

conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# Elimina la tabella se esiste
cursor.execute('DROP TABLE IF EXISTS corsi_formazione')

# Crea la tabella corsi_formazione con tutte le colonne, inclusa archiviato
cursor.execute('''
CREATE TABLE corsi_formazione (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titolo VARCHAR(100) NOT NULL,
    descrizione TEXT,
    durata_ore INTEGER,
    data_inizio DATETIME,
    data_fine DATETIME,
    is_obbligatorio BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER,
    archiviato BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (created_by_id) REFERENCES users (id)
)
''')

conn.commit()
conn.close()
print("Tabella corsi_formazione ricreata con successo.") 