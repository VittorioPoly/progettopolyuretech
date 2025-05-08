import os
import io
import base64
import matplotlib.pyplot as plt
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models import DatiExcel, RecordExcel
from app.forms import Modulo9ExcelUploadForm
from app.utils import admin_required, process_modulo9_excel

modulo9 = Blueprint('modulo9', __name__)

@modulo9.route('/modulo9')
@login_required
@admin_required
def index():
    page = request.args.get('page', 1, type=int)
    excel_files = DatiExcel.query.order_by(DatiExcel.uploaded_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('modulo9/index.html', title='Analisi Dati Excel', excel_files=excel_files)


@modulo9.route('/modulo9/upload', methods=['GET', 'POST'])
@login_required
@admin_required
def upload():
    form = Modulo9ExcelUploadForm()
    if form.validate_on_submit():
        file = form.excel_file.data
        filename = secure_filename(file.filename)
        filepath = os.path.join(os.getenv('UPLOAD_EXCEL_FOLDER'), f"modulo9_{filename}")
        file.save(filepath)

        excel_db = DatiExcel(
            nome_file=filename,
            descrizione=form.descrizione.data,
            uploaded_by_id=current_user.id
        )
        db.session.add(excel_db)
        db.session.flush()

        success, message = process_modulo9_excel(filepath, excel_db.id)
        if success:
            db.session.commit()
            flash(f'File caricato con successo: {message}', 'success')
            return redirect(url_for('modulo9.analyze', id=excel_db.id))
        else:
            db.session.rollback()
            flash(f'Errore nel caricamento: {message}', 'danger')

    return render_template('modulo9/upload.html', title='Carica Excel per Analisi', form=form)


@modulo9.route('/modulo9/analyze/<int:id>')
@login_required
@admin_required
def analyze(id):
    excel_file = DatiExcel.query.get_or_404(id)
    records = RecordExcel.query.filter_by(dati_excel_id=excel_file.id).all()

    columns = {}
    if records:
        sample_record = records[0]
        columns = {
            'colonna1': 'Colonna 1',
            'colonna2': 'Colonna 2',
            'colonna3': 'Colonna 3',
            'colonna4': 'Colonna 4',
            'colonna5': 'Colonna 5',
            'colonna6': 'Colonna 6'
        }

    return render_template('modulo9/analyze.html', title=f'Analisi Excel - {excel_file.nome_file}',
                           excel_file=excel_file, records=records, columns=columns)


@modulo9.route('/modulo9/chart/<int:id>/<string:column>')
@login_required
@admin_required
def chart(id, column):
    excel_file = DatiExcel.query.get_or_404(id)
    if not hasattr(RecordExcel, column):
        flash('Colonna non valida', 'danger')
        return redirect(url_for('modulo9.analyze', id=id))

    if column in ['colonna3', 'colonna4']:
        data = db.session.query(getattr(RecordExcel, column)).filter_by(dati_excel_id=excel_file.id).all()
        values = [float(d[0]) for d in data if d[0] is not None]

        plt.figure(figsize=(10, 6))
        plt.hist(values, bins=10)
        plt.title(f'Distribuzione {column}')
        plt.xlabel('Valore')
        plt.ylabel('Frequenza')
        plt.grid(True)

        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)

        chart_url = base64.b64encode(img.getvalue()).decode()
        plt.close()

        return render_template('modulo9/chart.html',
                               title=f'Grafico {column} - {excel_file.nome_file}',
                               chart_url=f'data:image/png;base64,{chart_url}',
                               column=column, excel_file=excel_file)
    else:
        flash('Tipo di colonna non supportato per grafici', 'warning')
        return redirect(url_for('modulo9.analyze', id=id))
