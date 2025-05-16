import sqlite3
import os
from datetime import datetime

def create_performance_table():
    db_path = os.path.join('app', 'app.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Controlla se la tabella esiste già
    c.execute("""
        SELECT name FROM sqlite_master WHERE type='table' AND name='performance';
    """)
    if c.fetchone():
        print("La tabella 'performance' esiste già.")
        conn.close()
        return

    # Crea la tabella performance
    c.execute("""
        CREATE TABLE performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dipendente_id INTEGER NOT NULL,
            competenza_id INTEGER NOT NULL,
            valutazione INTEGER NOT NULL,
            data DATETIME DEFAULT CURRENT_TIMESTAMP,
            note TEXT,
            FOREIGN KEY(dipendente_id) REFERENCES dipendente(id),
            FOREIGN KEY(competenza_id) REFERENCES competenza(id)
        );
    """)
    conn.commit()
    print("Tabella 'performance' creata con successo.")
    conn.close()

if __name__ == "__main__":
    create_performance_table() 