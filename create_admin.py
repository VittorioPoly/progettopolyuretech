from app import create_app, db
from app.models import User

# Crea un'istanza dell'applicazione Flask per avere il contesto dell'app
app = create_app()

def add_admin_user():
    with app.app_context():
        # Controlla se l'utente admin esiste già
        if User.query.filter_by(username='admin').first() is None:
            admin_user = User(username='admin', email='admin@example.com', role='admin')
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("Utente admin creato con successo con username 'admin' e password 'admin123'.")
        else:
            print("L'utente admin esiste già.")

if __name__ == '__main__':
    add_admin_user() 