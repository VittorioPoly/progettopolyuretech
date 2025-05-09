from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Dipendente, Competenza
from app.utils import admin_required

modulo8 = Blueprint('modulo8', __name__)

@modulo8.route('/modulo8')
@login_required
@admin_required
def index():
    dipendenti = Dipendente.query.order_by(Dipendente.nome).all()
    competenze = Competenza.query.order_by(Competenza.nome).all()
    return render_template('modulo8.html', title="Gestione Dipendenti e Competenze",
                           dipendenti=dipendenti, competenze=competenze)

@modulo8.route('/modulo8/dipendente/aggiungi', methods=['POST'])
@login_required
@admin_required
def aggiungi_dipendente():
    nome = request.form.get('nome')
    cognome = request.form.get('cognome')
    email = request.form.get('email')
    telefono = request.form.get('telefono')
    reparto = request.form.get('reparto')
    ruolo = request.form.get('ruolo')
    note = request.form.get('note')

    dip = Dipendente(
        nome=nome,
        cognome=cognome,
        email=email,
        telefono=telefono,
        reparto=reparto,
        ruolo=ruolo,
        note=note,
        created_by_id=current_user.id
    )
    db.session.add(dip)
    db.session.commit()
    flash('Dipendente aggiunto con successo', 'success')
    return redirect(url_for('modulo8.index'))

@modulo8.route('/modulo8/competenza/aggiungi', methods=['POST'])
@login_required
@admin_required
def aggiungi_competenza():
    nome = request.form.get('nome')
    descrizione = request.form.get('descrizione')
    livello = request.form.get('livello')
    area = request.form.get('area')

    comp = Competenza(
        nome=nome,
        descrizione=descrizione,
        livello=livello,
        area=area,
        created_by_id=current_user.id
    )
    db.session.add(comp)
    db.session.commit()
    flash('Competenza aggiunta con successo', 'success')
    return redirect(url_for('modulo8.index'))

@modulo8.route('/modulo8/associa', methods=['POST'])
@login_required
@admin_required
def associa_competenza():
    dipendente_id = request.form.get('dipendente_id')
    competenza_id = request.form.get('competenza_id')

    dip = Dipendente.query.get(dipendente_id)
    comp = Competenza.query.get(competenza_id)
    if comp not in dip.competenze:
        dip.competenze.append(comp)
        db.session.commit()
        flash('Competenza associata al dipendente', 'success')
    else:
        flash('Competenza già associata', 'warning')
    return redirect(url_for('modulo8.index'))

@modulo8.route('/modulo8/dipendente/<int:id>/rimuovi', methods=['POST'])
@login_required
@admin_required
def rimuovi_dipendente(id):
    dip = Dipendente.query.get_or_404(id)
    db.session.delete(dip)
    db.session.commit()
    flash('Dipendente rimosso', 'info')
    return redirect(url_for('modulo8.index'))

@modulo8.route('/modulo8/competenza/<int:id>/rimuovi', methods=['POST'])
@login_required
@admin_required
def rimuovi_competenza(id):
    comp = Competenza.query.get_or_404(id)
    db.session.delete(comp)
    db.session.commit()
    flash('Competenza rimossa', 'info')
    return redirect(url_for('modulo8.index'))
