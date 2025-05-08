import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from werkzeug.utils import secure_filename

from app import db
from app.models import Fornitore, Spesa
from app.forms import FornitoreForm, ExcelUploadForm, DateRangeForm
from app.utils import admin_required, process_spese_excel, generate_spese_chart

modulo3 = Blueprint('modulo3', __name__)

@modulo3.route('/modulo3')
@login_required
@admin_required
def index():
    return render_template('modulo3/index.html', title='Analisi Spese Fornitori')


@modulo3.route('/modulo3/upload', methods=['GET', 'POST'])
@login_required
@admin_required
def upload():
    form = ExcelUploadForm()
    if form.validate_on_submit():
        file = form.excel_file.data
        filename = secure_filename(file.filename)
        filepath = os.path.join(os.getenv('UPLOAD_EXCEL_FOLDER'), filename)
        file.save(filepath)

        success, message = process_spese_excel(filepath)
        if success:
            flash(f'File caricato con successo: {message}', 'success')
            return redirect(url_for('modulo3.index'))
        else:
            flash(f'Errore nel caricamento: {message}', 'danger')

    return render_template('modulo3/upload.html', title='Carica Excel Spese', form=form)


@modulo3.route('/modulo3/fornitori')
@login_required
@admin_required
def fornitori():
    page = request.args.get('page', 1, type=int)
    fornitori = Fornitore.query.order_by(Fornitore.nome).paginate(page=page, per_page=10, error_out=False)
    return render_template('modulo3/fornitori.html', title='Gestione Fornitori', fornitori=fornitori)


@modulo3.route('/modulo3/fornitore/add', methods=['GET', 'POST'])
@login_required
@admin_required
def fornitore_add():
    form = FornitoreForm()
    if form.validate_on_submit():
        fornitore = Fornitore(
            nome=form.nome.data,
            codice=form.codice.data,
            email=form.email.data,
            telefono=form.telefono.data,
            indirizzo=form.indirizzo.data
        )
        db.session.add(fornitore)
        db.session.commit()
        flash(f'Fornitore {form.nome.data} aggiunto con successo', 'success')
        return redirect(url_for('modulo3.fornitori'))

    return render_template('modulo3/fornitore_form.html', title='Aggiungi Fornitore', form=form)


@modulo3.route('/modulo3/spese/trend')
@login_required
@admin_required
def spese_trend():
    form = DateRangeForm()
    start_date = form.start_date.data if form.validate() else None
    end_date = form.end_date.data if form.validate() else None

    query = db.session.query(
        Spesa.data,
        db.func.sum(Spesa.importo).label('total')
    ).group_by(Spesa.data).order_by(Spesa.data)

    if start_date:
        query = query.filter(Spesa.data >= start_date)
    if end_date:
        query = query.filter(Spesa.data <= end_date)

    results = query.all()
    chart_data = {
        'date': [r.data.strftime('%Y-%m-%d') for r in results],
        'amounts': [float(r.total) for r in results]
    }
    chart_url = generate_spese_chart(chart_data)

    return render_template('modulo3/spese_trend.html', title='Andamento Spese', form=form, chart_url=chart_url)


@modulo3.route('/modulo3/spese/fornitore/<int:fornitore_id>')
@login_required
@admin_required
def spese_fornitore(fornitore_id):
    fornitore = Fornitore.query.get_or_404(fornitore_id)
    form = DateRangeForm()
    start_date = form.start_date.data if form.validate() else None
    end_date = form.end_date.data if form.validate() else None

    query = Spesa.query.filter_by(fornitore_id=fornitore.id)
    if start_date:
        query = query.filter(Spesa.data >= start_date)
    if end_date:
        query = query.filter(Spesa.data <= end_date)

    spese = query.order_by(Spesa.data.desc()).all()
    totale = sum(s.importo for s in spese)

    return render_template('modulo3/spese_fornitore.html', title=f'Spese - {fornitore.nome}', fornitore=fornitore, spese=spese, totale=totale, form=form)
