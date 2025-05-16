from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Dipendente, Competenza, Timbratura, VestiarioItem, Inventory, PrelievoVestiario
from app.utils import admin_required
from datetime import datetime
from calendar import monthrange
from app.forms import (
    DipendenteStep1Form, DipendenteStep2Form, DipendenteStep3Form,
    DipendenteStep4Form, DipendenteStep5Form, CompetenzaForm
)
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired, NumberRange

modulo8 = Blueprint('modulo8', __name__, url_prefix='/modulo8')

class VestiarioForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    taglia = StringField('Taglia', validators=[DataRequired()])
    quantita = IntegerField('Quantità', validators=[DataRequired(), NumberRange(min=0)])

@modulo8.route('/')
@login_required
@admin_required
def dashboard():
    # Dashboard con quattro moduli
    return render_template('modulo8/dashboard.html', title="Modulo 8")

@modulo8.route('/modulo8/dipendenti')
@login_required
@admin_required
def dipendenti():
    # recupera tutti i dipendenti, ordina per nome
    dips = Dipendente.query.order_by(Dipendente.nome).all()
    # per i link alle timbrature
    now = datetime.utcnow()
    return render_template(
        'modulo8/dipendenti.html',
        dipendenti=dips,
        now=now
    )

@modulo8.route('/modulo8/dipendenti/nuovo', methods=['GET','POST'])
@login_required
@admin_required
def nuovo_dipendente():
    form = DipendenteStep1Form()
    if form.validate_on_submit():
        # Determina il luogo di nascita
        luogo_nascita = form.luogo_nascita_altro.data if form.luogo_nascita.data == 'altro' else form.luogo_nascita.data
        
        # Determina la provincia di nascita
        provincia_nascita = form.provincia_nascita_altro.data if form.provincia_nascita.data == 'altro' else form.provincia_nascita.data
        
        # crea e salva il dipendente
        dip = Dipendente(
            nome=form.nome.data,
            cognome=form.cognome.data,
            data_nascita=form.data_nascita.data,
            luogo_nascita=luogo_nascita,
            provincia_nascita=provincia_nascita,
            codice_fiscale=form.codice_fiscale.data,
            email=form.email.data,
            telefono=form.telefono.data,
            created_by_id=current_user.id
        )
        db.session.add(dip)
        db.session.commit()
        flash('Dipendente creato con successo', 'success')
        return redirect(url_for('modulo8.dipendenti'))
    # PASSA il form al template
    return render_template(
        'modulo8/dipendenti/form.html',
        form=form
    )

@modulo8.route('/dipendenti/<int:id>')
@login_required
@admin_required
def profilo_dipendente(id):
    dip = Dipendente.query.get_or_404(id)
    return render_template('modulo8/profilo_dipendente.html',dip=dip,now=datetime.utcnow())

# subpages: performance, timbrature, vestiario per singolo dipendente
@modulo8.route(
    '/modulo8/dipendenti/<int:id>/performance',
    endpoint='performance_dipendente',
    methods=['GET','POST']
)
@login_required
@admin_required
def performance_dipendente(id):
    dip = Dipendente.query.get_or_404(id)
    # … qui calcoli performance_list e comp_list …
    return render_template('modulo8/dipendenti/performance.html', dip=dip, now=datetime.utcnow(), performance=performance_list, competenze=comp_list)

@modulo8.route('/dipendenti/<int:id>/timbrature')
@login_required
@admin_required
def dip_timbrature(id):
    dip = Dipendente.query.get_or_404(id)
    # recupera timbrature mensili
    return render_template('modulo8/dipendenti/timbrature.html', dip=dip)

@modulo8.route('/dipendenti/<int:id>/vestiario')
@login_required
@admin_required
def dip_vestiario(id):
    dip = Dipendente.query.get_or_404(id)
    return render_template('modulo8/dipendenti/vestiario.html', dip=dip)

# gestione competenze
@modulo8.route('/competenze')
@login_required
@admin_required
def gestione_competenze():
    competenze = Competenza.query.order_by(Competenza.nome).all()
    return render_template('modulo8/competenze/list.html', competenze=competenze)

@modulo8.route('/modulo8/competenze')
@login_required
@admin_required
def competenze():
    # recupera tutte le competenze ordinate per nome
    comps = Competenza.query.order_by(Competenza.nome).all()
    return render_template(
        'modulo8/competenze/form.html',
        competenze=comps
    )

@modulo8.route('/competenze/nuova', methods=['GET', 'POST'])
@login_required
@admin_required
def nuova_competenza():
    form = CompetenzaForm()
    if form.validate_on_submit():
        comp = Competenza(
            nome=form.nome.data,
            descrizione=form.descrizione.data,
            livello=form.livello.data,
            area=form.area.data,
            created_by_id=current_user.id
        )
        db.session.add(comp)
        db.session.commit()
        flash('Competenza creata con successo', 'success')
        return redirect(url_for('modulo8.competenze'))
    
    return render_template('modulo8/competenza_form.html', 
                         title='Nuova Competenza',
                         form=form)

