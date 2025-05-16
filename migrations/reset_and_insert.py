import sqlite3

# Connessione al database
conn = sqlite3.connect('app/app.db')
cursor = conn.cursor()

# Svuota la tabella dipendente
cursor.execute("DELETE FROM dipendente")
print("Tabella dipendente svuotata.")

# Dati di test
test_data = [
    ('Mario', 'Rossi', 'mario.rossi@example.com', '1234567890', '2020-01-01', None, 'Produzione', 'Operaio', 'Dipendente di prova 1', 0),
    ('Luigi', 'Verdi', 'luigi.verdi@example.com', '0987654321', '2019-06-15', None, 'Amministrazione', 'Impiegato', 'Dipendente di prova 2', 0),
    ('Anna', 'Bianchi', 'anna.bianchi@example.com', '5555555555', '2021-03-10', None, 'Risorse Umane', 'Manager', 'Dipendente di prova 3', 0),
    ('Paolo', 'Neri', 'paolo.neri@example.com', '4444444444', '2018-11-20', '2023-12-31', 'Vendite', 'Rappresentante', 'Dipendente di prova 4', 1)
]

# Inserisci i dati di test
for data in test_data:
    cursor.execute("""
        INSERT INTO dipendente (nome, cognome, email, telefono, data_assunzione, data_cessazione, reparto, ruolo, note, archiviato)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)

# Commit delle modifiche
conn.commit()

# Verifica i dati inseriti
cursor.execute("SELECT id, nome, cognome, data_assunzione, data_cessazione FROM dipendente")
rows = cursor.fetchall()
print("\nDati inseriti:")
for row in rows:
    print(row)

# Chiudi la connessione
conn.close()

print("\nReset e inserimento completati!") 