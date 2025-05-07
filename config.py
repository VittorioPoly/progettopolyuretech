import os
from datetime import timedelta

# Ottiene il percorso base dell'applicazione
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Configurazione di base
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chiave-segreta-molto-difficile-da-indovinare'
    
    # Configurazione SQLite Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurazione upload file
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    UPLOAD_IMAGES_FOLDER = os.path.join(UPLOAD_FOLDER, 'images')
    UPLOAD_EXCEL_FOLDER = os.path.join(UPLOAD_FOLDER, 'excel')
    UPLOAD_PDF_FOLDER = os.path.join(UPLOAD_FOLDER, 'pdf')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Limita upload a 16MB
    
    # Estensioni consentite
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    ALLOWED_EXCEL_EXTENSIONS = {'xlsx', 'xls'}
    
    # Configurazione sessione
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)  # Durata sessione attiva
    SESSION_TYPE = 'filesystem'
    
    # Configurazione email (per eventuale recupero password)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.example.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')
    
    # Configurazione per la sicurezza
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 ora
    
    # Configurazione logging
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Configurazione per l'accesso da rete
    SERVER_HOST = '0.0.0.0'  # Accetta connessioni da qualsiasi IP
    SERVER_PORT = int(os.environ.get('PORT', 5000))
    
    # Configurazione PDF
    PDF_FONT_DIR = os.path.join(basedir, 'app', 'static', 'fonts')
    
    # Impostazioni di debug (da disattivare in produzione)
    DEBUG = os.environ.get('FLASK_DEBUG') or True


class DevelopmentConfig(Config):
    DEBUG = True
    

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'test.db')
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    
    # In produzione, usa una chiave segreta più forte dall'ambiente
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'genera-una-chiave-segreta-molto-robusta'
    
    # Configurazione SSL (per HTTPS)
    SSL_CERT = os.environ.get('SSL_CERT')
    SSL_KEY = os.environ.get('SSL_KEY')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}