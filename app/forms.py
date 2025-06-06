from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SubmitField, FieldList
from wtforms import SelectField, FloatField, DateField, MultipleFileField, HiddenField, IntegerField
from wtforms import SelectMultipleField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange, ValidationError
from datetime import datetime, date
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
    id = HiddenField('ID')
    nome = StringField('Nome', validators=[DataRequired()])
    descrizione = TextAreaField('Descrizione')
    livello = SelectField('Livello', choices=[
        ('', 'Seleziona livello'),
        ('base', 'Base'),
        ('intermedio', 'Intermedio'),
        ('avanzato', 'Avanzato'),
        ('esperto', 'Esperto')
    ])
    area = StringField('Area')
    submit = SubmitField('Salva')
    
    def validate_nome(self, nome):
        """Verifica che il nome competenza non esista già"""
        comp = Competenza.query.filter_by(nome=nome.data).first()
        if comp is not None:
            # Se stiamo creando una nuova competenza (id è None)
            if not self.id.data:
                raise ValidationError('Competenza già esistente con questo nome.')
            # Se stiamo modificando una competenza esistente
            elif comp.id != int(self.id.data):
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
    giorno_inizio = DateField('Giorno Inizio', format='%Y-%m-%d', validators=[DataRequired()])
    giorno_fine = DateField('Giorno Fine', format='%Y-%m-%d', validators=[DataRequired()])
    scadenza_relativa = StringField('Scadenza (es. 1 anno, 6 mesi)', validators=[Optional()])
    is_obbligatorio = BooleanField('Corso Obbligatorio')
    submit = SubmitField('Salva')

    def validate_giorno_fine(self, giorno_fine):
        if giorno_fine.data < self.giorno_inizio.data:
            raise ValidationError('La data di fine non può essere precedente alla data di inizio.')

class PartecipazioneCorsoForm(FlaskForm):
    dipendenti = SelectMultipleField('Dipendenti', coerce=int, validators=[DataRequired()])
    stato = SelectField('Stato', choices=[
        ('da_iniziare', 'Da Iniziare'),
        ('in_corso', 'In Corso'),
        ('completato', 'Completato')
    ])
    valutazione = SelectField('Valutazione', 
                              choices=[
                                  ('', 'Seleziona Valutazione (Opzionale)'),
                                  (1, '1 - Insufficiente'),
                                  (2, '2 - Sufficiente'),
                                  (3, '3 - Buono'),
                                  (4, '4 - Ottimo'),
                                  (5, '5 - Eccellente')
                              ],
                              coerce=lambda x: int(x) if x else None,
                              validators=[Optional()])
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
    email = StringField('Email', validators=[Optional()])
    telefono = StringField('Telefono', validators=[Optional()])
    next_step = SubmitField('Avanti')

class DipendenteStep2Form(FlaskForm):
    """Form per il secondo step di creazione dipendente - Dati Lavorativi"""
    matricola = StringField('Matricola', validators=[Optional()])
    reparto = StringField('Reparto', validators=[Optional()])
    ruolo = StringField('Ruolo', validators=[Optional()])
    data_assunzione_somministrazione = DateField('Data Assunzione Somministrazione', validators=[Optional()])
    agenzia_somministrazione = StringField('Agenzia Somministrazione', validators=[Optional()])
    data_assunzione_indeterminato = DateField('Data Assunzione Indeterminato', validators=[Optional()])
    legge_104 = SelectField('Legge 104', choices=[('no', 'No'), ('si', 'Sì')], validators=[DataRequired()])
    donatore_avis = SelectField('Donatore AVIS', choices=[('no', 'No'), ('si', 'Sì')], validators=[DataRequired()])
    previous_step = SubmitField('Indietro')
    next_step = SubmitField('Avanti')

class DipendenteStep3Form(FlaskForm):
    """Form per il terzo step di creazione dipendente - Dati Residenza"""
    indirizzo_residenza = StringField('Indirizzo', validators=[Optional()])
    citta_residenza = StringField('Città', validators=[Optional()])
    provincia_residenza = StringField('Provincia', validators=[Optional()])
    cap_residenza = StringField('CAP', validators=[Optional()])
    previous_step = SubmitField('Indietro')
    next_step = SubmitField('Avanti')

class DipendenteStep4Form(FlaskForm):
    """Form per il quarto step di creazione dipendente - Competenze"""
    competenze = SelectMultipleField('Competenze', coerce=int, validators=[Optional()])
    percentuali = FieldList(IntegerField('Percentuale', validators=[Optional(), NumberRange(min=0, max=100)]))
    previous_step = SubmitField('Indietro')
    final_submit = SubmitField('Completa e Salva')

class VestiarioItemForm(FlaskForm):
    nome = StringField('Nome Articolo', validators=[DataRequired(), Length(min=2, max=100)])
    taglia = StringField('Taglia (Opzionale)', validators=[Optional(), Length(max=50)])
    quantita = IntegerField('Quantità Iniziale', validators=[DataRequired(), NumberRange(min=0)], default=0)
    submit = SubmitField('Salva Articolo')

