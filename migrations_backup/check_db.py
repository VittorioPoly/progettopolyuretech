import sqlite3

# Modifica qui se il percorso del tuo database è diverso
DB_PATH = 'app/app.db'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Elenca tutte le tabelle
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = c.fetchall()

if not tables:
    print("Il database è vuoto: non ci sono tabelle.")
else:
    print("Tabelle nel database:")
    for table in tables:
        table_name = table[0]
        c.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = c.fetchone()[0]
        print(f"- {table_name}: {count} righe")

conn.close() 