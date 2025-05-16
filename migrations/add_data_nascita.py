from app import db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

def migrate():
    # Get the database URL from the Flask app config
    db_path = 'app/app.db'
    
    # Create engine and session
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Add the new column
        print("Adding data_nascita column...")
        engine.execute('ALTER TABLE dipendente ADD COLUMN data_nascita DATE')
        print("Column added successfully!")
        
        # Commit the changes
        session.commit()
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == '__main__':
    migrate() 