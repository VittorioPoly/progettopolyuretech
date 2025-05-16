from app import create_app, db
from sqlalchemy import inspect
import sqlite3

app = create_app()

with app.app_context():
    inspector = inspect(db.engine)
    print("Table: dipendente")
    print("Columns:")
    for column in inspector.get_columns('dipendente'):
        print(f"- {column['name']}: {column['type']} (nullable: {column['nullable']})")
    print("\nUnique Constraints:")
    for constraint in inspector.get_unique_constraints('dipendente'):
        print(f"- {constraint}")

db_path = 'app/app.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('Struttura della tabella dipendente_competenza:')
cursor.execute('PRAGMA table_info(dipendente_competenza)')
for col in cursor.fetchall():
    print(f'- {col[1]} ({col[2]})')

conn.close() 