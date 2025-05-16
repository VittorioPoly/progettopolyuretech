from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from app import db
from app.models import Dipendente, Competenza, Timbratura, VestiarioItem, Inventory, PrelievoVestiario, DipendenteCompetenza, Performance
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
    # Recupera i parametri di ricerca
    search = request.args.get('search', '')
    reparto = request.args.get('reparto', '')
    ruolo = request.args.get('ruolo', '')
    
    # Query base
    query = Dipendente.query.filter_by(archiviato=False)
    
    # Applica i filtri di ricerca
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Dipendente.nome.ilike(search_term),
                Dipendente.cognome.ilike(search_term),
                Dipendente.email.ilike(search_term)
            )
        )
    
    if reparto:
        query = query.filter(Dipendente.reparto == reparto)
    
    if ruolo:
        query = query.filter(Dipendente.ruolo == ruolo)
    
    # Recupera i dipendenti filtrati
    dipendenti = query.order_by(Dipendente.nome).all()
    
    # Recupera la lista dei reparti e ruoli per i filtri
    reparti = db.session.query(Dipendente.reparto).distinct().filter(Dipendente.reparto.isnot(None)).all()
    reparti = [r[0] for r in reparti]
    
    ruoli = db.session.query(Dipendente.ruolo).distinct().filter(Dipendente.ruolo.isnot(None)).all()
    ruoli = [r[0] for r in ruoli]
    
    # Per i link alle timbrature
    now = datetime.utcnow()
    
    return render_template(
        'modulo8/dipendenti.html',
        dipendenti=dipendenti,
        now=now,
        reparti=reparti,
        ruoli=ruoli
    )

