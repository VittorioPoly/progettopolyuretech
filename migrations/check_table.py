import sqlite3
import os

def check_table():
    db_path = 'app/app.db'
    print(f"Verifico il database in: {db_path}")
    
    if not os.path.exists(db_path):
        print("Il database non esiste!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verifica se la tabella dipendente esiste
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dipendente'")
        if cursor.fetchone():
            print("\nLa tabella dipendente esiste!")
            
            # Mostra la struttura della tabella
            print("\nStruttura della tabella dipendente:")
            cursor.execute("PRAGMA table_info(dipendente)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"- {col[1]} ({col[2]})")
        else:
            print("\nLa tabella dipendente NON esiste!")
        
        conn.close()
    except Exception as e:
        print(f"Errore durante la verifica: {str(e)}")

if __name__ == "__main__":
    check_table() 