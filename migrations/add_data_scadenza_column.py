import sqlite3
import os

def upgrade():
    db_path = os.path.join('app.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        # 1. Crea una tabella temporanea con la nuova struttura
        cursor.execute('''
            CREATE TABLE corsi_formazione_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titolo VARCHAR(100) NOT NULL,
                descrizione TEXT,
                durata_ore INTEGER,
                data_inizio DATETIME,
                data_fine DATETIME,
                data_scadenza DATETIME,
                is_obbligatorio BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by_id INTEGER,
                archiviato BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (created_by_id) REFERENCES users (id)
            )
        ''')
        # 2. Copia i dati dalla vecchia tabella alla nuova (data_scadenza sarà NULL)
        cursor.execute('''
            INSERT INTO corsi_formazione_temp (
                id, titolo, descrizione, durata_ore, data_inizio, data_fine, is_obbligatorio, created_at, created_by_id, archiviato
            )
            SELECT id, titolo, descrizione, durata_ore, data_inizio, data_fine, is_obbligatorio, created_at, created_by_id, archiviato
            FROM corsi_formazione
        ''')
        # 3. Elimina la vecchia tabella
        cursor.execute('DROP TABLE corsi_formazione')
        # 4. Rinomina la tabella temporanea
        cursor.execute('ALTER TABLE corsi_formazione_temp RENAME TO corsi_formazione')
        conn.commit()
        print("Colonna data_scadenza aggiunta con successo.")
    except Exception as e:
        conn.rollback()
        print(f"Errore durante la migrazione: {str(e)}")
        raise e
    finally:
        conn.close()

if __name__ == '__main__':
    upgrade() 