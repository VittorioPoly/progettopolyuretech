from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Crea tutte le tabelle
    db.create_all()
    
    # Verifica se esiste un utente admin
    admin = User.query.filter_by(username='admin').first()
    if admin is None:
        # Crea un utente amministratore predefinito
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Utente admin creato con successo!')
    else:
        print('Utente admin già esistente')