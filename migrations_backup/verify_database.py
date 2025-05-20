import sqlite3
import os

def print_database_info():
    # Percorsi possibili del database
    possible_paths = [
        'app/app.db',
        'instance/app.db',
        'app.db'
    ]
    
    print("Verifica del database:")
    print("-" * 50)
    
    for db_path in possible_paths:
        if os.path.exists(db_path):
            print(f"\nDatabase trovato in: {db_path}")
            print(f"Dimensione: {os.path.getsize(db_path)} bytes")
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Verifica le tabelle
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                print("\nTabelle presenti:")
                for table in tables:
                    print(f"\n- {table[0]}")
                    # Mostra la struttura della tabella
                    cursor.execute(f"PRAGMA table_info({table[0]})")
                    columns = cursor.fetchall()
                    for col in columns:
                        print(f"  * {col[1]} ({col[2]})")
                
                conn.close()
            except sqlite3.Error as e:
                print(f"Errore nell'accesso al database: {e}")
        else:
            print(f"\nDatabase non trovato in: {db_path}")

if __name__ == "__main__":
    print_database_info() 