from app import create_app, db
from app.models import Dipendente
import os

def recreate_table():
    # Create Flask app and context
    app = create_app()
    with app.app_context():
        # Create a backup of the database
        db_path = 'app/app.db'
        backup_path = f'{db_path}.backup'
        if os.path.exists(db_path):
            with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
                dst.write(src.read())
            print(f"Database backed up to {backup_path}")
        
        try:
            # Drop and recreate the table using SQLAlchemy
            print("Dropping existing table...")
            Dipendente.__table__.drop(db.engine, checkfirst=True)
            
            print("Creating new table...")
            Dipendente.__table__.create(db.engine)
            
            print("Table recreated successfully!")
            
        except Exception as e:
            print(f"Error during table recreation: {str(e)}")
            # Restore from backup if something went wrong
            if os.path.exists(backup_path):
                with open(backup_path, 'rb') as src, open(db_path, 'wb') as dst:
                    dst.write(src.read())
                print("Database restored from backup")
            raise
        finally:
            # Remove backup file if everything went well
            if os.path.exists(backup_path):
                os.remove(backup_path)

if __name__ == '__main__':
    recreate_table() 