from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, Table, select
from sqlalchemy.orm import relationship, column_property
from app import db, login_manager
from sqlalchemy.ext.hybrid import hybrid_property

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
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='operatore')  # 'operatore' o 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    modules = db.Column(db.String(255), default='')  # Lista di moduli accessibili separati da virgola
    
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
    
    def has_module_access(self, module_id):
        """Verifica se l'utente ha accesso al modulo specificato"""
        if self.is_admin:
            return True
        return str(module_id) in self.modules.split(',')
    
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
class Dipendente(UserMixin, db.Model):
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
    mansione_id = db.Column(db.Integer, db.ForeignKey('mansione.id'), nullable=True)
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
                                         cascade='all, delete-orphan',
                                         overlaps="competenze,dipendenti")
    prelievi_vestiario = db.relationship('PrelievoVestiario', 
                               back_populates='dipendente',  # Modificato da backref
                               lazy='dynamic', 
                               cascade="all, delete-orphan")
    
    performance = db.relationship('Performance', back_populates='dipendente', cascade='all, delete-orphan')
    partecipazioni_corsi = db.relationship('PartecipazioneCorso', backref='dipendente', lazy='dynamic', cascade='all, delete-orphan')
    contratti = db.relationship('Contratto', 
                              back_populates='dipendente',  # Modificato da backref
                              lazy='dynamic', 
                              cascade="all, delete-orphan")
    prelievi_dpi = db.relationship('PrelievoDPI', backref='dipendente', lazy='dynamic', cascade="all, delete-orphan")
    mansione = db.relationship('Mansione', back_populates='dipendenti')

    # Aggiungiamo la relazione corretta per corsi_sicurezza
    corsi_sicurezza = db.relationship('CorsoSicurezza', 
                                    secondary='dipendente_corso_sicurezza', 
                                    lazy='dynamic',
                                    back_populates='dipendenti')

    @property
    def data_assunzione_date(self):
        if self.data_assunzione_indeterminato:
            return self.data_assunzione_indeterminato
        return self.data_assunzione_somministrazione

    @property
    def data_cessazione_date(self):
        return self.data_cessazione
    
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
    dipendente_id = db.Column(db.Integer, db.ForeignKey('dipendente.id', name='fk_timbratura_dipendente'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # 'entrata' o 'uscita'
    modificato_da = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_timbratura_modificatore'))
    data_modifica = db.Column(db.DateTime)
    
    dipendente = db.relationship('Dipendente', backref=db.backref('timbrature', lazy=True))
    modificatore = db.relationship('User', backref=db.backref('timbrature_modificate', lazy=True))

class RichiestaFerie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dipendente_id = db.Column(db.Integer, db.ForeignKey('dipendente.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'ferie', 'rol', 'ex_festivita'
    data_inizio = db.Column(db.Date, nullable=False)
    data_fine = db.Column(db.Date, nullable=False)
    ore = db.Column(db.Float, nullable=False)
    stato = db.Column(db.String(20), default='in_attesa')  # 'in_attesa', 'approvata', 'rifiutata'
    note = db.Column(db.String(200))
    data_richiesta = db.Column(db.DateTime, default=datetime.utcnow)
    approvato_da = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_richiesta_ferie_approvato_da'))
    data_approvazione = db.Column(db.DateTime)

    dipendente = db.relationship('Dipendente', backref='richieste_ferie')
    approvatore = db.relationship('User', backref='ferie_approvate')

class ResiduoFerie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dipendente_id = db.Column(db.Integer, db.ForeignKey('dipendente.id'), nullable=False)
    anno = db.Column(db.Integer, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'ferie', 'rol', 'ex_festivita'
    ore_totali = db.Column(db.Float, nullable=False)
    ore_usate = db.Column(db.Float, default=0)
    ore_residue = db.Column(db.Float, nullable=False)

    dipendente = db.relationship('Dipendente', backref='residui_ferie')

    __table_args__ = (
        db.UniqueConstraint('dipendente_id', 'anno', 'tipo', name='unique_residuo'),
    )

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
    data_prelievo = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    dipendente = db.relationship('Dipendente', back_populates='prelievi_vestiario')
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
    __tablename__ = 'corso_formazione'
    id = db.Column(db.Integer, primary_key=True)
    titolo = db.Column(db.String(100), nullable=False)
    descrizione = db.Column(db.Text)
    durata_ore = db.Column(db.Integer)
    giorno_inizio = db.Column(db.Date)
    giorno_fine = db.Column(db.Date, nullable=True)
    scadenza_relativa = db.Column(db.String(50), nullable=True) # es. "1 anno", "6 mesi"
    is_obbligatorio = db.Column(db.Boolean, default=False)
    archiviato = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    partecipazioni = db.relationship('PartecipazioneCorso', backref='corso', lazy=True)
    created_by = db.relationship('User')

class PartecipazioneCorso(db.Model):
    __tablename__ = 'partecipazione_corso'
    id = db.Column(db.Integer, primary_key=True)
    dipendente_id = db.Column(db.Integer, db.ForeignKey('dipendente.id'), nullable=False)
    corso_id = db.Column(db.Integer, db.ForeignKey('corso_formazione.id'), nullable=False)
    stato = db.Column(db.String(20), default='da_iniziare')  # da_iniziare, in_corso, completato
    data_iscrizione = db.Column(db.DateTime, default=datetime.utcnow)
    data_completamento = db.Column(db.DateTime)
    valutazione = db.Column(db.Integer)  # 1-5 stelle

class CorsoSicurezza(db.Model):
    __tablename__ = 'corso_sicurezza'
    id = db.Column(db.Integer, primary_key=True)
    titolo = db.Column(db.String(100), nullable=False)
    descrizione = db.Column(db.Text)
    durata_ore = db.Column(db.Integer)
    data_scadenza = db.Column(db.Date)
    is_completato = db.Column(db.Boolean, default=False)
    data_completamento = db.Column(db.DateTime)
    archiviato = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Aggiungiamo la relazione corretta per dipendenti
    dipendenti = db.relationship('Dipendente', 
                                 secondary='dipendente_corso_sicurezza', 
                                 lazy='dynamic',
                                 back_populates='corsi_sicurezza')

# Tabella di associazione per dipendenti e corsi di sicurezza
dipendente_corso_sicurezza = db.Table('dipendente_corso_sicurezza',
    db.Column('dipendente_id', db.Integer, db.ForeignKey('dipendente.id'), primary_key=True),
    db.Column('corso_id', db.Integer, db.ForeignKey('corso_sicurezza.id'), primary_key=True)
)

class RichiestaPermesso(db.Model):
    __tablename__ = 'richiesta_permesso'
    
    id = db.Column(db.Integer, primary_key=True)
    dipendente_id = db.Column(db.Integer, db.ForeignKey('dipendente.id'), nullable=False)
    data_inizio = db.Column(db.Date, nullable=False)
    data_fine = db.Column(db.Date, nullable=False)
    ore = db.Column(db.Float, nullable=False)
    motivo = db.Column(db.String(500), nullable=False)
    stato = db.Column(db.String(20), default='in_attesa')  # in_attesa, approvata, rifiutata
    data_richiesta = db.Column(db.DateTime, default=datetime.utcnow)
    approvato_da = db.Column(db.Integer, db.ForeignKey('users.id'))
    data_approvazione = db.Column(db.DateTime)

    dipendente_ref = db.relationship('Dipendente', foreign_keys=[dipendente_id], backref='richieste_permesso_dipendente')
    approvatore = db.relationship('User', foreign_keys=[approvato_da], backref='permessi_approvati_da_utente')

class Mansione(db.Model):
    __tablename__ = 'mansione'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descrizione = db.Column(db.Text, nullable=True)
    dipendenti = db.relationship('Dipendente', back_populates='mansione', lazy='dynamic')

    def __repr__(self):
        return f'<Mansione {self.nome}>'

# Nuovo modello per DPI
class DPI(db.Model):
    __tablename__ = 'dpi'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    descrizione = db.Column(db.Text, nullable=True)
    categoria = db.Column(db.String(100), nullable=True)
    fornitore = db.Column(db.String(150), nullable=True)
    codice = db.Column(db.String(50), nullable=True)
    taglia = db.Column(db.String(50), nullable=True)
    lotto = db.Column(db.String(100), nullable=True)
    data_acquisto = db.Column(db.Date, nullable=True)
    data_scadenza = db.Column(db.Date, nullable=True)
    data_scadenza_lotto = db.Column(db.Date, nullable=True)
    quantita_disponibile = db.Column(db.Integer, nullable=False, default=0)
    prelievi = db.relationship('PrelievoDPI', backref='dpi_item', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<DPI {self.nome} {self.taglia if self.taglia else ""}>'

# Nuovo modello per Prelievi DPI
class PrelievoDPI(db.Model):
    __tablename__ = 'prelievo_dpi'
    id = db.Column(db.Integer, primary_key=True)
    dpi_id = db.Column(db.Integer, db.ForeignKey('dpi.id'), nullable=False)
    dipendente_id = db.Column(db.Integer, db.ForeignKey('dipendente.id'), nullable=False)
    quantita_prelevata = db.Column(db.Integer, nullable=False)
    data_prelievo = db.Column(db.Date, nullable=False, default=date.today)
    data_scadenza_dpi_consegnato = db.Column(db.Date, nullable=True)

    def __repr__(self):
        return f'<PrelievoDPI ID: {self.id} DPI: {self.dpi_id} Dip: {self.dipendente_id} Data: {self.data_prelievo}>'

class TipoContratto(db.Model):
    __tablename__ = 'tipo_contratto'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True) # Es. Tempo Indeterminato, Tempo Determinato, Apprendistato
    descrizione = db.Column(db.Text, nullable=True)
    contratti = db.relationship('Contratto', back_populates='tipo_contratto', lazy='dynamic')

    def __repr__(self):
        return f'<TipoContratto {self.nome}>'

class Contratto(db.Model):
    __tablename__ = 'contratti'
    id = db.Column(db.Integer, primary_key=True)
    dipendente_id = db.Column(db.Integer, db.ForeignKey('dipendente.id'), nullable=False)
    tipo_contratto_id = db.Column(db.Integer, db.ForeignKey('tipo_contratto.id'), nullable=False)
    data_inizio = db.Column(db.Date, nullable=False)
    data_fine = db.Column(db.Date, nullable=True)
    note = db.Column(db.Text, nullable=True)

    dipendente = db.relationship('Dipendente', back_populates='contratti')
    tipo_contratto = db.relationship('TipoContratto', back_populates='contratti')

    def __repr__(self):
        return f'<Contratto ID: {self.id} Dip: {self.dipendente_id} Tipo: {self.tipo_contratto_id}>'