@modulo8.route('/competenze/modifica/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def modifica_competenza(id):
    competenza = Competenza.query.get_or_404(id)
    form = CompetenzaForm()
    
    if form.validate_on_submit():
        competenza.nome = form.nome.data
        competenza.descrizione = form.descrizione.data
        competenza.livello = form.livello.data
        competenza.area = form.area.data
        
        db.session.commit()
        flash('Competenza aggiornata con successo', 'success')
        return redirect(url_for('modulo8.competenze'))
    
    # Pre-popola il form
    if request.method == 'GET':
        form.nome.data = competenza.nome
        form.descrizione.data = competenza.descrizione
        form.livello.data = competenza.livello
        form.area.data = competenza.area
    
    return render_template('modulo8/competenza_form.html', 
                         title='Modifica Competenza',
                         form=form)

@modulo8.route('/competenze/visualizza/<int:id>')
@login_required
@admin_required
def visualizza_competenza(id):
    competenza = Competenza.query.get_or_404(id)
    dipendenti = competenza.dipendenti.all()
    return render_template('modulo8/competenze/view.html',
                         title=f'Dettagli Competenza: {competenza.nome}',
                         competenza=competenza,
                         dipendenti=dipendenti)

# timbrature: endpoint per QR
@modulo8.route('/timbrature/qrcode', methods=['POST'])
def timbratura_qr():
    data = request.get_json()
    dip_id = data.get('dipendente_id')
    tipo = data.get('tipo')  # entrata1, uscita1...
    tim = Timbratura(dipendente_id=dip_id, tipo=tipo)
    db.session.add(tim); db.session.commit()
    return jsonify(status='ok', timestamp=tim.timestamp.isoformat())

@modulo8.route('/timbrature/<int:dip_id>/mese/<int:year>/<int:month>')
@login_required
@admin_required
def view_timbrature(dip_id, year, month):
    dip = Dipendente.query.get_or_404(dip_id)
    # genera matrice giorni x 4 tipi
    return render_template('modulo8/timbrature/sheet.html', dip=dip, year=year, month=month)

@modulo8.route(
    '/modulo8/timbrature/<int:dip_id>/mese/<int:anno>/<int:mese>',
    endpoint='timbrature_mese'
)
@login_required
@admin_required
def timbrature_mese(dip_id, anno, mese):
    # 1. Recupera il dipendente
    dip = Dipendente.query.get_or_404(dip_id)

    # 2. Costruisci la lista dei giorni del mese
    _, num_giorni = monthrange(anno, mese)
    giorni = list(range(1, num_giorni + 1))

    # 3. Preleva tutte le timbrature di quel mese
    inizio = datetime(anno, mese, 1)
    fine  = datetime(anno, mese, num_giorni, 23, 59, 59)
    timb = (Timbratura.query
            .filter(Timbratura.dipendente_id == dip_id)
            .filter(Timbratura.timestamp.between(inizio, fine))
            .all())

    # 4. Mappa: giorno -> { tipo: timestamp_formattato }
    timbrature_map = {}
    for t in timb:
        g = t.timestamp.day
        if g not in timbrature_map:
            timbrature_map[g] = {}
        timbrature_map[g][t.tipo] = t.timestamp.strftime('%H:%M')

    return render_template(
        'modulo8/timbrature_mese.html',
        dip=dip,
        anno=anno,
        mese=mese,
        giorni=giorni,
        timbrature_map=timbrature_map,
        now=datetime.utcnow()
    )

# gestione vestiario
@modulo8.route('/vestiario')
@login_required
@admin_required
def gestione_vestiario():
    items = Inventory.query.all()
    return render_template('modulo8/vestiario/inventory.html', items=items)

@modulo8.route('/vestiario/nuovo', methods=['GET', 'POST'])
@login_required
@admin_required
def aggiungi_item_vestiario():
    form = VestiarioForm()
    if form.validate_on_submit():
        item = Inventory(
            nome=form.nome.data,
            taglia=form.taglia.data,
            quantita=form.quantita.data
        )
        db.session.add(item)
        db.session.commit()
        flash('Item aggiunto con successo', 'success')
        return redirect(url_for('modulo8.gestione_vestiario'))
        
    return render_template('modulo8/vestiario/nuovo.html', form=form)

@modulo8.route('/vestiario/prelievo', methods=['POST'])
@login_required
@admin_required
def prelievo():
    dip_id = request.form['dipendente_id']
    item_id = request.form['item_id']
    qty = int(request.form['quantity'])
    prel = PrelievoVestiario(
        dipendente_id=dip_id, item_id=item_id, quantity=qty
    )
    inv = Inventory.query.get(item_id)
    inv.quantity -= qty
    db.session.add(prel); db.session.commit()
    flash('Prelievo registrato', 'success')
    return redirect(url_for('modulo8.dip_vestiario', id=dip_id))

from app.models import Inventory, Dipendente
from flask_login import login_required
from app.utils import admin_required

@modulo8.route('/modulo8/vestiario', endpoint='vestiario_dipendente')
@login_required
@admin_required
def vestiario():
    # carica inventario e lista dipendenti per il select del form
    inventory = Inventory.query.order_by(Inventory.nome).all()
    dipendenti = Dipendente.query.order_by(Dipendente.nome).all()
    return render_template(
        'modulo8/vestiario.html',
        inventory=inventory,
        dipendenti=dipendenti
    )


@modulo8.route(
    '/modulo8/vestiario/prelievo',
    methods=['POST'],
    endpoint='prelievo_vestiario'
)
@login_required
@admin_required
def prelievo_vestiario():
    # 1. Leggi i dati dal form
    dip_id  = request.form.get('dipendente_id', type=int)
    item_id = request.form.get('item_id', type=int)
    qta     = request.form.get('quantita',   type=int)

    # 2. Controlli base
    dip = Dipendente.query.get_or_404(dip_id)
    item = Inventory.query.get_or_404(item_id)
    if qta < 1 or qta > item.quantita:
        flash('Quantità non valida o esaurita.', 'danger')
        return redirect(url_for('modulo8.vestiario'))

    # 3. Registra il prelievo e aggiorna stock
    item.quantita -= qta
    pre = PrelievoVestiario(
        dipendente_id=dip_id,
        item_id=item_id,
        quantita=qta
    )
    db.session.add(pre)
    db.session.commit()

    flash(f'Prelievo di {qta}× {item.nome} registrato per {dip.nome}.', 'success')
    return redirect(url_for('modulo8.vestiario'))

@modulo8.route('/dipendenti/modifica/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def modifica_dipendente(id):
    dipendente = Dipendente.query.get_or_404(id)
    step = int(request.args.get('step', 1))
    
    if step == 1:
        form = DipendenteStep1Form(obj=dipendente)
    elif step == 2:
        form = DipendenteStep2Form(obj=dipendente)
    elif step == 3:
        form = DipendenteStep3Form(obj=dipendente)
    elif step == 4:
        form = DipendenteStep4Form(obj=dipendente)
        # Precompila le competenze
        form.competenze.choices = [(c.id, c.nome) for c in Competenza.query.order_by(Competenza.nome).all()]
        form.competenze.data = [c.id for c in dipendente.competenze]
    elif step == 5:
        form = DipendenteStep5Form(obj=dipendente)
        # Precompila il vestiario
        form.vestiario.choices = [(v.id, v.nome) for v in VestiarioItem.query.order_by(VestiarioItem.nome).all()]
        form.vestiario.data = [v.id for v in dipendente.vestiario]
    else:
        return redirect(url_for('modulo8.dipendenti'))
    
    if form.validate_on_submit():
        action = request.form.get('action')
        
        if action == 'prev':
            return redirect(url_for('modulo8.modifica_dipendente', id=id, step=step-1))
        elif action == 'next':
            # Aggiorna i dati del dipendente
            if step == 1:
                dipendente.nome = form.nome.data
                dipendente.cognome = form.cognome.data
                dipendente.data_nascita = form.data_nascita.data
                dipendente.luogo_nascita = form.luogo_nascita.data
                dipendente.provincia_nascita = form.provincia_nascita.data
                dipendente.codice_fiscale = form.codice_fiscale.data
                dipendente.email = form.email.data
                dipendente.telefono = form.telefono.data
            elif step == 2:
                dipendente.matricola = form.matricola.data
                dipendente.reparto = form.reparto.data
                dipendente.ruolo = form.ruolo.data
                dipendente.data_assunzione_somministrazione = form.data_assunzione_somministrazione.data
                dipendente.agenzia_somministrazione = form.agenzia_somministrazione.data
                dipendente.data_assunzione_indeterminato = form.data_assunzione_indeterminato.data
                dipendente.legge_104 = form.legge_104.data == 'si'
                dipendente.donatore_avis = form.donatore_avis.data == 'si'
            elif step == 3:
                dipendente.indirizzo_residenza = form.indirizzo_residenza.data
                dipendente.citta_residenza = form.citta_residenza.data
                dipendente.provincia_residenza = form.provincia_residenza.data
                dipendente.cap_residenza = form.cap_residenza.data
            elif step == 4:
                # Aggiorna le competenze
                dipendente.competenze = []
                for competenza_id in form.competenze.data:
                    competenza = Competenza.query.get(competenza_id)
                    if competenza:
                        dipendente.competenze.append(competenza)
            elif step == 5:
                # Aggiorna il vestiario
                dipendente.vestiario = []
                for vestiario_id in form.vestiario.data:
                    vestiario = VestiarioItem.query.get(vestiario_id)
                    if vestiario:
                        dipendente.vestiario.append(vestiario)
            
            db.session.commit()
            return redirect(url_for('modulo8.modifica_dipendente', id=id, step=step+1))
        elif action == 'submit':
            # Aggiorna i dati del dipendente
            if step == 1:
                dipendente.nome = form.nome.data
                dipendente.cognome = form.cognome.data
                dipendente.data_nascita = form.data_nascita.data
                dipendente.luogo_nascita = form.luogo_nascita.data
                dipendente.provincia_nascita = form.provincia_nascita.data
                dipendente.codice_fiscale = form.codice_fiscale.data
                dipendente.email = form.email.data
                dipendente.telefono = form.telefono.data
            elif step == 2:
                dipendente.matricola = form.matricola.data
                dipendente.reparto = form.reparto.data
                dipendente.ruolo = form.ruolo.data
                dipendente.data_assunzione_somministrazione = form.data_assunzione_somministrazione.data
                dipendente.agenzia_somministrazione = form.agenzia_somministrazione.data
                dipendente.data_assunzione_indeterminato = form.data_assunzione_indeterminato.data
                dipendente.legge_104 = form.legge_104.data == 'si'
                dipendente.donatore_avis = form.donatore_avis.data == 'si'
            elif step == 3:
                dipendente.indirizzo_residenza = form.indirizzo_residenza.data
                dipendente.citta_residenza = form.citta_residenza.data
                dipendente.provincia_residenza = form.provincia_residenza.data
                dipendente.cap_residenza = form.cap_residenza.data
            elif step == 4:
                # Aggiorna le competenze
                dipendente.competenze = []
                for competenza_id in form.competenze.data:
                    competenza = Competenza.query.get(competenza_id)
                    if competenza:
                        dipendente.competenze.append(competenza)
            elif step == 5:
                # Aggiorna il vestiario
                dipendente.vestiario = []
                for vestiario_id in form.vestiario.data:
                    vestiario = VestiarioItem.query.get(vestiario_id)
                    if vestiario:
                        dipendente.vestiario.append(vestiario)
            
            db.session.commit()
            flash('Dipendente modificato con successo!', 'success')
            return redirect(url_for('modulo8.dipendenti'))
    
    return render_template('modulo8/dipendenti/modifica_step.html', form=form, dipendente=dipendente, step=step)

@modulo8.route('/dipendenti/elimina/<int:id>', methods=['POST'])
@login_required
@admin_required
def elimina_dipendente(id):
    dip = Dipendente.query.get_or_404(id)
    db.session.delete(dip)
    db.session.commit()
    flash('Dipendente eliminato con successo', 'success')
    return redirect(url_for('modulo8.dipendenti'))

@modulo8.route('/dipendenti/archivia/<int:id>', methods=['POST'])
@login_required
@admin_required
def archivia_dipendente(id):
    dip = Dipendente.query.get_or_404(id)
    data_cessazione = datetime.strptime(request.form['data_cessazione'], '%Y-%m-%d')
    dip.data_cessazione = datetime.combine(data_cessazione, datetime.min.time())
    dip.archiviato = True
    db.session.commit()
    flash('Dipendente archiviato con successo', 'success')
    return redirect(url_for('modulo8.dipendenti'))

@modulo8.route('/dipendenti/storico')
@login_required
@admin_required
def storico_dipendenti():
    dipendenti = Dipendente.query.filter_by(archiviato=True).order_by(Dipendente.data_cessazione.desc()).all()
    return render_template('modulo8/dipendenti/storico.html', dipendenti=dipendenti)

@modulo8.route('/dipendenti/storico/<int:id>')
@login_required
@admin_required
def visualizza_archivio_dipendente(id):
    dip = Dipendente.query.get_or_404(id)
    if not dip.archiviato:
        flash('Dipendente non archiviato', 'danger')
        return redirect(url_for('modulo8.dipendenti'))
    return render_template('modulo8/dipendenti/view_archivio.html', dip=dip)

@modulo8.route('/vestiario/modifica/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def modifica_item_vestiario(id):
    item = Inventory.query.get_or_404(id)
    form = VestiarioForm(obj=item)
    
    if form.validate_on_submit():
        item.nome = form.nome.data
        item.taglia = form.taglia.data
        item.quantita = form.quantita.data
        db.session.commit()
        flash('Item modificato con successo', 'success')
        return redirect(url_for('modulo8.gestione_vestiario'))
        
    return render_template('modulo8/vestiario/modifica.html', form=form, item=item)