class PrelievoVestiarioForm(FlaskForm):
    dipendente_id = SelectField('Dipendente', coerce=int, validators=[DataRequired()])
    quantita = IntegerField('Quantità da Prelevare', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Registra Prelievo')

    def __init__(self, *args, **kwargs):
        super(PrelievoVestiarioForm, self).__init__(*args, **kwargs)
        # Popola il campo dipendente_id con i dipendenti non archiviati
        from app.models import Dipendente
        self.dipendente_id.choices = [(d.id, f"{d.nome} {d.cognome}") for d in Dipendente.query.filter_by(archiviato=False).order_by(Dipendente.cognome, Dipendente.nome).all()]
        if not self.dipendente_id.choices:
            self.dipendente_id.choices = [(0, "Nessun dipendente disponibile")]
        elif len(self.dipendente_id.choices) > 1:
             self.dipendente_id.choices.insert(0, (0, "Seleziona un dipendente..."))

# Form per DPI
class DPIForm(FlaskForm):
    nome = StringField('Nome DPI', validators=[DataRequired(), Length(min=2, max=150)])
    descrizione = TextAreaField('Descrizione', validators=[Optional(), Length(max=500)])
    categoria = StringField('Categoria', validators=[Optional(), Length(max=100)])
    fornitore = StringField('Fornitore', validators=[Optional(), Length(max=150)])
    codice = StringField('Codice', validators=[Optional(), Length(max=50)])
    taglia = StringField('Taglia (Opzionale)', validators=[Optional(), Length(max=50)])
    lotto = StringField('Lotto (Opzionale)', validators=[Optional(), Length(max=100)])
    data_acquisto = DateField('Data Acquisto', format='%Y-%m-%d', validators=[Optional()])
    data_scadenza = DateField('Data Scadenza', format='%Y-%m-%d', validators=[Optional()])
    data_scadenza_lotto = DateField('Data Scadenza Lotto (Opzionale)', format='%Y-%m-%d', validators=[Optional()])
    quantita_disponibile = IntegerField('Quantità Disponibile', validators=[DataRequired(), NumberRange(min=0)], default=0)
    submit = SubmitField('Salva DPI')

# Form per Prelievo DPI
class PrelievoDPIForm(FlaskForm):
    # dpi_id sarà gestito dalla route/template, non un campo diretto del form base
    dipendente_id = SelectField('Dipendente', coerce=int, validators=[DataRequired()])
    quantita_prelevata = IntegerField('Quantità da Prelevare', validators=[DataRequired(), NumberRange(min=1)])
    data_prelievo = DateField('Data Prelievo', format='%Y-%m-%d', default=date.today, validators=[DataRequired()])
    # La scadenza del DPI consegnato potrebbe essere calcolata. 
    # Se deve essere inserita manualmente o ha una logica complessa, può restare.
    # Per ora la manteniamo opzionale, l'utente la imposterà se nota, altrimenti la logica applicativa può calcolarla.
    data_scadenza_dpi_consegnato = DateField('Data Scadenza DPI Consegnato (Opzionale)', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Registra Prelievo DPI')

    def __init__(self, *args, **kwargs):
        super(PrelievoDPIForm, self).__init__(*args, **kwargs)
        from app.models import Dipendente
        choices = [(d.id, f"{d.nome} {d.cognome}") for d in Dipendente.query.filter_by(archiviato=False).order_by(Dipendente.cognome, Dipendente.nome).all()]
        if not choices:
            self.dipendente_id.choices = [(0, "Nessun dipendente disponibile")] # o disabilitare il campo
        else:
            self.dipendente_id.choices = [(0, "Seleziona dipendente...")] + choices

# Form per Report Verbale DPI
class VerbaleDPIReportForm(FlaskForm):
    dipendente_id = SelectField('Dipendente', coerce=int, validators=[DataRequired()])
    # L'anno potrebbe essere un IntegerField o un SelectField con anni pertinenti
    anno = IntegerField('Anno del Verbale (YYYY)', validators=[
        DataRequired(),
        NumberRange(min=2000, max=date.today().year + 5) # Range di anni ragionevole
    ], default=date.today().year)
    submit = SubmitField('Genera Verbale PDF')

    def __init__(self, *args, **kwargs):
        super(VerbaleDPIReportForm, self).__init__(*args, **kwargs)
        from app.models import Dipendente
        choices = [(d.id, f"{d.nome} {d.cognome}") for d in Dipendente.query.filter_by(archiviato=False).order_by(Dipendente.cognome, Dipendente.nome).all()]
        if not choices:
            self.dipendente_id.choices = [(0, "Nessun dipendente disponibile")]
        else:
            self.dipendente_id.choices = [(0, "Seleziona dipendente...")] + choices
        
        # Potremmo popolare gli anni dinamicamente se necessario, ad esempio basati sui prelievi DPI esistenti
        # Per ora usiamo un IntegerField con validatori di range.