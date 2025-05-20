from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from app import db, login_manager

# Tabella di associazione per relazione many-to-many tra dipendenti e competenze
# dipendente_competenza = db.Table('dipendente_competenza',
#     db.Column('dipendente_id', db.Integer, db.ForeignKey('dipendente.id'), primary_key=True),
#     db.Column('competenza_id', db.Integer, db.ForeignKey('competenza.id'), primary_key=True)
# )

class User(UserMixin, db.Model):
    """Modello per gli utenti del sistema con gestione dei ruoli"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120))
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='operatore')  # 'operatore' o 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relazioni
    modulo1_entries = db.relationship('Modulo1Entry', 
                               backref='author', 
                               lazy='dynamic',
                               foreign_keys='Modulo1Entry.user_id')
    modulo5_entries = db.relationship('Modulo5Entry', 
                               backref='author', 
                               lazy='dynamic',
                               foreign_keys='Modulo5Entry.user_id')
    
    def set_password(self, password):
        """Imposta la password criptata"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Verifica la password"""
        return check_password_hash(self.password_hash, password)
        
    def is_admin(self):
        """Verifica se l'utente è un amministratore"""
        return self.role == 'admin'
    
    def is_operatore(self):
        """Verifica se l'utente è un operatore"""
        return self.role == 'operatore'
    
    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(id):
    """Funzione necessaria per flask-login"""
    return User.query.get(int(id))


# Modulo 1 e 5: Inserimento dati con foto
class Modulo1Entry(db.Model):
    """Modello per i dati inseriti nel Modulo 1"""
    __tablename__ = 'modulo1_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    valore_numerico = db.Column(db.Float, nullable=False)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    viewed = db.Column(db.Boolean, default=False)
    viewed_at = db.Column(db.DateTime)
    viewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relazione con le foto
    photos = db.relationship('Modulo1Photo', backref='entry', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Modulo1Entry {self.id}>'


class Modulo1Photo(db.Model):
    """Modello per le foto allegate a un'entry del Modulo 1"""
    __tablename__ = 'modulo1_photos'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(128), nullable=False)
    path = db.Column(db.String(256), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text)
    entry_id = db.Column(db.Integer, db.ForeignKey('modulo1_entries.id'), nullable=False)
    
    def __repr__(self):
        return f'<Modulo1Photo {self.filename}>'


# Modulo 5: Ricalca lo stesso schema del Modulo 1
class Modulo5Entry(db.Model):
    """Modello per i dati inseriti nel Modulo 5"""
    __tablename__ = 'modulo5_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    valore_numerico = db.Column(db.Float, nullable=False)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    viewed = db.Column(db.Boolean, default=False)
    viewed_at = db.Column(db.DateTime)
    viewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relazione con le foto
    photos = db.relationship('Modulo5Photo', backref='entry', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Modulo5Entry {self.id}>'


class Modulo5Photo(db.Model):
    """Modello per le foto allegate a un'entry del Modulo 5"""
    __tablename__ = 'modulo5_photos'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(128), nullable=False)
    path = db.Column(db.String(256), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text)
    entry_id = db.Column(db.Integer, db.ForeignKey('modulo5_entries.id'), nullable=False)
    
    def __repr__(self):
        return f'<Modulo5Photo {self.filename}>'


# Modulo 2: Analisi fatturato clienti (solo admin)
class Cliente(db.Model):
    """Modello per i clienti"""
    __tablename__ = 'clienti'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(128), nullable=False, index=True)
    codice = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120))
    telefono = db.Column(db.String(20))
    indirizzo = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relazione con i fatturati
    fatturati = db.relationship('Fatturato', backref='cliente', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Cliente {self.nome}>'


class Fatturato(db.Model):
    """Modello per i dati di fatturato"""
    __tablename__ = 'fatturati'
    
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.DateTime, nullable=False, index=True)
    importo = db.Column(db.Float, nullable=False)
    descrizione = db.Column(db.Text)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clienti.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __repr__(self):
        return f'<Fatturato {self.data} {self.importo}>'


