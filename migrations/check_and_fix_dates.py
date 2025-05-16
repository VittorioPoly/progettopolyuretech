import sqlite3
from datetime import datetime

# Connessione al database
conn = sqlite3.connect('app/app.db')
cursor = conn.cursor()

print("Controllo delle date nel database...\n")

# Controlla e mostra le date problematiche
cursor.execute("""
    SELECT id, nome, cognome, data_assunzione, data_cessazione 
    FROM dipendente 
    WHERE data_assunzione IS NOT NULL 
       OR data_cessazione IS NOT NULL
""")
rows = cursor.fetchall()

print("Date trovate nel database:")
for row in rows:
    print(f"ID: {row[0]}, Nome: {row[1]} {row[2]}")
    print(f"  Data assunzione: {row[3]}")
    print(f"  Data cessazione: {row[4]}\n")

# Converti tutte le date nel formato corretto
print("Conversione delle date in corso...")
for row in rows:
    id, _, _, data_assunzione, data_cessazione = row
    
    # Converti data_assunzione
    if data_assunzione:
        try:
            # Prova prima il formato con microsecondi
            try:
                date_obj = datetime.strptime(data_assunzione, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                # Se fallisce, prova il formato senza microsecondi
                date_obj = datetime.strptime(data_assunzione, '%Y-%m-%d %H:%M:%S')
            
            new_date = date_obj.strftime('%Y-%m-%d')
            cursor.execute("UPDATE dipendente SET data_assunzione = ? WHERE id = ?", (new_date, id))
            print(f"Convertita data assunzione per ID {id}: {data_assunzione} -> {new_date}")
        except ValueError as e:
            print(f"Errore nella conversione di data_assunzione per id {id}: {e}")
    
    # Converti data_cessazione
    if data_cessazione:
        try:
            # Prova prima il formato con microsecondi
            try:
                date_obj = datetime.strptime(data_cessazione, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                # Se fallisce, prova il formato senza microsecondi
                date_obj = datetime.strptime(data_cessazione, '%Y-%m-%d %H:%M:%S')
            
            new_date = date_obj.strftime('%Y-%m-%d')
            cursor.execute("UPDATE dipendente SET data_cessazione = ? WHERE id = ?", (new_date, id))
            print(f"Convertita data cessazione per ID {id}: {data_cessazione} -> {new_date}")
        except ValueError as e:
            print(f"Errore nella conversione di data_cessazione per id {id}: {e}")

# Commit delle modifiche
conn.commit()
print("\nConversione completata!")

# Mostra tutti i dati aggiornati
print("\nDati attuali nel database:")
cursor.execute("SELECT id, nome, cognome, data_assunzione, data_cessazione FROM dipendente")
rows = cursor.fetchall()
for row in rows:
    print(f"ID: {row[0]}, Nome: {row[1]} {row[2]}")
    print(f"  Data assunzione: {row[3]}")
    print(f"  Data cessazione: {row[4]}\n")

# Chiudi la connessione
conn.close() 