@modulo8.route('/modulo8/dipendenti/nuovo', methods=['GET','POST'])
@login_required
@admin_required
def nuovo_dipendente():
    step = int(request.args.get('step', 1))
    
    if step == 1:
        form = DipendenteStep1Form()
    elif step == 2:
        form = DipendenteStep2Form()
    elif step == 3:
        form = DipendenteStep3Form()
    elif step == 4:
        form = DipendenteStep4Form()
        # Precompila le competenze
        form.competenze.choices = [(c.id, c.nome) for c in Competenza.query.order_by(Competenza.nome).all()]
    elif step == 5:
        form = DipendenteStep5Form()
        # Precompila il vestiario
        form.vestiario.choices = [(v.id, v.nome) for v in VestiarioItem.query.order_by(VestiarioItem.nome).all()]
    else:
        return redirect(url_for('modulo8.dipendenti'))
    
    if form.validate_on_submit():
        action = request.form.get('action')
        
        if action == 'prev':
            return redirect(url_for('modulo8.nuovo_dipendente', step=step-1))
        elif action == 'next':
            # Salva i dati nella sessione
            if 'dipendente_data' not in session:
                session['dipendente_data'] = {}
            
            if step == 1:
                session['dipendente_data'].update({
                    'nome': form.nome.data,
                    'cognome': form.cognome.data,
                    'data_nascita': form.data_nascita.data.isoformat(),
                    'luogo_nascita': form.luogo_nascita.data,
                    'provincia_nascita': form.provincia_nascita.data,
                    'codice_fiscale': form.codice_fiscale.data,
                    'email': form.email.data,
                    'telefono': form.telefono.data
                })
            elif step == 2:
                session['dipendente_data'].update({
                    'matricola': form.matricola.data,
                    'reparto': form.reparto.data,
                    'ruolo': form.ruolo.data,
                    'data_assunzione_somministrazione': form.data_assunzione_somministrazione.data.isoformat() if form.data_assunzione_somministrazione.data else None,
                    'agenzia_somministrazione': form.agenzia_somministrazione.data,
                    'data_assunzione_indeterminato': form.data_assunzione_indeterminato.data.isoformat() if form.data_assunzione_indeterminato.data else None,
                    'legge_104': form.legge_104.data == 'si',
                    'donatore_avis': form.donatore_avis.data == 'si'
                })
            elif step == 3:
                session['dipendente_data'].update({
                    'indirizzo_residenza': form.indirizzo_residenza.data,
                    'citta_residenza': form.citta_residenza.data,
                    'provincia_residenza': form.provincia_residenza.data,
                    'cap_residenza': form.cap_residenza.data
                })
            elif step == 4:
                # Assicuriamoci che le competenze siano una lista
                competenze = form.competenze.data
                if not isinstance(competenze, list):
                    competenze = [competenze] if competenze else []
                session['dipendente_data']['competenze'] = competenze
            elif step == 5:
                # Assicuriamoci che il vestiario sia una lista
                vestiario = form.vestiario.data
                if not isinstance(vestiario, list):
                    vestiario = [vestiario] if vestiario else []
                session['dipendente_data']['vestiario'] = vestiario
                
                # Crea il dipendente con tutti i dati raccolti
                dip = Dipendente(
                    nome=session['dipendente_data']['nome'],
                    cognome=session['dipendente_data']['cognome'],
                    data_nascita=datetime.fromisoformat(session['dipendente_data']['data_nascita']),
                    luogo_nascita=session['dipendente_data']['luogo_nascita'],
                    provincia_nascita=session['dipendente_data']['provincia_nascita'],
                    codice_fiscale=session['dipendente_data']['codice_fiscale'],
                    email=session['dipendente_data']['email'],
                    telefono=session['dipendente_data']['telefono'],
                    matricola=session['dipendente_data']['matricola'],
                    reparto=session['dipendente_data']['reparto'],
                    ruolo=session['dipendente_data']['ruolo'],
                    data_assunzione_somministrazione=datetime.fromisoformat(session['dipendente_data']['data_assunzione_somministrazione']) if session['dipendente_data'].get('data_assunzione_somministrazione') else None,
                    agenzia_somministrazione=session['dipendente_data']['agenzia_somministrazione'],
                    data_assunzione_indeterminato=datetime.fromisoformat(session['dipendente_data']['data_assunzione_indeterminato']) if session['dipendente_data'].get('data_assunzione_indeterminato') else None,
                    legge_104=session['dipendente_data']['legge_104'],
                    donatore_avis=session['dipendente_data']['donatore_avis'],
                    indirizzo_residenza=session['dipendente_data']['indirizzo_residenza'],
                    citta_residenza=session['dipendente_data']['citta_residenza'],
                    provincia_residenza=session['dipendente_data']['provincia_residenza'],
                    cap_residenza=session['dipendente_data']['cap_residenza'],
                    created_by_id=current_user.id
                )
                
                # Aggiungi le competenze
                competenze = session['dipendente_data'].get('competenze', [])
                if not isinstance(competenze, list):
                    competenze = [competenze] if competenze else []
                for competenza_id in competenze:
                    competenza = Competenza.query.get(competenza_id)
                    if competenza:
                        dip.competenze.append(competenza)
                
                # Aggiungi il vestiario
                vestiario = session['dipendente_data'].get('vestiario', [])
                if not isinstance(vestiario, list):
                    vestiario = [vestiario] if vestiario else []
                for vestiario_id in vestiario:
                    vestiario_item = VestiarioItem.query.get(vestiario_id)
                    if vestiario_item:
                        dip.vestiario.append(vestiario_item)
                
                db.session.add(dip)
                db.session.commit()
                
                # Pulisci la sessione
                session.pop('dipendente_data', None)
                
                flash('Dipendente creato con successo!', 'success')
                return redirect(url_for('modulo8.dipendenti'))
            
            return redirect(url_for('modulo8.nuovo_dipendente', step=step+1))
    
    # Precompila il form con i dati della sessione se presenti
    if request.method == 'GET' and 'dipendente_data' in session:
        if step == 1:
            form.nome.data = session['dipendente_data'].get('nome')
            form.cognome.data = session['dipendente_data'].get('cognome')
            form.data_nascita.data = datetime.fromisoformat(session['dipendente_data']['data_nascita']) if session['dipendente_data'].get('data_nascita') else None
            form.luogo_nascita.data = session['dipendente_data'].get('luogo_nascita')
            form.provincia_nascita.data = session['dipendente_data'].get('provincia_nascita')
            form.codice_fiscale.data = session['dipendente_data'].get('codice_fiscale')
            form.email.data = session['dipendente_data'].get('email')
            form.telefono.data = session['dipendente_data'].get('telefono')
        elif step == 2:
            form.matricola.data = session['dipendente_data'].get('matricola')
            form.reparto.data = session['dipendente_data'].get('reparto')
            form.ruolo.data = session['dipendente_data'].get('ruolo')
            form.data_assunzione_somministrazione.data = datetime.fromisoformat(session['dipendente_data']['data_assunzione_somministrazione']) if session['dipendente_data'].get('data_assunzione_somministrazione') else None
            form.agenzia_somministrazione.data = session['dipendente_data'].get('agenzia_somministrazione')
            form.data_assunzione_indeterminato.data = datetime.fromisoformat(session['dipendente_data']['data_assunzione_indeterminato']) if session['dipendente_data'].get('data_assunzione_indeterminato') else None
            form.legge_104.data = 'si' if session['dipendente_data'].get('legge_104') else 'no'
            form.donatore_avis.data = 'si' if session['dipendente_data'].get('donatore_avis') else 'no'
        elif step == 3:
            form.indirizzo_residenza.data = session['dipendente_data'].get('indirizzo_residenza')
            form.citta_residenza.data = session['dipendente_data'].get('citta_residenza')
            form.provincia_residenza.data = session['dipendente_data'].get('provincia_residenza')
            form.cap_residenza.data = session['dipendente_data'].get('cap_residenza')
        elif step == 4:
            form.competenze.data = session['dipendente_data'].get('competenze', [])
        elif step == 5:
            form.vestiario.data = session['dipendente_data'].get('vestiario', [])
    
    return render_template('modulo8/dipendenti/modifica_step.html', 
                         form=form, 
                         step=step, 
                         is_new=True)

