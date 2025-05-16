import sqlite3
import os

db_path = os.path.join('app', 'app.db')

def backup_and_recreate_table():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    print("1. Backup dei dati esistenti...")
    try:
        # Backup dei dati esistenti
        cur.execute("SELECT dipendente_id, competenza_id FROM dipendente_competenza")
        existing_data = cur.fetchall()
        print(f"Trovati {len(existing_data)} record da preservare")
        
        # Elimina la tabella esistente
        print("2. Eliminazione della tabella esistente...")
        cur.execute("DROP TABLE IF EXISTS dipendente_competenza")
        
        # Ricrea la tabella con la struttura corretta
        print("3. Ricreazione della tabella con la struttura corretta...")
        cur.execute("""
        CREATE TABLE dipendente_competenza (
            dipendente_id INTEGER NOT NULL,
            competenza_id INTEGER NOT NULL,
            percentuale INTEGER DEFAULT 0,
            PRIMARY KEY (dipendente_id, competenza_id),
            FOREIGN KEY (dipendente_id) REFERENCES dipendente (id),
            FOREIGN KEY (competenza_id) REFERENCES competenza (id)
        )
        """)
        
        # Ripristina i dati
        print("4. Ripristino dei dati...")
        for dipendente_id, competenza_id in existing_data:
            cur.execute(
                "INSERT INTO dipendente_competenza (dipendente_id, competenza_id, percentuale) VALUES (?, ?, 0)",
                (dipendente_id, competenza_id)
            )
        
        conn.commit()
        print("Operazione completata con successo!")
        
        # Verifica finale
        cur.execute("PRAGMA table_info(dipendente_competenza)")
        columns = cur.fetchall()
        print("\nStruttura finale della tabella:")
        for col in columns:
            print(f" - {col[1]} ({col[2]})")
            
    except Exception as e:
        print(f"Errore durante l'operazione: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    backup_and_recreate_table() 