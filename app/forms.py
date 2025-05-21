from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SubmitField
from wtforms import SelectField, FloatField, DateField, MultipleFileField, HiddenField
from wtforms import IntegerField, DateTimeField, SelectMultipleField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange, ValidationError
from datetime import datetime
from app.models import User, Cliente, Fornitore, Competenza, Dipendente
from app import db
from app.data.italian_locations import COMUNI_ITALIANI, PROVINCE_ITALIANE

# ======================================================
# Form per autenticazione e gestione utenti
# ======================================================

class LoginForm(FlaskForm):
    """Form per il login degli utenti"""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Ricordami')
    submit = SubmitField('Accedi')


class RegistrationForm(FlaskForm):
    """Form per la registrazione degli utenti"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=8, message='La password deve essere di almeno 8 caratteri')
    ])
    password2 = PasswordField('Ripeti Password', validators=[
        DataRequired(), 
        EqualTo('password', message='Le password devono coincidere')
    ])
    role = SelectField('Ruolo', choices=[
        ('operatore', 'Operatore'), 
        ('admin', 'Amministratore')
    ])
    submit = SubmitField('Registra')
    
    def validate_username(self, username):
        """Verifica che lo username non esista già"""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username già utilizzato. Scegline un altro.')
    
    def validate_email(self, email):
        """Verifica che l'email non esista già"""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email già registrata. Utilizzane un\'altra o recupera la password.')


class ChangePasswordForm(FlaskForm):
    """Form per il cambio password"""
    old_password = PasswordField('Password attuale', validators=[DataRequired()])
    password = PasswordField('Nuova password', validators=[
        DataRequired(), 
        Length(min=8, message='La password deve essere di almeno 8 caratteri')
    ])
    password2 = PasswordField('Ripeti nuova password', validators=[
        DataRequired(), 
        EqualTo('password', message='Le password devono coincidere')
    ])
    submit = SubmitField('Cambia Password')


# ======================================================
# Form per Modulo 1 e 5: Inserimento dati con foto
# ======================================================

class Modulo1EntryForm(FlaskForm):
    """Form per inserimento dati Modulo 1"""
    valore_numerico = FloatField('Valore numerico', validators=[DataRequired()])
    note = TextAreaField('Note', validators=[Optional(), Length(max=1000)])
    photos = MultipleFileField('Foto (opzionali)', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Solo immagini sono permesse!')
    ])
    submit = SubmitField('Salva')


class Modulo1ViewForm(FlaskForm):
    """Form per segnare come visti i dati del Modulo 1"""
    entry_id = HiddenField('ID Entry', validators=[DataRequired()])
    mark_viewed = BooleanField('Segna come visto', default=False)
    submit = SubmitField('Aggiorna')


# Modulo 5 usa gli stessi form del Modulo 1
Modulo5EntryForm = Modulo1EntryForm
Modulo5ViewForm = Modulo1ViewForm


# ======================================================
# Form per Modulo 2: Analisi fatturato clienti
# ======================================================