@modulo8.route('/dipendenti/<int:id>')
@login_required
@admin_required
def profilo_dipendente(id):
    dip = Dipendente.query.get_or_404(id)
    return render_template('modulo8/profilo_dipendente.html',dip=dip,now=datetime.utcnow())

# subpages: performance, timbrature, vestiario per singolo dipendente
@modulo8.route('/dipendenti/<int:id>/performance')
@login_required
@admin_required
def performance(id):
    dipendente = Dipendente.query.get_or_404(id)
    performance_list = Performance.query.filter_by(dipendente_id=id).order_by(Performance.data.desc()).all()
    
    # Calcola le statistiche
    media_performance = 0
    if performance_list:
        media_performance = sum(p.valutazione for p in performance_list) / len(performance_list)
    
    # Prepara i dati per il grafico
    performance_data = {
        'labels': [p.data.strftime('%d/%m/%Y') for p in performance_list],
        'values': [p.valutazione for p in performance_list]
    }
    
    # Recupera le competenze non ancora valutate
    competenze_valutate = {p.competenza_id for p in performance_list}
    competenze_disponibili = Competenza.query.filter(~Competenza.id.in_(competenze_valutate)).all()
    
    return render_template('modulo8/dipendenti/performance.html',
                         dip=dipendente,
                         performance=performance_list,
                         competenze=competenze_disponibili,
                         media_performance=round(media_performance, 1),
                         competenze_valutate=len(competenze_valutate),
                         ultima_valutazione=performance_list[0].data if performance_list else None,
                         performance_data=performance_data,
                         now=datetime.now())

