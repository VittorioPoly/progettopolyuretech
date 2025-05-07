import os
import io
import base64
from functools import wraps
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from werkzeug.utils import secure_filename
from flask import abort, current_app, flash
from flask_login import current_user

from app import db
from app.models import (Cliente, Fatturato, Fornitore, Spesa, 
                       DatiExcel, RecordExcel)


# ======================================================
# Decoratori per controllo accessi
# ======================================================

def admin_required(f):
    """Decoratore per limitare l'accesso agli amministratori"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)  # Accesso negato
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename, allowed_extensions):
    """Controlla se il file ha un'estensione permessa"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


# ======================================================
# Funzioni per generazione PDF
# ======================================================

def generate_pdf(data, filename):
    """Genera un PDF con i dati passati come dizionario"""
    pdf_dir = os.path.join(current_app.config['UPLOAD_PDF_FOLDER'])
    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir)
    
    pdf_path = os.path.join(pdf_dir, filename)
    
    # Crea PDF usando ReportLab
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Contenuto del PDF
    elements = []
    styles = getSampleStyleSheet()
    
    # Titolo
    title = styles['Heading1']
    elements.append(Paragraph("Report Dati", title))
    elements.append(Spacer(1, 20))
    
    # Contenuto
    table_data = []
    for key, value in data.items():
        table_data.append([key, str(value)])
    
    # Crea tabella
    t = Table(table_data, colWidths=[150, 300])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(t)
    
    # Piè di pagina con data e ora
    elements.append(Spacer(1, 20))
    footer_text = f"Documento generato il {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}"
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    # Costruisci il PDF
    doc.build(elements)
    
    return pdf_path


# ======================================================
# Funzioni per processare file Excel
# ======================================================

def process_fatturato_excel(file_path):
    """Elabora file Excel con dati di fatturato clienti"""
    try:
        # Leggi il file Excel
        df = pd.read_excel(file_path)
        
        # Verifica le colonne obbligatorie
        required_columns = ['cliente', 'data', 'importo']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return False, f"Colonne mancanti: {', '.join(missing_columns)}"
        
        # Processa ogni riga
        records_added = 0
        for _, row in df.iterrows():
            # Verifica se il cliente esiste
            cliente_nome = row['cliente']
            cliente = Cliente.query.filter_by(nome=cliente_nome).first()
            
            # Se il cliente non esiste, crealo
            if not cliente:
                cliente = Cliente(
                    nome=cliente_nome,
                    codice=f"AUTO_{len(cliente_nome)}_{datetime.utcnow().strftime('%Y%m%d')}",
                )
                db.session.add(cliente)
                db.session.flush()  # Ottieni l'ID assegnato
            
            # Crea il record di fatturato
            fatturato = Fatturato(
                data=row['data'],
                importo=row['importo'],
                descrizione=row.get('descrizione', ''),
                cliente_id=cliente.id,
                uploaded_by_id=current_user.id if current_user else None
            )
            
            db.session.add(fatturato)
            records_added += 1
        
        # Commit delle modifiche
        db.session.commit()
        
        return True, f"Importati {records_added} record di fatturato con successo."
    
    except Exception as e:
        db.session.rollback()
        return False, f"Errore durante l'elaborazione del file: {str(e)}"


def process_spese_excel(file_path):
    """Elabora file Excel con dati di spese fornitori"""
    try:
        # Leggi il file Excel
        df = pd.read_excel(file_path)
        
        # Verifica le colonne obbligatorie
        required_columns = ['fornitore', 'data', 'importo']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return False, f"Colonne mancanti: {', '.join(missing_columns)}"
        
        # Processa ogni riga
        records_added = 0
        for _, row in df.iterrows():
            # Verifica se il fornitore esiste
            fornitore_nome = row['fornitore']
            fornitore = Fornitore.query.filter_by(nome=fornitore_nome).first()
            
            # Se il fornitore non esiste, crealo
            if not fornitore:
                fornitore = Fornitore(
                    nome=fornitore_nome,
                    codice=f"AUTO_{len(fornitore_nome)}_{datetime.utcnow().strftime('%Y%m%d')}",
                )
                db.session.add(fornitore)
                db.session.flush()  # Ottieni l'ID assegnato
            
            # Crea il record di spesa
            spesa = Spesa(
                data=row['data'],
                importo=row['importo'],
                descrizione=row.get('descrizione', ''),
                fornitore_id=fornitore.id,
                uploaded_by_id=current_user.id if current_user else None
            )
            
            db.session.add(spesa)
            records_added += 1
        
        # Commit delle modifiche
        db.session.commit()
        
        return True, f"Importati {records_added} record di spese con successo."
    
    except Exception as e:
        db.session.rollback()
        return False, f"Errore durante l'elaborazione del file: {str(e)}"


