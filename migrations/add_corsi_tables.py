from app import db
from app.models import CorsoFormazione, PartecipazioneCorso

def upgrade():
    # Create the tables
    db.create_all()

if __name__ == '__main__':
    upgrade()
    print("Tables created successfully!") 