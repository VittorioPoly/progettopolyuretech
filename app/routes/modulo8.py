from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from app import db
from app.models import Dipendente, Competenza, Timbratura, VestiarioItem, Inventory, PrelievoVestiario, DipendenteCompetenza, Performance, CorsoFormazione, PartecipazioneCorso, CorsoSicurezza
from app.utils import admin_required
from datetime import datetime
from calendar import monthrange
from app.forms import (
    DipendenteStep1Form, DipendenteStep2Form, DipendenteStep3Form,
    DipendenteStep4Form, DipendenteStep5Form, CompetenzaForm, CorsoFormazioneForm, PartecipazioneCorsoForm
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
        competenze_lista = Competenza.query.order_by(Competenza.nome).all()
    elif step == 5:
        form = DipendenteStep5Form()
        # Precompila il vestiario con nome e taglia
        form.vestiario.choices = [(v.id, f"{v.nome} ({v.taglia})" if v.taglia else v.nome) for v in VestiarioItem.query.order_by(VestiarioItem.nome).all()]
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
                # Nuova gestione: salva competenze e percentuali
                competenze = request.form.getlist('competenze')
                percentuali = {}
                for comp_id in competenze:
                    percentuali[comp_id] = request.form.get(f'percentuale_{comp_id}', '0')
                session['dipendente_data']['competenze'] = competenze
                session['dipendente_data']['competenze_percentuali'] = percentuali
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
    
    competenze_lista = Competenza.query.order_by(Competenza.nome).all()
    return render_template(
        'modulo8/dipendenti/modifica_step.html',
        form=form,
        step=step,
        is_new=True,
        competenze_lista=competenze_lista,
        dip=None
    )

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

@modulo8.route('/dipendenti/<int:id>/modifica_step', methods=['GET','POST'])
@login_required
@admin_required
def modifica_dipendente_step(id):
    dip = Dipendente.query.get_or_404(id)
    step = int(request.args.get('step', 1))

    # Determina il form corretto in base allo step
    if step == 1:
        form = DipendenteStep1Form(obj=dip)
    elif step == 2:
        form = DipendenteStep2Form(obj=dip)
    elif step == 3:
        form = DipendenteStep3Form(obj=dip)
    elif step == 4:
        form = DipendenteStep4Form() # Le competenze richiedono una logica speciale per il pre-compilamento
        # Precompila le scelte per il campo competenze (non i dati selezionati)
        form.competenze.choices = [(c.id, c.nome) for c in Competenza.query.order_by(Competenza.nome).all()]
        # Precompila le competenze e percentuali esistenti per questo dipendente
        if request.method == 'GET':
            selected_competenze_ids = [c.id for c in dip.competenze]
            form.competenze.data = selected_competenze_ids
            # Le percentuali dovranno essere gestite separatamente nel template per il pre-filling
            # Potremmo passare un dizionario di percentuali al template
    elif step == 5:
        form = DipendenteStep5Form() # Il vestiario richiede una logica speciale per il pre-compilamento
        form.vestiario.choices = [(v.id, f"{v.nome} ({v.taglia})" if v.taglia else v.nome) for v in VestiarioItem.query.order_by(VestiarioItem.nome).all()]
        if request.method == 'GET':
            selected_vestiario_ids = [vi.id for vi in dip.vestiario] # Assumendo che dip.vestiario sia una lista di VestiarioItem
            form.vestiario.data = selected_vestiario_ids
    else:
        flash('Step non valido.', 'warning')
        return redirect(url_for('modulo8.profilo_dipendente', id=dip.id))

    if form.validate_on_submit():
        action = request.form.get('action')
        
        if action == 'prev':
            if step > 1:
                return redirect(url_for('modulo8.modifica_dipendente_step', id=dip.id, step=step-1))
            else:
                return redirect(url_for('modulo8.profilo_dipendente', id=dip.id)) # Torna al profilo se si è al primo step

        elif action == 'next':
            # Salva i dati per lo step corrente
            if step == 1:
                dip.nome = form.nome.data
                dip.cognome = form.cognome.data
                dip.data_nascita = form.data_nascita.data
                dip.luogo_nascita = form.luogo_nascita.data
                dip.provincia_nascita = form.provincia_nascita.data
                dip.codice_fiscale = form.codice_fiscale.data
                dip.email = form.email.data
                dip.telefono = form.telefono.data
            elif step == 2:
                dip.matricola = form.matricola.data
                dip.reparto = form.reparto.data
                dip.ruolo = form.ruolo.data
                dip.data_assunzione_somministrazione = form.data_assunzione_somministrazione.data
                dip.agenzia_somministrazione = form.agenzia_somministrazione.data
                dip.data_assunzione_indeterminato = form.data_assunzione_indeterminato.data
                dip.legge_104 = form.legge_104.data == 'si'
                dip.donatore_avis = form.donatore_avis.data == 'si'
            elif step == 3:
                dip.indirizzo_residenza = form.indirizzo_residenza.data
                dip.citta_residenza = form.citta_residenza.data
                dip.provincia_residenza = form.provincia_residenza.data
                dip.cap_residenza = form.cap_residenza.data
            elif step == 4:
                # Gestione competenze (rimuovi vecchie, aggiungi nuove con percentuali)
                # Rimuovi tutte le competenze esistenti per questo dipendente
                DipendenteCompetenza.query.filter_by(dipendente_id=dip.id).delete()
                
                competenze_selezionate_ids = request.form.getlist('competenze')
                for comp_id_str in competenze_selezionate_ids:
                    comp_id = int(comp_id_str)
                    percentuale_str = request.form.get(f'percentuale_{comp_id}', '0')
                    percentuale = int(percentuale_str) if percentuale_str.isdigit() else 0
                    
                    nuova_dip_competenza = DipendenteCompetenza(
                        dipendente_id=dip.id,
                        competenza_id=comp_id,
                        percentuale=percentuale
                    )
                    db.session.add(nuova_dip_competenza)
            elif step == 5:
                # Gestione vestiario (rimuovi vecchi, aggiungi nuovi)
                # Questo è un many-to-many semplice, quindi WTForms dovrebbe gestirlo con form.populate_obj se il campo è corretto
                # Tuttavia, la gestione many-to-many con SelectMultipleField può essere tricky per l'update.
                # Un approccio più sicuro è cancellare e ricreare le associazioni.
                dip.vestiario = [] # Rimuove le vecchie associazioni
                selected_vestiario_ids = form.vestiario.data
                if selected_vestiario_ids:
                    for vest_id in selected_vestiario_ids:
                        item = VestiarioItem.query.get(vest_id)
                        if item:
                            dip.vestiario.append(item)
            
            db.session.commit()
            flash(f'Dati dello step {step} aggiornati con successo!', 'success')

            if step < 5: # Assumendo 5 step totali
                return redirect(url_for('modulo8.modifica_dipendente_step', id=dip.id, step=step+1))
            else:
                # Dopo l'ultimo step, torna al profilo del dipendente
                return redirect(url_for('modulo8.profilo_dipendente', id=dip.id))

    # Per il GET request, se non è validate_on_submit, semplicemente renderizza il template
    # con il form pre-compilato.
    
    competenze_lista = None
    dip_competenze_percentuali = {}
    if step == 4:
        competenze_lista = Competenza.query.order_by(Competenza.nome).all()
        # Iterate over dip.competenze_associate to get DipendenteCompetenza objects
        for dc_assoc in dip.competenze_associate: 
            dip_competenze_percentuali[dc_assoc.competenza_id] = dc_assoc.percentuale

    return render_template(
        'modulo8/dipendenti/modifica_step.html',
        form=form,
        step=step,
        is_new=False, # Stiamo modificando, non creando
        dip=dip,      # Passa l'oggetto dipendente al template
        competenze_lista=competenze_lista, # Per lo step 4
        dip_competenze_percentuali=dip_competenze_percentuali # Per pre-compilare le percentuali step 4
    )

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

@modulo8.route('/formazione')
@login_required
@admin_required
def formazione():
    return render_template('modulo8/formazione.html', title="Gestione Formazione")

@modulo8.route('/sicurezza')
@login_required
@admin_required
def sicurezza():
    return render_template('modulo8/sicurezza.html', title="Gestione Sicurezza")

@modulo8.route('/formazione/corsi')
@login_required
@admin_required
def lista_corsi():
    show_archived = request.args.get('show_archived', 'false') == 'true'
    query = CorsoFormazione.query
    if not show_archived:
        query = query.filter_by(archiviato=False)
    corsi = query.order_by(CorsoFormazione.giorno_inizio.desc()).all()
    return render_template('modulo8/corsi/lista.html', corsi=corsi, show_archived=show_archived)

@modulo8.route('/formazione/corsi/nuovo', methods=['GET', 'POST'])
@login_required
@admin_required
def nuovo_corso():
    form = CorsoFormazioneForm()
    if form.validate_on_submit():
        corso = CorsoFormazione(
            titolo=form.titolo.data,
            descrizione=form.descrizione.data,
            durata_ore=form.durata_ore.data,
            giorno_inizio=form.giorno_inizio.data,
            giorno_fine=form.giorno_fine.data,
            scadenza_relativa=form.scadenza_relativa.data,
            is_obbligatorio=form.is_obbligatorio.data,
            created_by_id=current_user.id
        )
        db.session.add(corso)
        db.session.commit()
        flash('Corso creato con successo!', 'success')
        return redirect(url_for('modulo8.lista_corsi'))
    return render_template('modulo8/corsi/nuovo.html', title='Nuovo Corso', form=form)

@modulo8.route('/formazione/corsi/<int:id>')
@login_required
@admin_required
def dettaglio_corso(id):
    corso = CorsoFormazione.query.get_or_404(id)
    partecipazioni = PartecipazioneCorso.query.filter_by(corso_id=id).all()
    return render_template('modulo8/corsi/dettaglio.html', corso=corso, partecipazioni=partecipazioni)

@modulo8.route('/formazione/corsi/<int:id>/modifica', methods=['GET', 'POST'])
@login_required
@admin_required
def modifica_corso(id):
    corso = CorsoFormazione.query.get_or_404(id)
    form = CorsoFormazioneForm(obj=corso)
    if form.validate_on_submit():
        corso.titolo = form.titolo.data
        corso.descrizione = form.descrizione.data
        corso.durata_ore = form.durata_ore.data
        corso.giorno_inizio = form.giorno_inizio.data
        corso.giorno_fine = form.giorno_fine.data
        corso.scadenza_relativa = form.scadenza_relativa.data
        corso.is_obbligatorio = form.is_obbligatorio.data
        db.session.commit()
        flash('Corso aggiornato con successo!', 'success')
        return redirect(url_for('modulo8.dettaglio_corso', id=corso.id))
    return render_template('modulo8/corsi/nuovo.html', title='Modifica Corso', form=form, corso=corso)

@modulo8.route('/formazione/corsi/<int:id>/partecipanti/nuovo', methods=['GET', 'POST'])
@login_required
@admin_required
def nuovo_partecipante(id):
    corso = CorsoFormazione.query.get_or_404(id)
    form = PartecipazioneCorsoForm()
    dipendenti = Dipendente.query.filter_by(archiviato=False).order_by(Dipendente.nome).all()
    form.dipendenti.choices = [(d.id, f"{d.nome} {d.cognome}") for d in dipendenti]
    dipendenti_dict = {d.id: d for d in dipendenti}
    
    if form.validate_on_submit():
        for dip_id in form.dipendenti.data:
            partecipazione = PartecipazioneCorso(
                dipendente_id=dip_id,
                corso_id=id,
                stato=form.stato.data,
                valutazione=form.valutazione.data,
                note=form.note.data
            )
            if form.stato.data == 'completato':
                partecipazione.data_completamento = datetime.utcnow()
            db.session.add(partecipazione)
        db.session.commit()
        flash('Partecipanti aggiunti con successo', 'success')
        return redirect(url_for('modulo8.dettaglio_corso', id=id))
    return render_template('modulo8/corsi/nuovo_partecipante.html', form=form, corso=corso, dipendenti_dict=dipendenti_dict)

@modulo8.route('/formazione/corsi/partecipanti/<int:id>/modifica', methods=['GET', 'POST'])
@login_required
@admin_required
def modifica_partecipante(id):
    partecipazione = PartecipazioneCorso.query.get_or_404(id)
    form = PartecipazioneCorsoForm(obj=partecipazione)
    if form.validate_on_submit():
        partecipazione.stato = form.stato.data
        partecipazione.valutazione = form.valutazione.data
        partecipazione.note = form.note.data
        if form.stato.data == 'completato' and not partecipazione.data_completamento:
            partecipazione.data_completamento = datetime.utcnow()
        db.session.commit()
        flash('Partecipazione modificata con successo', 'success')
        return redirect(url_for('modulo8.dettaglio_corso', id=partecipazione.corso_id))
    return render_template('modulo8/corsi/modifica_partecipante.html', form=form, partecipazione=partecipazione)

@modulo8.route('/formazione/corsi/<int:id>/archivia', methods=['POST'])
@login_required
@admin_required
def archivia_corso(id):
    corso = CorsoFormazione.query.get_or_404(id)
    corso.archiviato = True
    db.session.commit()
    flash('Corso archiviato con successo', 'success')
    return redirect(url_for('modulo8.lista_corsi'))

@modulo8.route('/formazione/corsi/<int:id>/elimina', methods=['POST'])
@login_required
@admin_required
def elimina_corso(id):
    corso = CorsoFormazione.query.get_or_404(id)
    db.session.delete(corso)
    db.session.commit()
    flash('Corso eliminato con successo', 'success')
    return redirect(url_for('modulo8.lista_corsi'))

@modulo8.route('/formazione/corsi/<int:id>/ripristina', methods=['POST'])
@login_required
@admin_required
def ripristina_corso(id):
    corso = CorsoFormazione.query.get_or_404(id)
    corso.archiviato = False
    db.session.commit()
    flash('Corso ripristinato con successo', 'success')
    return redirect(url_for('modulo8.lista_corsi'))

@modulo8.route('/formazione/corsi/partecipanti/<int:id>/elimina', methods=['POST'])
@login_required
@admin_required
def elimina_partecipante(id):
    partecipazione = PartecipazioneCorso.query.get_or_404(id)
    corso_id = partecipazione.corso_id
    db.session.delete(partecipazione)
    db.session.commit()
    flash('Partecipante eliminato con successo', 'success')
    return redirect(url_for('modulo8.dettaglio_corso', id=corso_id))

@modulo8.route('/formazione/corsi/<int:id>/partecipanti/elimina', methods=['POST'])
@login_required
@admin_required
def elimina_partecipanti(id):
    ids = request.form.getlist('partecipanti_ids')
    if ids:
        PartecipazioneCorso.query.filter(PartecipazioneCorso.id.in_(ids)).delete(synchronize_session=False)
        db.session.commit()
        flash(f'Eliminati {len(ids)} partecipanti selezionati', 'success')
    else:
        flash('Nessun partecipante selezionato', 'warning')
    return redirect(url_for('modulo8.dettaglio_corso', id=id))

@modulo8.route('/dipendenti/<int:id>/modifica-campo', methods=['POST'])
@login_required
@admin_required
def modifica_campo_dipendente(id):
    dip = Dipendente.query.get_or_404(id)
    field_name = request.form.get('field_name')
    field_value = request.form.get('field_value')
    
    # Lista dei campi modificabili
    allowed_fields = [
        'nome', 'cognome', 'data_nascita', 'luogo_nascita', 'provincia_nascita',
        'codice_fiscale', 'email', 'telefono', 'legge_104', 'donatore_avis',
        'matricola', 'reparto', 'ruolo', 'data_assunzione_somministrazione',
        'agenzia_somministrazione', 'data_assunzione_indeterminato',
        'indirizzo_residenza', 'citta_residenza', 'provincia_residenza', 'cap_residenza'
    ]
    
    if field_name not in allowed_fields:
        flash('Campo non valido', 'danger')
        return redirect(url_for('modulo8.profilo_dipendente', id=id))
    
    # Gestione campi speciali
    if field_name in ['data_nascita', 'data_assunzione_somministrazione', 'data_assunzione_indeterminato']:
        if field_value:
            field_value = datetime.strptime(field_value, '%Y-%m-%d').date()
        else:
            field_value = None
    elif field_name in ['legge_104', 'donatore_avis']:
        field_value = field_value == 'true'
    
    # Aggiorna il campo
    setattr(dip, field_name, field_value)
    db.session.commit()
    
    flash('Campo aggiornato con successo', 'success')
    return redirect(url_for('modulo8.profilo_dipendente', id=id))

@modulo8.route('/dipendenti/<int:id>/modifica-percentuale-competenza', methods=['POST'])
@login_required
@admin_required
def modifica_percentuale_competenza(id):
    dip = Dipendente.query.get_or_404(id)
    competenza_id = request.form.get('competenza_id', type=int)
    percentuale = request.form.get('percentuale', type=int)
    
    if not competenza_id or not isinstance(percentuale, int) or percentuale < 0 or percentuale > 100:
        flash('Dati non validi', 'danger')
        return redirect(url_for('modulo8.profilo_dipendente', id=id))
    
    # Trova l'associazione dipendente-competenza
    dip_comp = DipendenteCompetenza.query.filter_by(
        dipendente_id=id,
        competenza_id=competenza_id
    ).first()
    
    if not dip_comp:
        flash('Competenza non trovata', 'danger')
        return redirect(url_for('modulo8.profilo_dipendente', id=id))
    
    # Aggiorna la percentuale
    dip_comp.percentuale = percentuale
    db.session.commit()
    
    flash('Percentuale competenza aggiornata con successo', 'success')
    return redirect(url_for('modulo8.profilo_dipendente', id=id))

@modulo8.route('/dipendenti/<int:id>/formazione')
@login_required
@admin_required
def formazione_dipendente(id):
    dip = Dipendente.query.get_or_404(id)
    corsi = CorsoFormazione.query.filter_by(archiviato=False).all()
    return render_template('modulo8/dipendenti/formazione.html', dip=dip, corsi=corsi)

@modulo8.route('/dipendenti/<int:id>/sicurezza')
@login_required
@admin_required
def sicurezza_dipendente(id):
    dip = Dipendente.query.get_or_404(id)
    corsi_sicurezza = CorsoSicurezza.query.filter_by(archiviato=False).all()
    return render_template('modulo8/dipendenti/sicurezza.html', 
                         dip=dip, 
                         corsi_sicurezza=corsi_sicurezza,
                         now=datetime.utcnow())

@modulo8.route('/partecipazione/<int:id>/completa', methods=['POST'])
@login_required
@admin_required
def completa_partecipazione(id):
    partecipazione = PartecipazioneCorso.query.get_or_404(id)
    data = request.get_json()
    valutazione = data.get('valutazione')
    
    if not isinstance(valutazione, int) or valutazione < 1 or valutazione > 5:
        return jsonify({'error': 'Valutazione non valida'}), 400
    
    partecipazione.stato = 'completato'
    partecipazione.data_completamento = datetime.utcnow()
    partecipazione.valutazione = valutazione
    db.session.commit()
    
    return jsonify({'success': True})

@modulo8.route('/corso-sicurezza/<int:id>/completa', methods=['POST'])
@login_required
@admin_required
def completa_corso_sicurezza(id):
    corso = CorsoSicurezza.query.get_or_404(id)
    corso.is_completato = True
    corso.data_completamento = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})