def process_modulo9_excel(file_path, dati_excel_id):
    """Elabora file Excel generico per il Modulo 9"""
    try:
        # Leggi il file Excel
        df = pd.read_excel(file_path)
        
        # Limita il numero di righe per evitare problemi di memoria
        max_rows = 1000
        if len(df) > max_rows:
            df = df.head(max_rows)
            warning = f"Attenzione: il file contiene più di {max_rows} righe. Solo le prime {max_rows} saranno importate."
        else:
            warning = None
        
        # Determina le prime 6 colonne (o meno se ci sono meno colonne)
        columns = df.columns[:min(6, len(df.columns))]
        
        # Processa ogni riga
        records_added = 0
        for _, row in df.iterrows():
            # Crea il record excel
            record = RecordExcel(
                dati_excel_id=dati_excel_id,
            )
            
            # Assegna i valori delle colonne ai campi del modello
            # Colonna 1 e 2 come stringhe
            if len(columns) > 0:
                record.colonna1 = str(row[columns[0]])
            if len(columns) > 1:
                record.colonna2 = str(row[columns[1]])
            
            # Colonna 3 e 4 come numeri
            if len(columns) > 2:
                try:
                    record.colonna3 = float(row[columns[2]])
                except (ValueError, TypeError):
                    record.colonna3 = None
            
            if len(columns) > 3:
                try:
                    record.colonna4 = float(row[columns[3]])
                except (ValueError, TypeError):
                    record.colonna4 = None
            
            # Colonna 5 come data
            if len(columns) > 4:
                if pd.notna(row[columns[4]]) and isinstance(row[columns[4]], (datetime, pd.Timestamp)):
                    record.colonna5 = row[columns[4]]
                else:
                    record.colonna5 = None
            
            # Colonna 6 come stringa
            if len(columns) > 5:
                record.colonna6 = str(row[columns[5]])
            
            db.session.add(record)
            records_added += 1
        
        # Commit delle modifiche
        db.session.commit()
        
        message = f"Importati {records_added} record con successo."
        if warning:
            message = f"{warning} {message}"
            
        return True, message
    
    except Exception as e:
        db.session.rollback()
        return False, f"Errore durante l'elaborazione del file: {str(e)}"


# ======================================================
# Funzioni per generare grafici
# ======================================================

def generate_fatturato_chart(data):
    """Genera un grafico dell'andamento del fatturato"""
    # Crea la figura
    plt.figure(figsize=(10, 6))
    
    # Disegna il grafico
    plt.plot(data['date'], data['amounts'], marker='o', linestyle='-', color='b')
    
    # Aggiungi titolo e etichette
    plt.title('Andamento Fatturato')
    plt.xlabel('Data')
    plt.ylabel('Importo (€)')
    
    # Aggiungi griglia e ruota le etichette delle date
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)
    
    # Adatta il layout
    plt.tight_layout()
    
    # Salva il grafico in memoria
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=100)
    img.seek(0)
    
    # Chiudi la figura per liberare memoria
    plt.close()
    
    # Converti in base64 per visualizzazione HTML
    chart_url = base64.b64encode(img.getvalue()).decode()
    
    return f'data:image/png;base64,{chart_url}'


def generate_spese_chart(data):
    """Genera un grafico dell'andamento delle spese"""
    # Crea la figura
    plt.figure(figsize=(10, 6))
    
    # Disegna il grafico
    plt.plot(data['date'], data['amounts'], marker='o', linestyle='-', color='r')
    
    # Aggiungi titolo e etichette
    plt.title('Andamento Spese')
    plt.xlabel('Data')
    plt.ylabel('Importo (€)')
    
    # Aggiungi griglia e ruota le etichette delle date
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)
    
    # Adatta il layout
    plt.tight_layout()
    
    # Salva il grafico in memoria
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=100)
    img.seek(0)
    
    # Chiudi la figura per liberare memoria
    plt.close()
    
    # Converti in base64 per visualizzazione HTML
    chart_url = base64.b64encode(img.getvalue()).decode()
    
    return f'data:image/png;base64,{chart_url}'


def generate_pie_chart(labels, values, title):
    """Genera un grafico a torta generico"""
    # Crea la figura
    plt.figure(figsize=(8, 8))
    
    # Disegna il grafico a torta
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, shadow=True)
    
    # Aggiungi titolo e rendi la forma circolare
    plt.title(title)
    plt.axis('equal')
    
    # Adatta il layout
    plt.tight_layout()
    
    # Salva il grafico in memoria
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=100)
    img.seek(0)
    
    # Chiudi la figura per liberare memoria
    plt.close()
    
    # Converti in base64 per visualizzazione HTML
    chart_url = base64.b64encode(img.getvalue()).decode()
    
    return f'data:image/png;base64,{chart_url}'


