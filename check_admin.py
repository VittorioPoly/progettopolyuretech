from app import db, create_app
from app.models import User

app = create_app()
with app.app_context():
    # Verifica se esiste già un utente admin
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print(f"Utente admin trovato: {admin.username}, email: {admin.email}, ruolo: {admin.role}")
    else:
        print("Utente admin non trovato, lo creo...")
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Utente admin creato con successo!") 