from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models import Modulo6Entry
from app.forms import Modulo6EntryForm, Modulo6ViewForm
from app.utils import admin_required

modulo6 = Blueprint('modulo6', __name__)

@modulo6.route('/modulo6')
@login_required
@admin_required
def index():
    page = request.args.get('page', 1, type=int)
    entries = Modulo6Entry.query.order_by(Modulo6Entry.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('modulo6/index.html', title='Modulo 6 - Riepilogo', entries=entries)


@modulo6.route('/modulo6/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add():
    form = Modulo6EntryForm()
    if form.validate_on_submit():
        entry = Modulo6Entry(
            valore1=form.valore1.data,
            valore2=form.valore2.data,
            valore3=form.valore3.data,
            note=form.note.data,
            created_by_id=current_user.id
        )
        db.session.add(entry)
        db.session.commit()
        flash('Dati inseriti con successo', 'success')
        return redirect(url_for('modulo6.view', id=entry.id))

    return render_template('modulo6/add.html', title='Inserisci Dati - Modulo 6', form=form)


@modulo6.route('/modulo6/view/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def view(id):
    entry = Modulo6Entry.query.get_or_404(id)
    form = Modulo6ViewForm()

    if form.validate_on_submit():
        if form.mark_viewed.data and not entry.viewed:
            entry.viewed = True
            entry.viewed_at = datetime.utcnow()
            db.session.commit()
            flash('Dato segnato come visto', 'success')
        return redirect(url_for('modulo6.index'))

    form.entry_id.data = entry.id
    return render_template('modulo6/view.html', title=f'Visualizza Dato - Modulo 6', entry=entry, form=form)