class ClienteForm(FlaskForm):
    """Form per aggiungere/modificare clienti"""
    nome = StringField('Nome cliente', validators=[DataRequired(), Length(max=128)])
    codice = StringField('Codice cliente', validators=[DataRequired(), Length(max=64)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    telefono = StringField('Telefono', validators=[Optional(), Length(max=20)])
    indirizzo = StringField('Indirizzo', validators=[Optional(), Length(max=256)])
    submit = SubmitField('Salva')
    
    def validate_codice(self, codice):
        """Verifica che il codice cliente non esista già"""
        cliente = Cliente.query.filter_by(codice=codice.data).first()
        if cliente is not None and (not hasattr(self, 'id') or cliente.id != self.id.data):
            raise ValidationError('Codice cliente già esistente. Usa un altro codice.')


class FatturatoForm(FlaskForm):
    """Form per inserimento manuale di fatturati"""
    cliente_id = SelectField('Cliente', coerce=int, validators=[DataRequired()])
    data = DateField('Data', validators=[DataRequired()], format='%Y-%m-%d')
    importo = FloatField('Importo', validators=[DataRequired(), NumberRange(min=0)])
    descrizione = TextAreaField('Descrizione', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Salva')
    
    def __init__(self, *args, **kwargs):
        super(FatturatoForm, self).__init__(*args, **kwargs)
        self.cliente_id.choices = [(c.id, c.nome) for c in Cliente.query.order_by(Cliente.nome).all()]


class ExcelUploadForm(FlaskForm):
    """Form per caricamento file Excel"""
    excel_file = FileField('File Excel', validators=[
        FileRequired(),
        FileAllowed(['xlsx', 'xls'], 'Solo file Excel!')
    ])
    submit = SubmitField('Carica')


# ======================================================
# Form per Modulo 3: Analisi spese fornitori
# ======================================================

class FornitoreForm(FlaskForm):
    """Form per aggiungere/modificare fornitori"""
    nome = StringField('Nome fornitore', validators=[DataRequired(), Length(max=128)])
    codice = StringField('Codice fornitore', validators=[DataRequired(), Length(max=64)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    telefono = StringField('Telefono', validators=[Optional(), Length(max=20)])
    indirizzo = StringField('Indirizzo', validators=[Optional(), Length(max=256)])
    submit = SubmitField('Salva')
    
    def validate_codice(self, codice):
        """Verifica che il codice fornitore non esista già"""
        fornitore = Fornitore.query.filter_by(codice=codice.data).first()
        if fornitore is not None and (not hasattr(self, 'id') or fornitore.id != self.id.data):
            raise ValidationError('Codice fornitore già esistente. Usa un altro codice.')


class SpesaForm(FlaskForm):
    """Form per inserimento manuale di spese"""
    fornitore_id = SelectField('Fornitore', coerce=int, validators=[DataRequired()])
    data = DateField('Data', validators=[DataRequired()], format='%Y-%m-%d')
    importo = FloatField('Importo', validators=[DataRequired(), NumberRange(min=0)])
    descrizione = TextAreaField('Descrizione', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Salva')
    
    def __init__(self, *args, **kwargs):
        super(SpesaForm, self).__init__(*args, **kwargs)
        self.fornitore_id.choices = [(f.id, f.nome) for f in Fornitore.query.order_by(Fornitore.nome).all()]


# Modulo 3 usa lo stesso form ExcelUploadForm del Modulo 2 per caricare file Excel


# ======================================================
# Form per Modulo 4: Generazione PDF
# ======================================================

class Modulo4EntryForm(FlaskForm):
    """Form per inserimento dati e generazione PDF"""
    titolo = StringField('Titolo', validators=[DataRequired(), Length(max=128)])
    valore1 = FloatField('Valore 1', validators=[DataRequired()])
    valore2 = FloatField('Valore 2', validators=[Optional()])
    valore3 = FloatField('Valore 3', validators=[Optional()])
    note = TextAreaField('Note', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Genera PDF')


# ======================================================
# Form per Modulo 6 e 7: Inserimento dati con riepilogo
# ======================================================

class Modulo6EntryForm(FlaskForm):
    """Form per inserimento dati Modulo 6"""
    valore1 = FloatField('Valore 1', validators=[DataRequired()])
    valore2 = FloatField('Valore 2', validators=[Optional()])
    valore3 = FloatField('Valore 3', validators=[Optional()])
    note = TextAreaField('Note', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Salva')


class Modulo6ViewForm(FlaskForm):
    """Form per segnare come visti i dati del Modulo 6"""
    entry_id = HiddenField('ID Entry', validators=[DataRequired()])
    mark_viewed = BooleanField('Segna come visto', default=False)
    submit = SubmitField('Aggiorna')


# Modulo 7 usa gli stessi form del Modulo 6
Modulo7EntryForm = Modulo6EntryForm
Modulo7ViewForm = Modulo6ViewForm


# ======================================================
# Form per Modulo 8: Gestione dipendenti e competenze
# ======================================================

class DipendenteForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    cognome = StringField('Cognome', validators=[DataRequired()])
    data_nascita = DateField('Data di Nascita', validators=[DataRequired()])
    luogo_nascita = StringField('Luogo di Nascita', validators=[DataRequired()])
    provincia_nascita = StringField('Provincia di Nascita', validators=[DataRequired()])
    codice_fiscale = StringField('Codice Fiscale', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email()])
    telefono = StringField('Telefono', validators=[Optional()])
    
    matricola = StringField('Matricola', validators=[Optional()])
    reparto = StringField('Reparto', validators=[Optional()])
    ruolo = StringField('Ruolo', validators=[Optional()])
    data_assunzione_somministrazione = DateField('Data Assunzione Somministrazione', validators=[Optional()])
    agenzia_somministrazione = StringField('Agenzia Somministrazione', validators=[Optional()])
    data_assunzione_indeterminato = DateField('Data Assunzione Indeterminato', validators=[Optional()])
    legge_104 = BooleanField('Legge 104')
    donatore_avis = BooleanField('Donatore AVIS')
    
    indirizzo_residenza = StringField('Indirizzo', validators=[DataRequired()])
    citta_residenza = StringField('Città', validators=[DataRequired()])
    provincia_residenza = StringField('Provincia', validators=[DataRequired()])
    cap_residenza = StringField('CAP', validators=[DataRequired()])
    
    submit = SubmitField('Salva')


class CompetenzaForm(FlaskForm):
    """Form per aggiungere/modificare competenze"""
    nome = StringField('Nome', validators=[DataRequired(), Length(max=100)])
    descrizione = TextAreaField('Descrizione', validators=[Optional(), Length(max=500)])
    livello = SelectField('Livello', choices=[
        ('base', 'Base'),
        ('intermedio', 'Intermedio'),
        ('avanzato', 'Avanzato')
    ], validators=[DataRequired()])
    area = SelectField('Area', choices=[
        ('tecnica', 'Tecnica'),
        ('soft_skill', 'Soft Skill'),
        ('sicurezza', 'Sicurezza'),
        ('qualita', 'Qualità'),
        ('altro', 'Altro')
    ], validators=[DataRequired()])
    submit = SubmitField('Salva')
    
    def validate_nome(self, nome):
        """Verifica che il nome competenza non esista già"""
        comp = Competenza.query.filter_by(nome=nome.data).first()
        if comp is not None and (not hasattr(self, 'id') or comp.id != self.id.data):
            raise ValidationError('Competenza già esistente con questo nome.')


class AssegnaCompetenzaForm(FlaskForm):
    """Form per assegnare competenze a un dipendente"""
    dipendente_id = SelectField('Dipendente', coerce=int, validators=[DataRequired()])
    competenze = SelectMultipleField('Competenze', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Assegna')
    
    def __init__(self, *args, **kwargs):
        super(AssegnaCompetenzaForm, self).__init__(*args, **kwargs)
        self.dipendente_id.choices = [(d.id, f"{d.nome} {d.cognome}") 
                                     for d in Dipendente.query.order_by(Dipendente.cognome).all()]
        self.competenze.choices = [(c.id, c.nome) for c in Competenza.query.order_by(Competenza.nome).all()]


# ======================================================
# Form per Modulo 9: Analisi dati da Excel
# ======================================================

class Modulo9ExcelUploadForm(FlaskForm):
    """Form per caricamento file Excel nel Modulo 9"""
    excel_file = FileField('File Excel', validators=[
        FileRequired(),
        FileAllowed(['xlsx', 'xls'], 'Solo file Excel!')
    ])
    descrizione = TextAreaField('Descrizione del file', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Carica e Analizza')


# ======================================================
# Form per componenti comuni
# ======================================================

class SearchForm(FlaskForm):
    """Form per ricerca generica"""
    q = StringField('Cerca', validators=[DataRequired()])
    submit = SubmitField('Cerca')


class DateRangeForm(FlaskForm):
    """Form per filtro intervallo date"""
    start_date = DateField('Data inizio', validators=[Optional()], format='%Y-%m-%d')
    end_date = DateField('Data fine', validators=[Optional()], format='%Y-%m-%d')
    submit = SubmitField('Filtra')
    
    def validate(self):
        """Validazione personalizzata per assicurare che start_date <= end_date"""
        if not super(DateRangeForm, self).validate():
            return False
            
        if self.start_date.data and self.end_date.data and self.start_date.data > self.end_date.data:
            self.end_date.errors.append('La data di fine deve essere successiva alla data di inizio')
            return False
            
        return True


class TrainingCourseForm(FlaskForm):
    name = StringField('Nome del Corso', validators=[DataRequired()])
    description = TextAreaField('Descrizione')
    date = DateField('Data del Corso', validators=[DataRequired()])
    employees = SelectMultipleField('Dipendenti', coerce=int)
    submit = SubmitField('Salva')

class CourseCompletionForm(FlaskForm):
    status = SelectField('Stato', choices=[
        ('pending', 'Da Svolgere'),
        ('in_progress', 'In Corso'),
        ('completed', 'Completato')
    ])
    submit = SubmitField('Aggiorna Stato')

class CorsoFormazioneForm(FlaskForm):
    titolo = StringField('Titolo', validators=[DataRequired()])
    descrizione = TextAreaField('Descrizione')
    durata_ore = IntegerField('Durata (ore)', validators=[DataRequired(), NumberRange(min=1)])
    data_inizio = DateTimeField('Data Inizio', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    data_fine = DateTimeField('Data Fine', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    data_scadenza = DateTimeField('Scadenza', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    is_obbligatorio = BooleanField('Corso Obbligatorio')
    submit = SubmitField('Salva')

    def validate_data_fine(self, data_fine):
        if data_fine.data and self.data_inizio.data and data_fine.data <= self.data_inizio.data:
            raise ValidationError('La data di fine deve essere successiva alla data di inizio')

class PartecipazioneCorsoForm(FlaskForm):
    dipendenti = SelectMultipleField('Dipendenti', coerce=int, validators=[DataRequired()])
    stato = SelectField('Stato', choices=[
        ('da_iniziare', 'Da Iniziare'),
        ('in_corso', 'In Corso'),
        ('completato', 'Completato')
    ])
    valutazione = SelectField('Valutazione', choices=[
        (1, '1 - Insufficiente'),
        (2, '2 - Sufficiente'),
        (3, '3 - Buono'),
        (4, '4 - Ottimo'),
        (5, '5 - Eccellente')
    ], coerce=int)
    note = TextAreaField('Note')
    submit = SubmitField('Salva')

class DipendenteStep1Form(FlaskForm):
    """Form per il primo step di creazione dipendente - Dati Personali"""
    nome = StringField('Nome', validators=[DataRequired()])
    cognome = StringField('Cognome', validators=[DataRequired()])
    data_nascita = DateField('Data di Nascita', validators=[DataRequired()])
    luogo_nascita = StringField('Luogo di Nascita', validators=[DataRequired()])
    provincia_nascita = StringField('Provincia di Nascita', validators=[DataRequired()])
    codice_fiscale = StringField('Codice Fiscale', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email()])
    telefono = StringField('Telefono', validators=[Optional()])
    submit = SubmitField('Avanti')
    prev = SubmitField('Indietro')

class DipendenteStep2Form(FlaskForm):
    """Form per il secondo step di creazione dipendente - Dati Lavorativi"""
    matricola = StringField('Matricola', validators=[Optional()])
    reparto = StringField('Reparto', validators=[Optional()])
    ruolo = StringField('Ruolo', validators=[Optional()])
    data_assunzione_somministrazione = DateField('Data Assunzione Somministrazione', validators=[Optional()])
    agenzia_somministrazione = StringField('Agenzia Somministrazione', validators=[Optional()])
    data_assunzione_indeterminato = DateField('Data Assunzione Indeterminato', validators=[Optional()])
    legge_104 = SelectField('Legge 104', choices=[('si', 'Sì'), ('no', 'No')], validators=[DataRequired()])
    donatore_avis = SelectField('Donatore AVIS', choices=[('si', 'Sì'), ('no', 'No')], validators=[DataRequired()])
    submit = SubmitField('Avanti')
    prev = SubmitField('Indietro')

class DipendenteStep3Form(FlaskForm):
    """Form per il terzo step di creazione dipendente - Dati Residenza"""
    indirizzo_residenza = StringField('Indirizzo', validators=[DataRequired()])
    citta_residenza = StringField('Città', validators=[DataRequired()])
    provincia_residenza = StringField('Provincia', validators=[DataRequired()])
    cap_residenza = StringField('CAP', validators=[DataRequired()])
    submit = SubmitField('Avanti')
    prev = SubmitField('Indietro')

class DipendenteStep4Form(FlaskForm):
    """Form per il quarto step di creazione dipendente - Competenze"""
    competenze = SelectMultipleField('Competenze', coerce=int, validators=[Optional()])
    submit = SubmitField('Avanti')
    prev = SubmitField('Indietro')

class DipendenteStep5Form(FlaskForm):
    """Form per il quinto step di creazione dipendente - Vestiario"""
    vestiario = SelectMultipleField('Vestiario', coerce=int, validators=[Optional()])
    submit = SubmitField('Completa')
    prev = SubmitField('Indietro')