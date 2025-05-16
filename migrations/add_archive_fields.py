from app import create_app, db
from datetime import datetime
from sqlalchemy import text

def upgrade():
    app = create_app()
    with app.app_context():
        # Add new columns
        db.session.execute(text('ALTER TABLE dipendente ADD COLUMN data_cessazione DATE'))
        db.session.execute(text('ALTER TABLE dipendente ADD COLUMN archiviato BOOLEAN DEFAULT FALSE'))
        
        # Update existing records
        db.session.execute(text('UPDATE dipendente SET archiviato = FALSE WHERE archiviato IS NULL'))
        
        # Commit the changes
        db.session.commit()

def downgrade():
    app = create_app()
    with app.app_context():
        # Remove the columns
        db.session.execute(text('ALTER TABLE dipendente DROP COLUMN data_cessazione'))
        db.session.execute(text('ALTER TABLE dipendente DROP COLUMN archiviato'))
        
        # Commit the changes
        db.session.commit()

if __name__ == '__main__':
    upgrade() 