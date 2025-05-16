import sqlite3
from datetime import datetime

# Connessione al database
conn = sqlite3.connect('app/app.db')
cursor = conn.cursor()

# Ottieni la struttura della tabella dipendente
cursor.execute("PRAGMA table_info(dipendente)")
columns = cursor.fetchall()
print("Struttura tabella dipendente:")
for col in columns:
    print(col)

# Ottieni tutti i record
cursor.execute("SELECT id, data_assunzione, data_cessazione FROM dipendente")
rows = cursor.fetchall()

# Aggiorna ogni record con il formato corretto della data
for row in rows:
    id, data_assunzione, data_cessazione = row
    
    # Converti data_assunzione
    if data_assunzione and '00:00:00' in data_assunzione:
        try:
            date_obj = datetime.strptime(data_assunzione, '%Y-%m-%d %H:%M:%S.%f')
            new_date = date_obj.strftime('%Y-%m-%d')
            cursor.execute("UPDATE dipendente SET data_assunzione = ? WHERE id = ?", (new_date, id))
        except ValueError as e:
            print(f"Errore nella conversione di data_assunzione per id {id}: {e}")
    
    # Converti data_cessazione
    if data_cessazione and '00:00:00' in data_cessazione:
        try:
            date_obj = datetime.strptime(data_cessazione, '%Y-%m-%d %H:%M:%S.%f')
            new_date = date_obj.strftime('%Y-%m-%d')
            cursor.execute("UPDATE dipendente SET data_cessazione = ? WHERE id = ?", (new_date, id))
        except ValueError as e:
            print(f"Errore nella conversione di data_cessazione per id {id}: {e}")

# Commit delle modifiche
conn.commit()

# Verifica i dati aggiornati
cursor.execute("SELECT id, nome, cognome, data_assunzione, data_cessazione FROM dipendente")
rows = cursor.fetchall()
print("\nDati aggiornati:")
for row in rows:
    print(row)

# Chiudi la connessione
conn.close()

print("\nConversione completata!") 