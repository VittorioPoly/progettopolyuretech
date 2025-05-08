import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from werkzeug.utils import secure_filename

from app import db
from app.models import Cliente, Fatturato
from app.forms import ClienteForm, ExcelUploadForm, DateRangeForm
from app.utils import admin_required, process_fatturato_excel, generate_fatturato_chart

modulo2 = Blueprint('modulo2', __name__)

@modulo2.route('/modulo2')
@login_required
@admin_required
def index():
    return render_template('modulo2/index.html', title='Analisi Fatturato Clienti')


@modulo2.route('/modulo2/upload', methods=['GET', 'POST'])
@login_required
@admin_required
def upload():
    form = ExcelUploadForm()
    if form.validate_on_submit():
        file = form.excel_file.data
        filename = secure_filename(file.filename)
        filepath = os.path.join(os.getenv('UPLOAD_EXCEL_FOLDER'), filename)
        file.save(filepath)

        success, message = process_fatturato_excel(filepath)
        if success:
            flash(f'File caricato con successo: {message}', 'success')
            return redirect(url_for('modulo2.index'))
        else:
            flash(f'Errore nel caricamento: {message}', 'danger')

    return render_template('modulo2/upload.html', title='Carica Excel Fatturato', form=form)


@modulo2.route('/modulo2/clienti')
@login_required
@admin_required
def clienti():
    page = request.args.get('page', 1, type=int)
    clienti = Cliente.query.order_by(Cliente.nome).paginate(page=page, per_page=10, error_out=False)
    return render_template('modulo2/clienti.html', title='Gestione Clienti', clienti=clienti)


@modulo2.route('/modulo2/cliente/add', methods=['GET', 'POST'])
@login_required
@admin_required
def cliente_add():
    form = ClienteForm()
    if form.validate_on_submit():
        cliente = Cliente(
            nome=form.nome.data,
            codice=form.codice.data,
            email=form.email.data,
            telefono=form.telefono.data,
            indirizzo=form.indirizzo.data
        )
        db.session.add(cliente)
        db.session.commit()
        flash(f'Cliente {form.nome.data} aggiunto con successo', 'success')
        return redirect(url_for('modulo2.clienti'))

    return render_template('modulo2/cliente_form.html', title='Aggiungi Cliente', form=form)


@modulo2.route('/modulo2/fatturato/trend')
@login_required
@admin_required
def fatturato_trend():
    form = DateRangeForm()
    start_date = form.start_date.data if form.validate() else None
    end_date = form.end_date.data if form.validate() else None

    query = db.session.query(
        Fatturato.data,
        db.func.sum(Fatturato.importo).label('total')
    ).group_by(Fatturato.data).order_by(Fatturato.data)

    if start_date:
        query = query.filter(Fatturato.data >= start_date)
    if end_date:
        query = query.filter(Fatturato.data <= end_date)

    results = query.all()
    chart_data = {
        'date': [r.data.strftime('%Y-%m-%d') for r in results],
        'amounts': [float(r.total) for r in results]
    }
    chart_url = generate_fatturato_chart(chart_data)

    return render_template('modulo2/fatturato_trend.html', title='Andamento Fatturato', form=form, chart_url=chart_url)


@modulo2.route('/modulo2/fatturato/cliente/<int:cliente_id>')
@login_required
@admin_required
def fatturato_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    form = DateRangeForm()
    start_date = form.start_date.data if form.validate() else None
    end_date = form.end_date.data if form.validate() else None

    query = Fatturato.query.filter_by(cliente_id=cliente.id)
    if start_date:
        query = query.filter(Fatturato.data >= start_date)
    if end_date:
        query = query.filter(Fatturato.data <= end_date)

    fatturati = query.order_by(Fatturato.data.desc()).all()
    totale = sum(f.importo for f in fatturati)

    return render_template('modulo2/fatturato_cliente.html', title=f'Fatturato - {cliente.nome}', cliente=cliente, fatturati=fatturati, totale=totale, form=form)
