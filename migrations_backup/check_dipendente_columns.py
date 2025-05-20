import sqlite3

def print_columns():
    print('--- INIZIO SCRIPT ---')
    db_path = 'app/app.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(dipendente)")
    columns = cursor.fetchall()
    print("Colonne della tabella dipendente:")
    for col in columns:
        print(col)
    conn.close()

if __name__ == '__main__':
    print_columns() 