@modulo8.route('/dipendenti/<int:dipendente_id>/iscrivi-corso/<int:corso_id>', methods=['POST'])
@login_required
@admin_required
def iscrivi_corso(dipendente_id, corso_id):
    dip = Dipendente.query.get_or_404(dipendente_id)
    corso = CorsoFormazione.query.get_or_404(corso_id)
    
    # Verifica se il dipendente è già iscritto
    if PartecipazioneCorso.query.filter_by(dipendente_id=dipendente_id, corso_id=corso_id).first():
        flash('Il dipendente è già iscritto a questo corso', 'warning')
        return redirect(url_for('modulo8.formazione_dipendente', id=dipendente_id))
    
    partecipazione = PartecipazioneCorso(
        dipendente_id=dipendente_id,
        corso_id=corso_id,
        stato='da_iniziare'
    )
    db.session.add(partecipazione)
    db.session.commit()
    
    flash('Dipendente iscritto al corso con successo', 'success')
    return redirect(url_for('modulo8.formazione_dipendente', id=dipendente_id))

@modulo8.route('/dipendenti/<int:dipendente_id>/assegna-corso-sicurezza/<int:corso_id>', methods=['POST'])
@login_required
@admin_required
def assegna_corso_sicurezza(dipendente_id, corso_id):
    dip = Dipendente.query.get_or_404(dipendente_id)
    corso = CorsoSicurezza.query.get_or_404(corso_id)
    
    # Verifica se il corso è già assegnato
    if corso in dip.corsi_sicurezza:
        flash('Il corso è già assegnato a questo dipendente', 'warning')
        return redirect(url_for('modulo8.sicurezza_dipendente', id=dipendente_id))
    
    dip.corsi_sicurezza.append(corso)
    db.session.commit()
    
    flash('Corso di sicurezza assegnato con successo', 'success')
    return redirect(url_for('modulo8.sicurezza_dipendente', id=dipendente_id))
