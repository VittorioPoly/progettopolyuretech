import sqlite3

db_path = 'app/app.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('Colonne della tabella dipendente:')
cursor.execute("PRAGMA table_info(dipendente)")
columns = cursor.fetchall()
for col in columns:
    print(f"- {col[1]} ({col[2]})")

conn.close() 