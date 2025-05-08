import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user

from app import db
from app.models import Modulo4Entry
from app.forms import Modulo4EntryForm
from app.utils import admin_required, generate_pdf

modulo4 = Blueprint('modulo4', __name__)

@modulo4.route('/modulo4')
@login_required
@admin_required
def index():
    page = request.args.get('page', 1, type=int)
    entries = Modulo4Entry.query.order_by(Modulo4Entry.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('modulo4/index.html', title='Generazione PDF', entries=entries)


@modulo4.route('/modulo4/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add():
    form = Modulo4EntryForm()
    if form.validate_on_submit():
        entry = Modulo4Entry(
            titolo=form.titolo.data,
            valore1=form.valore1.data,
            valore2=form.valore2.data,
            valore3=form.valore3.data,
            note=form.note.data,
            created_by_id=current_user.id
        )
        db.session.add(entry)
        db.session.flush()

        data = {
            'Titolo': form.titolo.data,
            'Valore 1': form.valore1.data,
            'Valore 2': form.valore2.data or 'Non specificato',
            'Valore 3': form.valore3.data or 'Non specificato',
            'Note': form.note.data or 'Nessuna nota',
            'Data creazione': datetime.utcnow().strftime('%d/%m/%Y %H:%M'),
            'Creato da': current_user.username
        }
        filename = f"modulo4_report_{entry.id}.pdf"
        pdf_path = generate_pdf(data, filename)

        entry.pdf_path = os.path.relpath(pdf_path, os.getenv('STATIC_FOLDER'))
        db.session.commit()

        flash('PDF generato con successo', 'success')
        return redirect(url_for('modulo4.view', id=entry.id))

    return render_template('modulo4/add.html', title='Genera Nuovo PDF', form=form)


@modulo4.route('/modulo4/view/<int:id>')
@login_required
@admin_required
def view(id):
    entry = Modulo4Entry.query.get_or_404(id)
    return render_template('modulo4/view.html', title=f'Visualizza PDF - {entry.titolo}', entry=entry)


@modulo4.route('/modulo4/download/<int:id>')
@login_required
@admin_required
def download(id):
    entry = Modulo4Entry.query.get_or_404(id)
    if not entry.pdf_path:
        flash('PDF non disponibile', 'danger')
        return redirect(url_for('modulo4.index'))

    pdf_path = os.path.join(os.getenv('STATIC_FOLDER'), entry.pdf_path)
    return send_file(pdf_path, as_attachment=True, download_name=f"Report_{entry.titolo}.pdf")
