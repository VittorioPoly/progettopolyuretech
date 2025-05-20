import sqlite3

# Modifica qui se il percorso del tuo database è diverso
db_path = 'app/app.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('Tabelle presenti nel database:')
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"- {table[0]}")

conn.close() 