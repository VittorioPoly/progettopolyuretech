from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Dipendente, Competenza, Timbratura, VestiarioItem, Inventory, PrelievoVestiario
from app.utils import admin_required
from datetime import datetime
from calendar import monthrange
from app.models import PrelievoVestiario, Inventory, Dipendente
from app.forms import DipendenteForm
from app.models import Dipendente

modulo8 = Blueprint('modulo8', __name__, url_prefix='/modulo8')

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
    form = DipendenteForm()
    if form.validate_on_submit():
        # crea e salva il dipendente
        dip = Dipendente(
            nome=form.nome.data,
            cognome=form.cognome.data,
            email=form.email.data,
            telefono=form.telefono.data,
            data_assunzione=form.data_assunzione.data,
            reparto=form.reparto.data,
            ruolo=form.ruolo.data,
            note=form.note.data,
            created_by_id=current_user.id
        )
        # assegna competenze (many-to-many)
        dip.competenze = Competenza.query.filter(
            Competenza.id.in_(form.competenze.data)
        ).all()
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

@modulo8.route('/competenze/nuova', methods=['GET','POST'])
@login_required
@admin_required
def nuova_competenza():
    if request.method == 'POST':
        comp = Competenza(
            nome=request.form['nome'], descrizione=request.form.get('descrizione'),
            livello=request.form.get('livello'), area=request.form.get('area'),
            created_by_id=current_user.id
        )
        db.session.add(comp); db.session.commit()
        flash('Competenza creata', 'success')
        return redirect(url_for('modulo8.gestione_competenze'))
    return render_template('modulo8/competenze/form.html')

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