@modulo8.route('/dipendenti/<int:id>/performance/aggiungi', methods=['POST'])
@login_required
@admin_required
def aggiungi_performance(id):
    dipendente = Dipendente.query.get_or_404(id)
    competenza_id = request.form.get('competenza_id')
    valutazione = request.form.get('valutazione')
    note = request.form.get('note')
    
    if not competenza_id or not valutazione:
        flash('Tutti i campi sono obbligatori', 'danger')
        return redirect(url_for('modulo8.performance', id=id))
    
    try:
        valutazione = int(valutazione)
        if not 0 <= valutazione <= 100:
            raise ValueError
    except ValueError:
        flash('La valutazione deve essere un numero tra 0 e 100', 'danger')
        return redirect(url_for('modulo8.performance', id=id))
    
    performance = Performance(
        dipendente_id=id,
        competenza_id=competenza_id,
        valutazione=valutazione,
        note=note
    )
    
    db.session.add(performance)
    db.session.commit()
    
    flash('Valutazione aggiunta con successo', 'success')
    return redirect(url_for('modulo8.performance', id=id))

@modulo8.route('/dipendenti/performance/<int:id>/modifica', methods=['POST'])
@login_required
@admin_required
def modifica_performance(id):
    performance = Performance.query.get_or_404(id)
    valutazione = request.form.get('valutazione')
    note = request.form.get('note')
    
    if not valutazione:
        flash('La valutazione è obbligatoria', 'danger')
        return redirect(url_for('modulo8.performance', id=performance.dipendente_id))
    
    try:
        valutazione = int(valutazione)
        if not 0 <= valutazione <= 100:
            raise ValueError
    except ValueError:
        flash('La valutazione deve essere un numero tra 0 e 100', 'danger')
        return redirect(url_for('modulo8.performance', id=performance.dipendente_id))
    
    performance.valutazione = valutazione
    performance.note = note
    performance.data = datetime.utcnow()
    
    db.session.commit()
    
    flash('Valutazione modificata con successo', 'success')
    return redirect(url_for('modulo8.performance', id=performance.dipendente_id))

@modulo8.route('/dipendenti/performance/<int:id>/elimina', methods=['POST'])
@login_required
@admin_required
def elimina_performance(id):
    performance = Performance.query.get_or_404(id)
    dipendente_id = performance.dipendente_id
    
    db.session.delete(performance)
    db.session.commit()
    
    flash('Valutazione eliminata con successo', 'success')
    return redirect(url_for('modulo8.performance', id=dipendente_id))

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
        # Precompila le percentuali
        competenze_percentuali = {dc.competenza_id: dc.percentuale for dc in dipendente.competenze_associate}
        form.competenze.data = list(competenze_percentuali.keys())
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
                # Rimuovi tutte le competenze esistenti
                DipendenteCompetenza.query.filter_by(dipendente_id=dipendente.id).delete()
                
                # Aggiungi le nuove competenze con le relative percentuali
                for competenza_id in form.competenze.data:
                    percentuale = int(request.form.get(f'percentuale_{competenza_id}', 0))
                    dc = DipendenteCompetenza(
                        dipendente_id=dipendente.id,
                        competenza_id=competenza_id,
                        percentuale=percentuale
                    )
                    db.session.add(dc)
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
                # Rimuovi tutte le competenze esistenti
                DipendenteCompetenza.query.filter_by(dipendente_id=dipendente.id).delete()
                
                # Aggiungi le nuove competenze con le relative percentuali
                for competenza_id in form.competenze.data:
                    percentuale = int(request.form.get(f'percentuale_{competenza_id}', 0))
                    dc = DipendenteCompetenza(
                        dipendente_id=dipendente.id,
                        competenza_id=competenza_id,
                        percentuale=percentuale
                    )
                    db.session.add(dc)
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

@modulo8.route('/competenze/elimina/<int:id>', methods=['POST'])
@login_required
@admin_required
def elimina_competenza(id):
    competenza = Competenza.query.get_or_404(id)
    
    # Elimina prima le associazioni con i dipendenti
    DipendenteCompetenza.query.filter_by(competenza_id=id).delete()
    
    # Poi elimina la competenza
    db.session.delete(competenza)
    db.session.commit()
    
    flash('Competenza eliminata con successo', 'success')
    return redirect(url_for('modulo8.competenze'))
