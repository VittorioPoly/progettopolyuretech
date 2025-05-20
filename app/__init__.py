import os
from datetime import datetime
from flask import Flask, session, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_session import Session

# Inizializzazione delle estensioni
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()
session_extension = Session()  # Rinominato per evitare conflitti con flask.session

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Carica la configurazione da config.py
    from config import config
    app.config.from_object(config[config_name])
    
    # Assicurati che le cartelle di upload esistano
    init_upload_folders(app)
    
    # Inizializza le estensioni
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    session_extension.init_app(app)  # Usa session_extension invece di session
    
    # Configura il login_manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Effettua il login per accedere a questa pagina.'
    login_manager.login_message_category = 'warning'
    
    # Registra i modelli
    with app.app_context():
        from app import models
    
    # Importa e registra le rotte
    from app.routes import register_routes
    register_routes(app)
    
    # Registra gli error handler
    register_error_handlers(app)
    
    # Registra i filtri Jinja2
    register_jinja_filters(app)

    # Registra il context processor per i dati globali
    @app.context_processor
    def inject_globals():
        return {
            'theme': 'light',  # valore di default
            'app_name': 'Gestionale Aziendale',
            'current_year': datetime.utcnow().year
        }
    
    return app
    
# Funzioni di supporto
def init_upload_folders(app):
    # Crea le cartelle di upload se non esistono
    upload_folders = [
        app.config.get('UPLOAD_FOLDER', 'app/static/uploads'),
        app.config.get('UPLOAD_IMAGES_FOLDER', 'app/static/uploads/images'),
        app.config.get('UPLOAD_EXCEL_FOLDER', 'app/static/uploads/excel'),
        app.config.get('UPLOAD_PDF_FOLDER', 'app/static/uploads/pdf')
    ]
    
    for folder in upload_folders:
        if not os.path.exists(folder):
            os.makedirs(folder)

def register_error_handlers(app):
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html', title='Pagina non trovata'), 404
    
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html', title='Accesso negato'), 403
    
    @app.errorhandler(500)
    def internal_server_error(e):
        db.session.rollback()  # Rollback in caso di errore del database
        return render_template('errors/500.html', title='Errore del server'), 500

def register_jinja_filters(app):
    """Registra filtri Jinja2 personalizzati"""
    @app.template_filter('format_date')
    def format_date(value, format='%d/%m/%Y'):
        """Formatta una data nel formato italiano"""
        if value:
            return value.strftime(format)
        return ""
    
    @app.template_filter('format_currency')
    def format_currency(value):
        """Formatta un valore come valuta"""
        if value is not None:
            return f"€ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return "€ 0,00"
    
    @app.template_filter('truncate_text')
    def truncate_text(text, length=100):
        """Tronca il testo alla lunghezza specificata"""
        if text and len(text) > length:
            return text[:length] + "..."
        return text if text else ""