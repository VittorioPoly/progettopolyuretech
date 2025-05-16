import sqlite3

# Modifica qui se il percorso del tuo database è diverso
DB_PATH = 'app/app.db'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Aggiorna data_assunzione
c.execute("""
    UPDATE dipendente
    SET data_assunzione = substr(data_assunzione, 1, 10)
    WHERE data_assunzione IS NOT NULL
""")

# Aggiorna data_cessazione
c.execute("""
    UPDATE dipendente
    SET data_cessazione = substr(data_cessazione, 1, 10)
    WHERE data_cessazione IS NOT NULL
""")

conn.commit()
conn.close()

print('Date conversion complete!') 