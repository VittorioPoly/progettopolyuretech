#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from app import create_app
from app import db
from app.models import User
from config import config

# Determina quale configurazione usare (sviluppo di default)
config_name = os.environ.get('FLASK_CONFIG') or 'default'
app = create_app(config_name)

if __name__ == '__main__':
    # Avvia il server
    host = app.config.get('SERVER_HOST', '0.0.0.0')
    port = app.config.get('SERVER_PORT', 5000)
    debug = app.config.get('DEBUG', False)
    
    print(f"Avvio server su http://{host}:{port}")
    print(f"Per accedere da altri dispositivi nella rete, usa l'indirizzo IP di questo computer.")
    
    app.run(
        host=host,
        port=port,
        debug=debug
    )
# Crea un contesto dell'applicazione
with app.app_context():
    # Crea le tabelle del database se non esistono
    db.create_all()
    
    # Verifica se esiste già un utente amministratore
    admin = User.query.filter_by(role='admin').first()
    if admin is None:
        # Crea un utente amministratore di default
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin'
        )
        admin.set_password('admin123')  # Password temporanea da cambiare al primo accesso
        db.session.add(admin)
        db.session.commit()
        print('Utente amministratore creato con username: admin e password: admin123')
        print('Si consiglia di cambiare la password al primo accesso!')

@app.cli.command("init-db")
def init_db():
    """Inizializza il database."""
    db.create_all()
    print('Database inizializzato.')

@app.cli.command("create-admin")
def create_admin():
    """Crea un utente amministratore."""
    username = input("Inserisci username: ")
    email = input("Inserisci email: ")
    password = input("Inserisci password: ")
    
    admin = User(
        username=username,
        email=email,
        role='admin'
    )
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    print(f'Utente amministratore {username} creato con successo!')

@app.cli.command("create-operator")
def create_operator():
    """Crea un utente operatore."""
    username = input("Inserisci username: ")
    email = input("Inserisci email: ")
    password = input("Inserisci password: ")
    
    operator = User(
        username=username,
        email=email,
        role='operatore'
    )
    operator.set_password(password)
    db.session.add(operator)
    db.session.commit()
    print(f'Utente operatore {username} creato con successo!')

@app.cli.command("list-users")
def list_users():
    """Elenca tutti gli utenti registrati."""
    users = User.query.all()
    print("Utenti registrati:")
    for user in users:
        print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}, Ruolo: {user.role}")

# Verificare se esiste la cartella uploads e le sue sottocartelle
def check_upload_folders():
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
        print(f"Cartella {upload_folder} creata.")
    
    # Crea sottocartelle
    subfolders = ['images', 'excel', 'pdf']
    for subfolder in subfolders:
        subfolder_path = os.path.join(upload_folder, subfolder)
        if not os.path.exists(subfolder_path):
            os.makedirs(subfolder_path)
            print(f"Sottocartella {subfolder_path} creata.")

if __name__ == '__main__':
    # Verifica le cartelle di upload prima di avviare l'app
    check_upload_folders()
    
    # Determina se usare SSL (HTTPS)
    ssl_context = None
    if config_name == 'production' and app.config.get('SSL_CERT') and app.config.get('SSL_KEY'):
        ssl_context = (app.config['SSL_CERT'], app.config['SSL_KEY'])
        print("Avvio server con SSL (HTTPS) abilitato.")
    
    # Avvia il server
    host = app.config.get('SERVER_HOST', '0.0.0.0')
    port = app.config.get('SERVER_PORT', 5000)
    debug = app.config.get('DEBUG', False)
    
    print(f"Avvio server su http{'s' if ssl_context else ''}://{host}:{port}")
    print(f"Per accedere da altri dispositivi nella rete, usa l'indirizzo IP di questo computer.")
    
    app.run(
        host=host,
        port=port,
        debug=debug,
        ssl_context=ssl_context
    )