def generate_bar_chart(labels, values, title, xlabel, ylabel):
    """Genera un grafico a barre generico"""
    # Crea la figura
    plt.figure(figsize=(10, 6))
    
    # Disegna il grafico a barre
    plt.bar(labels, values)
    
    # Aggiungi titolo e etichette
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    
    # Ruota le etichette se necessario
    if max(len(str(label)) for label in labels) > 5:
        plt.xticks(rotation=45)
    
    # Aggiungi griglia
    plt.grid(True, linestyle='--', alpha=0.7, axis='y')
    
    # Adatta il layout
    plt.tight_layout()
    
    # Salva il grafico in memoria
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=100)
    img.seek(0)
    
    # Chiudi la figura per liberare memoria
    plt.close()
    
    # Converti in base64 per visualizzazione HTML
    chart_url = base64.b64encode(img.getvalue()).decode()
    
    return f'data:image/png;base64,{chart_url}'


# ======================================================
# Funzioni per il calcolo di statistiche
# ======================================================

def calculate_stats(values):
    """Calcola statistiche di base per una serie di valori"""
    if not values or len(values) == 0:
        return {
            'count': 0,
            'min': None,
            'max': None,
            'mean': None,
            'median': None,
            'sum': None
        }
    
    # Converti in pandas Series per calcoli semplificati
    s = pd.Series(values)
    
    return {
        'count': len(s),
        'min': s.min(),
        'max': s.max(),
        'mean': s.mean(),
        'median': s.median(),
        'sum': s.sum()
    }


def get_fatturato_per_cliente(start_date=None, end_date=None):
    """Recupera il fatturato totale per cliente in un periodo"""
    query = db.session.query(
        Cliente.nome.label('cliente'),
        db.func.sum(Fatturato.importo).label('totale')
    ).join(Fatturato).group_by(Cliente.nome)
    
    if start_date:
        query = query.filter(Fatturato.data >= start_date)
    if end_date:
        query = query.filter(Fatturato.data <= end_date)
    
    return query.all()


def get_spese_per_fornitore(start_date=None, end_date=None):
    """Recupera le spese totali per fornitore in un periodo"""
    query = db.session.query(
        Fornitore.nome.label('fornitore'),
        db.func.sum(Spesa.importo).label('totale')
    ).join(Spesa).group_by(Fornitore.nome)
    
    if start_date:
        query = query.filter(Spesa.data >= start_date)
    if end_date:
        query = query.filter(Spesa.data <= end_date)
    
    return query.all()


def get_fatturato_mensile(year=None):
    """Recupera il fatturato mensile per un anno specifico"""
    query = db.session.query(
        db.func.strftime('%m', Fatturato.data).label('mese'),
        db.func.sum(Fatturato.importo).label('totale')
    ).group_by('mese')
    
    if year:
        query = query.filter(db.func.strftime('%Y', Fatturato.data) == str(year))
    
    results = query.all()
    
    # Converti in dizionario per facile accesso
    months = {
        '01': 'Gennaio', '02': 'Febbraio', '03': 'Marzo', '04': 'Aprile',
        '05': 'Maggio', '06': 'Giugno', '07': 'Luglio', '08': 'Agosto',
        '09': 'Settembre', '10': 'Ottobre', '11': 'Novembre', '12': 'Dicembre'
    }
    
    data = {months[r.mese]: float(r.totale) for r in results if r.mese in months}
    
    return data


def get_spese_mensili(year=None):
    """Recupera le spese mensili per un anno specifico"""
    query = db.session.query(
        db.func.strftime('%m', Spesa.data).label('mese'),
        db.func.sum(Spesa.importo).label('totale')
    ).group_by('mese')
    
    if year:
        query = query.filter(db.func.strftime('%Y', Spesa.data) == str(year))
    
    results = query.all()
    
    # Converti in dizionario per facile accesso
    months = {
        '01': 'Gennaio', '02': 'Febbraio', '03': 'Marzo', '04': 'Aprile',
        '05': 'Maggio', '06': 'Giugno', '07': 'Luglio', '08': 'Agosto',
        '09': 'Settembre', '10': 'Ottobre', '11': 'Novembre', '12': 'Dicembre'
    }
    
    data = {months[r.mese]: float(r.totale) for r in results if r.mese in months}
    
    return data