# Modulo 3: Analisi spese fornitori (solo admin)
class Fornitore(db.Model):
    """Modello per i fornitori"""
    __tablename__ = 'fornitori'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(128), nullable=False, index=True)
    codice = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120))
    telefono = db.Column(db.String(20))
    indirizzo = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relazione con le spese
    spese = db.relationship('Spesa', backref='fornitore', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Fornitore {self.nome}>'


class Spesa(db.Model):
    """Modello per i dati di spesa"""
    __tablename__ = 'spese'
    
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.DateTime, nullable=False, index=True)
    importo = db.Column(db.Float, nullable=False)
    descrizione = db.Column(db.Text)
    fornitore_id = db.Column(db.Integer, db.ForeignKey('fornitori.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __repr__(self):
        return f'<Spesa {self.data} {self.importo}>'


# Modulo 4: Generazione PDF (solo admin)
class Modulo4Entry(db.Model):
    """Modello per i dati inseriti nel Modulo 4 per generazione PDF"""
    __tablename__ = 'modulo4_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    titolo = db.Column(db.String(128), nullable=False)
    valore1 = db.Column(db.Float)
    valore2 = db.Column(db.Float)
    valore3 = db.Column(db.Float)
    note = db.Column(db.Text)
    pdf_path = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<Modulo4Entry {self.id}>'


# Modulo 6 e 7: Inserimento dati con riepilogo (solo admin)
class Modulo6Entry(db.Model):
    """Modello per i dati inseriti nel Modulo 6"""
    __tablename__ = 'modulo6_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    valore1 = db.Column(db.Float, nullable=False)
    valore2 = db.Column(db.Float)
    valore3 = db.Column(db.Float)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    viewed = db.Column(db.Boolean, default=False)
    viewed_at = db.Column(db.DateTime)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<Modulo6Entry {self.id}>'


class Modulo7Entry(db.Model):
    """Modello per i dati inseriti nel Modulo 7"""
    __tablename__ = 'modulo7_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    valore1 = db.Column(db.Float, nullable=False)
    valore2 = db.Column(db.Float)
    valore3 = db.Column(db.Float)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    viewed = db.Column(db.Boolean, default=False)
    viewed_at = db.Column(db.DateTime)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<Modulo7Entry {self.id}>'


# Modulo 8: Gestione dipendenti e competenze (solo admin)
class Dipendente(db.Model):
    """Modello per i dipendenti dell'azienda"""
    __tablename__ = 'dipendente'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cognome = db.Column(db.String(100), nullable=False)
    data_nascita = db.Column(db.Date, nullable=False)
    luogo_nascita = db.Column(db.String(100), nullable=False)
    provincia_nascita = db.Column(db.String(2), nullable=False)
    codice_fiscale = db.Column(db.String(16))
    email = db.Column(db.String(120))
    telefono = db.Column(db.String(20))
    matricola = db.Column(db.String(20), unique=True)
    reparto = db.Column(db.String(100))
    ruolo = db.Column(db.String(100))
    data_assunzione_somministrazione = db.Column(db.Date)
    agenzia_somministrazione = db.Column(db.String(100))
    data_assunzione_indeterminato = db.Column(db.Date)
    legge_104 = db.Column(db.Boolean, default=False)
    donatore_avis = db.Column(db.Boolean, default=False)
    indirizzo_residenza = db.Column(db.String(200))
    citta_residenza = db.Column(db.String(100))
    provincia_residenza = db.Column(db.String(2))
    cap_residenza = db.Column(db.String(5))
    data_cessazione = db.Column(db.Date)
    note = db.Column(db.Text)
    archiviato = db.Column(db.Boolean, default=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    created_by = db.relationship('User', backref='dipendenti_creati')

    competenze = db.relationship('Competenza', 
                               secondary='dipendente_competenza',
                               backref=db.backref('dipendenti', lazy='dynamic'))
    competenze_associate = db.relationship('DipendenteCompetenza', 
                                         back_populates='dipendente',
                                         overlaps="competenze,dipendenti")
    vestiario = db.relationship('Inventory', 
                              secondary='prelievi_vestiario', 
                              backref='dipendenti')
    performance = db.relationship('Performance', back_populates='dipendente', cascade='all, delete-orphan')

    @property
    def data_assunzione_date(self):
        """Restituisce solo la data di assunzione senza l'orario"""
        return self.data_assunzione.date() if self.data_assunzione else None
    
    @property
    def data_cessazione_date(self):
        """Restituisce solo la data di cessazione senza l'orario"""
        return self.data_cessazione.date() if self.data_cessazione else None
    
    def __repr__(self):
        return f'<Dipendente {self.nome} {self.cognome}>'


class Competenza(db.Model):
    """Modello per le competenze dei dipendenti"""
    __tablename__ = 'competenza'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(64), nullable=False, unique=True)
    descrizione = db.Column(db.Text)
    livello = db.Column(db.String(20))  # base, intermedio, avanzato
    area = db.Column(db.String(64))     # tecnica, amministrativa, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    dipendenti_associati = db.relationship('DipendenteCompetenza', 
                                         back_populates='competenza',
                                         overlaps="competenze,dipendenti")
    performance = db.relationship('Performance', back_populates='competenza', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Competenza {self.nome}>'


class DipendenteCompetenza(db.Model):
    __tablename__ = 'dipendente_competenza'
    dipendente_id = db.Column(db.Integer, db.ForeignKey('dipendente.id'), primary_key=True)
    competenza_id = db.Column(db.Integer, db.ForeignKey('competenza.id'), primary_key=True)
    percentuale = db.Column(db.Integer, default=0)  # Valore da 0 a 100

    dipendente = db.relationship('Dipendente', 
                               back_populates='competenze_associate',
                               overlaps="competenze,dipendenti")
    competenza = db.relationship('Competenza', 
                               back_populates='dipendenti_associati',
                               overlaps="competenze,dipendenti")

# ==== Modulo 8: Timbrature ====
class Timbratura(db.Model):
    __tablename__ = 'timbrature'
    id = db.Column(db.Integer, primary_key=True)
    dipendente_id = db.Column(db.Integer, db.ForeignKey('dipendente.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)         # 'entrata1','uscita1','entrata2','uscita2'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Timbratura d{self.dipendente_id} {self.tipo} @ {self.timestamp}>'

# ==== Modulo 8: Vestiario / Magazzino ====
class Inventory(db.Model):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(128), nullable=False)
    taglia = db.Column(db.String(64))                        # facoltativa
    quantita = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self):
        return f'<Inventory {self.nome} ({self.taglia}) x{self.quantita}>'

# registro di ogni prelievo di vestiario
class PrelievoVestiario(db.Model):
    __tablename__ = 'prelievi_vestiario'
    id = db.Column(db.Integer, primary_key=True)
    dipendente_id = db.Column(db.Integer, db.ForeignKey('dipendente.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    quantita = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    dipendente = db.relationship('Dipendente', backref='prelievi_vestiario')
    item = db.relationship('Inventory')

    def __repr__(self):
        return f'<PrelievoVestiario d{self.dipendente_id} i{self.item_id} x{self.quantita}>'
# Per il tuo import in modulo8.py
VestiarioItem = Inventory

# Modulo 9: Analisi dati da Excel (solo admin)
class DatiExcel(db.Model):
    """Modello per i dati importati da Excel nel Modulo 9"""
    __tablename__ = 'dati_excel'
    
    id = db.Column(db.Integer, primary_key=True)
    nome_file = db.Column(db.String(128), nullable=False)
    descrizione = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relazione con i dati
    records = db.relationship('RecordExcel', backref='file_origine', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<DatiExcel {self.nome_file}>'


class RecordExcel(db.Model):
    """Modello per i singoli record importati da Excel nel Modulo 9"""
    __tablename__ = 'record_excel'
    
    id = db.Column(db.Integer, primary_key=True)
    colonna1 = db.Column(db.String(128))
    colonna2 = db.Column(db.String(128))
    colonna3 = db.Column(db.Float)
    colonna4 = db.Column(db.Float)
    colonna5 = db.Column(db.DateTime)
    colonna6 = db.Column(db.String(256))
    dati_excel_id = db.Column(db.Integer, db.ForeignKey('dati_excel.id'), nullable=False)
    
    def __repr__(self):
        return f'<RecordExcel {self.id}>'

class Performance(db.Model):
    """Modello per le performance dei dipendenti"""
    __tablename__ = 'performance'
    
    id = db.Column(db.Integer, primary_key=True)
    dipendente_id = db.Column(db.Integer, db.ForeignKey('dipendente.id'), nullable=False)
    competenza_id = db.Column(db.Integer, db.ForeignKey('competenza.id'), nullable=False)
    valutazione = db.Column(db.Integer, nullable=False)  # percentuale da 0 a 100
    data = db.Column(db.DateTime, default=datetime.utcnow)
    note = db.Column(db.Text)
    
    dipendente = db.relationship('Dipendente', back_populates='performance')
    competenza = db.relationship('Competenza', back_populates='performance')
    
    def __repr__(self):
        return f'<Performance {self.dipendente.nome} {self.competenza.nome} {self.valutazione}%>'

class TrainingCourse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completions = db.relationship('CourseCompletion', backref='course', lazy=True)

class CourseCompletion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('training_course.id'), nullable=False)
    dipendente_id = db.Column(db.Integer, db.ForeignKey('dipendente.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, completed, in_progress

    dipendente = db.relationship('Dipendente')

class CorsoFormazione(db.Model):
    __tablename__ = 'corsi_formazione'
    
    id = db.Column(db.Integer, primary_key=True)
    titolo = db.Column(db.String(100), nullable=False)
    descrizione = db.Column(db.Text)
    durata_ore = db.Column(db.Integer)
    data_inizio = db.Column(db.DateTime)
    data_fine = db.Column(db.DateTime)
    data_scadenza = db.Column(db.DateTime)  # nuova colonna per la scadenza
    is_obbligatorio = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    archiviato = db.Column(db.Boolean, default=False)
    
    # Relazioni
    created_by = db.relationship('User', backref='corsi_creati')
    partecipanti = db.relationship('PartecipazioneCorso', back_populates='corso', cascade='all, delete-orphan')

class PartecipazioneCorso(db.Model):
    __tablename__ = 'partecipazioni_corsi'
    
    id = db.Column(db.Integer, primary_key=True)
    dipendente_id = db.Column(db.Integer, db.ForeignKey('dipendente.id'), nullable=False)
    corso_id = db.Column(db.Integer, db.ForeignKey('corsi_formazione.id'), nullable=False)
    stato = db.Column(db.String(20), default='da_iniziare')  # da_iniziare, in_corso, completato
    data_completamento = db.Column(db.DateTime)
    valutazione = db.Column(db.Integer)  # 1-5
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relazioni
    dipendente = db.relationship('Dipendente', backref='partecipazioni_corsi')
    corso = db.relationship('CorsoFormazione', back_populates='partecipanti')