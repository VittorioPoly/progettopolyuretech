import sqlite3
from datetime import datetime

# Modifica qui se il percorso del tuo database è diverso
DB_PATH = 'app/app.db'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Recupera i dati dalla tabella dipendente
c.execute("SELECT id, data_assunzione, data_cessazione FROM dipendente")
rows = c.fetchall()

print(f"Trovate {len(rows)} righe da convertire")

# Converti i valori TIMESTAMP in DATE
for row in rows:
    dipendente_id, data_assunzione, data_cessazione = row
    print(f"\nProcessando dipendente_id {dipendente_id}")
    print(f"data_assunzione originale: {data_assunzione}")
    print(f"data_cessazione originale: {data_cessazione}")
    
    if data_assunzione:
        try:
            # Rimuovi i microsecondi se presenti
            if '.' in data_assunzione:
                data_assunzione = data_assunzione.split('.')[0]
            # Converti il timestamp in oggetto datetime
            dt = datetime.strptime(data_assunzione, '%Y-%m-%d %H:%M:%S')
            # Estrai solo la data
            data_assunzione_date = dt.date().isoformat()
            print(f"data_assunzione convertita: {data_assunzione_date}")
            # Aggiorna il database
            c.execute("UPDATE dipendente SET data_assunzione = ? WHERE id = ?", (data_assunzione_date, dipendente_id))
        except ValueError as e:
            print(f"Errore nella conversione di data_assunzione per dipendente_id {dipendente_id}: {e}")
            print(f"Valore problematico: {data_assunzione}")
    
    if data_cessazione:
        try:
            # Rimuovi i microsecondi se presenti
            if '.' in data_cessazione:
                data_cessazione = data_cessazione.split('.')[0]
            # Converti il timestamp in oggetto datetime
            dt = datetime.strptime(data_cessazione, '%Y-%m-%d %H:%M:%S')
            # Estrai solo la data
            data_cessazione_date = dt.date().isoformat()
            print(f"data_cessazione convertita: {data_cessazione_date}")
            # Aggiorna il database
            c.execute("UPDATE dipendente SET data_cessazione = ? WHERE id = ?", (data_cessazione_date, dipendente_id))
        except ValueError as e:
            print(f"Errore nella conversione di data_cessazione per dipendente_id {dipendente_id}: {e}")
            print(f"Valore problematico: {data_cessazione}")

conn.commit()
conn.close()

print("\nConversione completata.") 