import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models import Modulo1Entry, Modulo1Photo
from app.forms import Modulo1EntryForm, Modulo1ViewForm
from app.utils import admin_required
from flask import current_app as app

modulo1 = Blueprint('modulo1', __name__)

@modulo1.route('/modulo1')
@login_required
def index():
    if current_user.is_admin():
        return redirect(url_for('modulo1.list'))
    else:
        return redirect(url_for('modulo1.add'))


@modulo1.route('/modulo1/add', methods=['GET', 'POST'])
@login_required
def add():
    form = Modulo1EntryForm()
    if form.validate_on_submit():
        entry = Modulo1Entry(
            valore_numerico=form.valore_numerico.data,
            note=form.note.data,
            user_id=current_user.id
        )
        db.session.add(entry)
        db.session.flush()

        photos = request.files.getlist('photos')
        if photos and photos[0].filename:
            for photo in photos:
                filename = secure_filename(photo.filename)
                photo_path = os.path.join(app.config['UPLOAD_IMAGES_FOLDER'], f"modulo1_{entry.id}_{filename}")
                photo.save(photo_path)

                photo_db = Modulo1Photo(
                    filename=filename,
                    path=os.path.relpath(photo_path, app.static_folder),
                    description=f"Foto allegata a modulo 1, entry {entry.id}",
                    entry_id=entry.id
                )
                db.session.add(photo_db)

        db.session.commit()
        flash('Dati inseriti con successo', 'success')
        return redirect(url_for('modulo1.add'))

    return render_template('modulo1/add.html', title='Inserisci Dati - Modulo 1', form=form)


@modulo1.route('/modulo1/list')
@login_required
@admin_required
def list():
    page = request.args.get('page', 1, type=int)
    entries = Modulo1Entry.query.order_by(Modulo1Entry.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('modulo1/list.html', title='Elenco Dati - Modulo 1', entries=entries)


@modulo1.route('/modulo1/view/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def view(id):
    entry = Modulo1Entry.query.get_or_404(id)
    form = Modulo1ViewForm()

    if form.validate_on_submit():
        if form.mark_viewed.data and not entry.viewed:
            entry.viewed = True
            entry.viewed_at = datetime.utcnow()
            entry.viewed_by_id = current_user.id
            db.session.commit()
            flash('Dato segnato come visto', 'success')
        return redirect(url_for('modulo1.list'))

    form.entry_id.data = entry.id
    photos = Modulo1Photo.query.filter_by(entry_id=entry.id).all()
    return render_template('modulo1/view.html', title=f'Visualizza Dato - Modulo 1', entry=entry, form=form, photos=photos)
