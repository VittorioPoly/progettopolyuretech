import os
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, abort, jsonify, send_file, session
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

from app import db, login_manager
from app.models import (User, Modulo1Entry, Modulo1Photo, Cliente, Fatturato, 
                      Fornitore, Spesa, Modulo4Entry, Modulo5Entry, Modulo5Photo, 
                      Modulo6Entry, Modulo7Entry, Dipendente, Competenza, 
                      DatiExcel, RecordExcel)
from app.forms import (LoginForm, RegistrationForm, ChangePasswordForm, Modulo1EntryForm, 
                     Modulo1ViewForm, ClienteForm, FatturatoForm, ExcelUploadForm, 
                     FornitoreForm, SpesaForm, Modulo4EntryForm, Modulo5EntryForm, 
                     Modulo5ViewForm, Modulo6EntryForm, Modulo6ViewForm, Modulo7EntryForm, 
                     Modulo7ViewForm, DipendenteForm, CompetenzaForm, AssegnaCompetenzaForm, 
                     Modulo9ExcelUploadForm, SearchForm, DateRangeForm)
from app.utils import (admin_required, generate_pdf, process_fatturato_excel, 
                     process_spese_excel, process_modulo9_excel, generate_fatturato_chart,
                     generate_spese_chart)

def register_routes(app):
    # ======================================================
    # Rotte per autenticazione e gestione utenti
    # ======================================================

    @app.route('/')
    @app.route('/index')
    @login_required
    def index():
        """Pagina iniziale con riepilogo dei moduli disponibili"""
        stats = {
            'modulo1_count': 0,
            'modulo1_unviewed': 0,
            'modulo5_count': 0,
            'modulo5_unviewed': 0,
            'fatturato_totale': 0,
            'clienti_count': 0,
            'users_count': 0,
            'admin_count': 0,
            'operatori_count': 0
        }
        
        if current_user.is_admin():
            # Statistiche Modulo 1
            stats['modulo1_count'] = Modulo1Entry.query.count()
            stats['modulo1_unviewed'] = Modulo1Entry.query.filter_by(viewed=False).count()
            
            # Statistiche Modulo 5
            stats['modulo5_count'] = Modulo5Entry.query.count()
            stats['modulo5_unviewed'] = Modulo5Entry.query.filter_by(viewed=False).count()
            
            # Statistiche Fatturato e Clienti
            from sqlalchemy import func
            stats['fatturato_totale'] = db.session.query(func.sum(Fatturato.importo)).scalar() or 0
            stats['clienti_count'] = Cliente.query.count()
            
            # Statistiche Utenti
            stats['users_count'] = User.query.count()
            stats['admin_count'] = User.query.filter_by(role='admin').count()
            stats['operatori_count'] = User.query.filter_by(role='operatore').count()
        
        # Attività recenti (ultimi 5 eventi)
        recent_activities = []
        return render_template('dashboard/index.html', title='Dashboard', stats=stats, recent_activities=recent_activities)
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Pagina di login"""
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user is None or not user.check_password(form.password.data):
                flash('Username o password non validi', 'danger')
                return redirect(url_for('login'))
            
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
            
            flash(f'Benvenuto, {user.username}!', 'success')
            return redirect(next_page)
        
        return render_template('auth/login.html', title='Accesso', form=form)

    @app.route('/logout')
    def logout():
        """Logout utente"""
        logout_user()
        flash('Hai effettuato il logout correttamente', 'success')
        return redirect(url_for('login'))

    @app.route('/register', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def register():
        """Registrazione nuovo utente (solo admin)"""
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(
                username=form.username.data,
                email=form.email.data,
                role=form.role.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash(f'Utente {form.username.data} registrato con successo!', 'success')
            return redirect(url_for('index'))
        
        return render_template('auth/register.html', title='Registrazione', form=form)

    @app.route('/change_password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        """Cambio password utente corrente"""
        form = ChangePasswordForm()
        if form.validate_on_submit():
            if not current_user.check_password(form.old_password.data):
                flash('Password attuale non corretta', 'danger')
                return redirect(url_for('change_password'))
            
            current_user.set_password(form.password.data)
            db.session.commit()
            flash('Password aggiornata con successo', 'success')
            return redirect(url_for('index'))
        
        return render_template('auth/change_password.html', title='Cambio Password', form=form)


    @app.route('/profile')
    @login_required
    def profile():
        """Profilo utente"""
        return render_template('auth/profile.html', title='Profilo')

# ======================================================
# Rotte per Modulo 1: Inserimento dati con foto (operatore/admin)
# ======================================================

    @app.route('/modulo1')
    @login_required
    def modulo1_index():
        """Pagina principale Modulo 1"""
        # Operatori vedono form inserimento, admin vedono riepilogo
        if current_user.is_admin():
            return redirect(url_for('modulo1_list'))
        else:
            return redirect(url_for('modulo1_add'))


    @app.route('/modulo1/add', methods=['GET', 'POST'])
    @login_required
    def modulo1_add():
        """Aggiunta dati Modulo 1 (operatore)"""
        form = Modulo1EntryForm()
        if form.validate_on_submit():
            # Salva i dati principali
            entry = Modulo1Entry(
                valore_numerico=form.valore_numerico.data,
                note=form.note.data,
                user_id=current_user.id
            )
            db.session.add(entry)
            db.session.flush()  # Per ottenere l'ID dell'entry
            
            # Salva le foto se presenti
            photos = request.files.getlist('photos')
            if photos and photos[0].filename:
                for photo in photos:
                    filename = secure_filename(photo.filename)
                    # Crea percorso univoco
                    photo_path = os.path.join(app.config['UPLOAD_IMAGES_FOLDER'], f"modulo1_{entry.id}_{filename}")
                    photo.save(photo_path)
                    
                    # Salva riferimento nel DB
                    photo_db = Modulo1Photo(
                        filename=filename,
                        path=os.path.relpath(photo_path, app.static_folder),
                        description=f"Foto allegata a modulo 1, entry {entry.id}",
                        entry_id=entry.id
                    )
                    db.session.add(photo_db)
            
            db.session.commit()
            flash('Dati inseriti con successo', 'success')
            return redirect(url_for('modulo1_add'))
        
        return render_template('modulo1/add.html', title='Inserisci Dati - Modulo 1', form=form)


    @app.route('/modulo1/list')
    @login_required
    @admin_required
    def modulo1_list():
        """Elenco dati Modulo 1 (admin)"""
        page = request.args.get('page', 1, type=int)
        entries = Modulo1Entry.query.order_by(Modulo1Entry.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False)
        
        return render_template('modulo1/list.html', title='Elenco Dati - Modulo 1', entries=entries)


    @app.route('/modulo1/view/<int:id>', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def modulo1_view(id):
        """Visualizzazione singolo dato Modulo 1 (admin)"""
        entry = Modulo1Entry.query.get_or_404(id)
        form = Modulo1ViewForm()
        
        if form.validate_on_submit():
            if form.mark_viewed.data and not entry.viewed:
                entry.viewed = True
                entry.viewed_at = datetime.utcnow()
                entry.viewed_by_id = current_user.id
                db.session.commit()
                flash('Dato segnato come visto', 'success')
            return redirect(url_for('modulo1_list'))
        
        form.entry_id.data = entry.id
        photos = Modulo1Photo.query.filter_by(entry_id=entry.id).all()
        
        return render_template('modulo1/view.html', title=f'Visualizza Dato - Modulo 1',
                            entry=entry, form=form, photos=photos)


# ======================================================
# Rotte per Modulo 2: Analisi fatturato clienti (solo admin)
# ======================================================

    @app.route('/modulo2')
    @login_required
    @admin_required
    def modulo2_index():
        """Pagina principale Modulo 2 (admin)"""
        return render_template('modulo2/index.html', title='Analisi Fatturato Clienti')


    @app.route('/modulo2/upload', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def modulo2_upload():
        """Upload excel fatturato clienti (admin)"""
        form = ExcelUploadForm()
        if form.validate_on_submit():
            file = form.excel_file.data
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_EXCEL_FOLDER'], filename)
            file.save(filepath)
            
            # Processa il file Excel
            success, message = process_fatturato_excel(filepath)
            
            if success:
                flash(f'File caricato con successo: {message}', 'success')
                return redirect(url_for('modulo2_index'))
            else:
                flash(f'Errore nel caricamento: {message}', 'danger')
        
        return render_template('modulo2/upload.html', title='Carica Excel Fatturato', form=form)


    @app.route('/modulo2/clienti')
    @login_required
    @admin_required
    def modulo2_clienti():
        """Gestione clienti (admin)"""
        page = request.args.get('page', 1, type=int)
        clienti = Cliente.query.order_by(Cliente.nome).paginate(
            page=page, per_page=10, error_out=False)
        
        return render_template('modulo2/clienti.html', title='Gestione Clienti', clienti=clienti)


    @app.route('/modulo2/cliente/add', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def modulo2_cliente_add():
        """Aggiunta cliente (admin)"""
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
            return redirect(url_for('modulo2_clienti'))
        
        return render_template('modulo2/cliente_form.html', title='Aggiungi Cliente', form=form)


    @app.route('/modulo2/cliente/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def modulo2_cliente_edit(id):
        """Modifica cliente (admin)"""
        cliente = Cliente.query.get_or_404(id)
        form = ClienteForm()
        
        if form.validate_on_submit():
            cliente.nome = form.nome.data
            cliente.codice = form.codice.data
            cliente.email = form.email.data
            cliente.telefono = form.telefono.data
            cliente.indirizzo = form.indirizzo.data
            
            db.session.commit()
            flash(f'Cliente {cliente.nome} aggiornato con successo', 'success')
            return redirect(url_for('modulo2_clienti'))
        
        # Pre-popola il form
        if request.method == 'GET':
            form.nome.data = cliente.nome
            form.codice.data = cliente.codice
            form.email.data = cliente.email
            form.telefono.data = cliente.telefono
            form.indirizzo.data = cliente.indirizzo
        
        return render_template('modulo2/cliente_form.html', title='Modifica Cliente', form=form)


    @app.route('/modulo2/fatturato/trend')
    @login_required
    @admin_required
    def modulo2_fatturato_trend():
        """Visualizzazione trend fatturato nel tempo (admin)"""
        form = DateRangeForm()
        
        # Applica filtri se presenti
        start_date = form.start_date.data if form.validate() and form.start_date.data else None
        end_date = form.end_date.data if form.validate() and form.end_date.data else None
        
        # Recupera dati dal DB
        query = db.session.query(
            Fatturato.data,
            db.func.sum(Fatturato.importo).label('total')
        ).group_by(Fatturato.data).order_by(Fatturato.data)
        
        if start_date:
            query = query.filter(Fatturato.data >= start_date)
        if end_date:
            query = query.filter(Fatturato.data <= end_date)
        
        results = query.all()
        
        # Prepara dati per il grafico
        chart_data = {
            'date': [r.data.strftime('%Y-%m-%d') for r in results],
            'amounts': [float(r.total) for r in results]
        }
        
        chart_url = generate_fatturato_chart(chart_data)
        
        return render_template('modulo2/fatturato_trend.html', title='Andamento Fatturato',
                              form=form, chart_url=chart_url)


    @app.route('/modulo2/fatturato/cliente/<int:cliente_id>')
    @login_required
    @admin_required
    def modulo2_fatturato_cliente(cliente_id):
        """Analisi fatturato per singolo cliente (admin)"""
        cliente = Cliente.query.get_or_404(cliente_id)
        form = DateRangeForm()
        
        # Applica filtri se presenti
        start_date = form.start_date.data if form.validate() and form.start_date.data else None
        end_date = form.end_date.data if form.validate() and form.end_date.data else None
        
        # Recupera dati dal DB
        query = Fatturato.query.filter_by(cliente_id=cliente.id)
        
        if start_date:
            query = query.filter(Fatturato.data >= start_date)
        if end_date:
            query = query.filter(Fatturato.data <= end_date)
        
        fatturati = query.order_by(Fatturato.data.desc()).all()
        
        # Calcola totale
        totale = sum(f.importo for f in fatturati)
        
        return render_template('modulo2/fatturato_cliente.html', title=f'Fatturato - {cliente.nome}',
                              cliente=cliente, fatturati=fatturati, totale=totale, form=form)

# ======================================================
# Rotte per Modulo 3: Analisi spese fornitori (solo admin)
# ======================================================

    @app.route('/modulo3')
    @login_required
    @admin_required
    def modulo3_index():
        """Pagina principale Modulo 3 (admin)"""
        return render_template('modulo3/index.html', title='Analisi Spese Fornitori')


    @app.route('/modulo3/upload', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def modulo3_upload():
        """Upload excel spese fornitori (admin)"""
        form = ExcelUploadForm()
        if form.validate_on_submit():
            file = form.excel_file.data
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_EXCEL_FOLDER'], filename)
            file.save(filepath)
            
            # Processa il file Excel
            success, message = process_spese_excel(filepath)
            
            if success:
                flash(f'File caricato con successo: {message}', 'success')
                return redirect(url_for('modulo3_index'))
            else:
                flash(f'Errore nel caricamento: {message}', 'danger')
        
        return render_template('modulo3/upload.html', title='Carica Excel Spese', form=form)


    @app.route('/modulo3/fornitori')
    @login_required
    @admin_required
    def modulo3_fornitori():
        """Gestione fornitori (admin)"""
        page = request.args.get('page', 1, type=int)
        fornitori = Fornitore.query.order_by(Fornitore.nome).paginate(
            page=page, per_page=10, error_out=False)
        
        return render_template('modulo3/fornitori.html', title='Gestione Fornitori', fornitori=fornitori)


    @app.route('/modulo3/fornitore/add', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def modulo3_fornitore_add():
        """Aggiunta fornitore (admin)"""
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
            return redirect(url_for('modulo3_fornitori'))
        
        return render_template('modulo3/fornitore_form.html', title='Aggiungi Fornitore', form=form)


    @app.route('/modulo3/fornitore/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def modulo3_fornitore_edit(id):
        """Modifica fornitore (admin)"""
        fornitore = Fornitore.query.get_or_404(id)
        form = FornitoreForm()
        
        if form.validate_on_submit():
            fornitore.nome = form.nome.data
            fornitore.codice = form.codice.data
            fornitore.email = form.email.data
            fornitore.telefono = form.telefono.data
            fornitore.indirizzo = form.indirizzo.data
            
            db.session.commit()
            flash(f'Fornitore {fornitore.nome} aggiornato con successo', 'success')
            return redirect(url_for('modulo3_fornitori'))
        
        # Pre-popola il form
        if request.method == 'GET':
            form.nome.data = fornitore.nome
            form.codice.data = fornitore.codice
            form.email.data = fornitore.email
            form.telefono.data = fornitore.telefono
            form.indirizzo.data = fornitore.indirizzo
        
        return render_template('modulo3/fornitore_form.html', title='Modifica Fornitore', form=form)


    @app.route('/modulo3/spese/trend')
    @login_required
    @admin_required
    def modulo3_spese_trend():
        """Visualizzazione trend spese nel tempo (admin)"""
        form = DateRangeForm()
        
        # Applica filtri se presenti
        start_date = form.start_date.data if form.validate() and form.start_date.data else None
        end_date = form.end_date.data if form.validate() and form.end_date.data else None
        
        # Recupera dati dal DB
        query = db.session.query(
            Spesa.data,
            db.func.sum(Spesa.importo).label('total')
        ).group_by(Spesa.data).order_by(Spesa.data)
        
        if start_date:
            query = query.filter(Spesa.data >= start_date)
        if end_date:
            query = query.filter(Spesa.data <= end_date)
        
        results = query.all()
        
        # Prepara dati per il grafico
        chart_data = {
            'date': [r.data.strftime('%Y-%m-%d') for r in results],
            'amounts': [float(r.total) for r in results]
        }
        
        chart_url = generate_spese_chart(chart_data)
        
        return render_template('modulo3/spese_trend.html', title='Andamento Spese',
                              form=form, chart_url=chart_url)


    @app.route('/modulo3/spese/fornitore/<int:fornitore_id>')
    @login_required
    @admin_required
    def modulo3_spese_fornitore(fornitore_id):
        """Analisi spese per singolo fornitore (admin)"""
        fornitore = Fornitore.query.get_or_404(fornitore_id)
        form = DateRangeForm()
        
        # Applica filtri se presenti
        start_date = form.start_date.data if form.validate() and form.start_date.data else None
        end_date = form.end_date.data if form.validate() and form.end_date.data else None
        
        # Recupera dati dal DB
        query = Spesa.query.filter_by(fornitore_id=fornitore.id)
        
        if start_date:
            query = query.filter(Spesa.data >= start_date)
        if end_date:
            query = query.filter(Spesa.data <= end_date)
        
        spese = query.order_by(Spesa.data.desc()).all()
        
        # Calcola totale
        totale = sum(s.importo for s in spese)
        
        return render_template('modulo3/spese_fornitore.html', title=f'Spese - {fornitore.nome}',
                              fornitore=fornitore, spese=spese, totale=totale, form=form)


# ======================================================
# Rotte per Modulo 4: Generazione PDF (solo admin)
# ======================================================

    @app.route('/modulo4')
    @login_required
    @admin_required
    def modulo4_index():
        """Pagina principale Modulo 4 (admin)"""
        page = request.args.get('page', 1, type=int)
        entries = Modulo4Entry.query.order_by(Modulo4Entry.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False)
        
        return render_template('modulo4/index.html', title='Generazione PDF', entries=entries)


    @app.route('/modulo4/add', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def modulo4_add():
        """Inserimento dati e generazione PDF (admin)"""
        form = Modulo4EntryForm()
        if form.validate_on_submit():
            # Creare entry nel database
            entry = Modulo4Entry(
                titolo=form.titolo.data,
                valore1=form.valore1.data,
                valore2=form.valore2.data,
                valore3=form.valore3.data,
                note=form.note.data,
                created_by_id=current_user.id
            )
            db.session.add(entry)
            db.session.flush()  # Per ottenere l'ID
            
            # Genera PDF
            data = {
                'Titolo': form.titolo.data,
                'Valore 1': form.valore1.data,
                'Valore 2': form.valore2.data if form.valore2.data else 'Non specificato',
                'Valore 3': form.valore3.data if form.valore3.data else 'Non specificato',
                'Note': form.note.data if form.note.data else 'Nessuna nota',
                'Data creazione': datetime.utcnow().strftime('%d/%m/%Y %H:%M'),
                'Creato da': current_user.username
            }
            
            filename = f"modulo4_report_{entry.id}.pdf"
            pdf_path = generate_pdf(data, filename)
            
            # Aggiorna entry con percorso PDF
            entry.pdf_path = os.path.relpath(pdf_path, app.static_folder)
            db.session.commit()
            
            flash('PDF generato con successo', 'success')
            return redirect(url_for('modulo4_view', id=entry.id))
        
        return render_template('modulo4/add.html', title='Genera Nuovo PDF', form=form)


    @app.route('/modulo4/view/<int:id>')
    @login_required
    @admin_required
    def modulo4_view(id):
        """Visualizzazione e download PDF generato (admin)"""
        entry = Modulo4Entry.query.get_or_404(id)
        
        return render_template('modulo4/view.html', title=f'Visualizza PDF - {entry.titolo}',
                              entry=entry)


    @app.route('/modulo4/download/<int:id>')
    @login_required
    @admin_required
    def modulo4_download(id):
        """Download PDF generato (admin)"""
        entry = Modulo4Entry.query.get_or_404(id)
        
        if not entry.pdf_path:
            flash('PDF non disponibile', 'danger')
            return redirect(url_for('modulo4_index'))
        
        pdf_path = os.path.join(app.static_folder, entry.pdf_path)
        return send_file(pdf_path, as_attachment=True, download_name=f"Report_{entry.titolo}.pdf")

# ======================================================
# Rotte per Modulo 5: Inserimento dati con foto (simile al Modulo 1)
# ======================================================

    @app.route('/modulo5')
    @login_required
    def modulo5_index():
        """Pagina principale Modulo 5"""
        # Operatori vedono form inserimento, admin vedono riepilogo
        if current_user.is_admin():
            return redirect(url_for('modulo5_list'))
        else:
            return redirect(url_for('modulo5_add'))


    @app.route('/modulo5/add', methods=['GET', 'POST'])
    @login_required
    def modulo5_add():
        """Aggiunta dati Modulo 5 (operatore)"""
        form = Modulo5EntryForm()
        if form.validate_on_submit():
            # Salva i dati principali
            entry = Modulo5Entry(
                valore_numerico=form.valore_numerico.data,
                note=form.note.data,
                user_id=current_user.id
            )
            db.session.add(entry)
            db.session.flush()  # Per ottenere l'ID dell'entry
            
            # Salva le foto se presenti
            photos = request.files.getlist('photos')
            if photos and photos[0].filename:
                for photo in photos:
                    filename = secure_filename(photo.filename)
                    # Crea percorso univoco
                    photo_path = os.path.join(app.config['UPLOAD_IMAGES_FOLDER'], f"modulo5_{entry.id}_{filename}")
                    photo.save(photo_path)
                    
                    # Salva riferimento nel DB
                    photo_db = Modulo5Photo(
                        filename=filename,
                        path=os.path.relpath(photo_path, app.static_folder),
                        description=f"Foto allegata a modulo 5, entry {entry.id}",
                        entry_id=entry.id
                    )
                    db.session.add(photo_db)
            
            db.session.commit()
            flash('Dati inseriti con successo', 'success')
            return redirect(url_for('modulo5_add'))
        
        return render_template('modulo5/add.html', title='Inserisci Dati - Modulo 5', form=form)


    @app.route('/modulo5/list')
    @login_required
    @admin_required
    def modulo5_list():
        """Elenco dati Modulo 5 (admin)"""
        page = request.args.get('page', 1, type=int)
        entries = Modulo5Entry.query.order_by(Modulo5Entry.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False)
        
        return render_template('modulo5/list.html', title='Elenco Dati - Modulo 5', entries=entries)


    @app.route('/modulo5/view/<int:id>', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def modulo5_view(id):
        """Visualizzazione singolo dato Modulo 5 (admin)"""
        entry = Modulo5Entry.query.get_or_404(id)
        form = Modulo5ViewForm()
        
        if form.validate_on_submit():
            if form.mark_viewed.data and not entry.viewed:
                entry.viewed = True
                entry.viewed_at = datetime.utcnow()
                entry.viewed_by_id = current_user.id
                db.session.commit()
                flash('Dato segnato come visto', 'success')
            return redirect(url_for('modulo5_list'))
        
        form.entry_id.data = entry.id
        photos = Modulo5Photo.query.filter_by(entry_id=entry.id).all()
        
        return render_template('modulo5/view.html', title=f'Visualizza Dato - Modulo 5',
                              entry=entry, form=form, photos=photos)


# ======================================================
# Rotte per Modulo 6: Inserimento dati con riepilogo (solo admin)
# ======================================================

    @app.route('/modulo6')
    @login_required
    @admin_required
    def modulo6_index():
        """Pagina principale Modulo 6 (admin)"""
        page = request.args.get('page', 1, type=int)
        entries = Modulo6Entry.query.order_by(Modulo6Entry.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False)
        
        return render_template('modulo6/index.html', title='Modulo 6 - Riepilogo', entries=entries)


    @app.route('/modulo6/add', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def modulo6_add():
        """Aggiunta dati Modulo 6 (admin)"""
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
            return redirect(url_for('modulo6_view', id=entry.id))
        
        return render_template('modulo6/add.html', title='Inserisci Dati - Modulo 6', form=form)


    @app.route('/modulo6/view/<int:id>', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def modulo6_view(id):
        """Visualizzazione singolo dato Modulo 6 (admin)"""
        entry = Modulo6Entry.query.get_or_404(id)
        form = Modulo6ViewForm()
        
        if form.validate_on_submit():
            if form.mark_viewed.data and not entry.viewed:
                entry.viewed = True
                entry.viewed_at = datetime.utcnow()
                db.session.commit()
                flash('Dato segnato come visto', 'success')
            return redirect(url_for('modulo6_index'))
        
        form.entry_id.data = entry.id
        
        return render_template('modulo6/view.html', title=f'Visualizza Dato - Modulo 6',
                              entry=entry, form=form)


# ======================================================
# Rotte per Modulo 7: Inserimento dati con riepilogo (solo admin)
# ======================================================

    @app.route('/modulo7')
    @login_required
    @admin_required
    def modulo7_index():
        """Pagina principale Modulo 7 (admin)"""
        page = request.args.get('page', 1, type=int)
        entries = Modulo7Entry.query.order_by(Modulo7Entry.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False)
        
        return render_template('modulo7/index.html', title='Modulo 7 - Riepilogo', entries=entries)


    @app.route('/modulo7/add', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def modulo7_add():
        """Aggiunta dati Modulo 7 (admin)"""
        form = Modulo7EntryForm()
        if form.validate_on_submit():
            entry = Modulo7Entry(
                valore1=form.valore1.data,
                valore2=form.valore2.data,
                valore3=form.valore3.data,
                note=form.note.data,
                created_by_id=current_user.id
            )
            db.session.add(entry)
            db.session.commit()
            flash('Dati inseriti con successo', 'success')
            return redirect(url_for('modulo7_view', id=entry.id))
        
        return render_template('modulo7/add.html', title='Inserisci Dati - Modulo 7', form=form)


    @app.route('/modulo7/view/<int:id>', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def modulo7_view(id):
        """Visualizzazione singolo dato Modulo 7 (admin)"""
        entry = Modulo7Entry.query.get_or_404(id)
        form = Modulo7ViewForm()
        
        if form.validate_on_submit():
            if form.mark_viewed.data and not entry.viewed:
                entry.viewed = True
                entry.viewed_at = datetime.utcnow()
                db.session.commit()
                flash('Dato segnato come visto', 'success')
            return redirect(url_for('modulo7_index'))
        
        form.entry_id.data = entry.id
        
        return render_template('modulo7/view.html', title=f'Visualizza Dato - Modulo 7',
                              entry=entry, form=form)


# ======================================================
# Rotte per Modulo 8: Gestione dipendenti e competenze (solo admin)
# ======================================================

    @app.route('/modulo8')
    @login_required
    @admin_required
    def modulo8_index():
        """Pagina principale Modulo 8 (admin)"""
        return render_template('modulo8/index.html', title='Gestione Dipendenti e Competenze')


    # --- Gestione Dipendenti ---

    @app.route('/modulo8/dipendenti')
    @login_required
    @admin_required
    def modulo8_dipendenti():
        """Elenco dipendenti (admin)"""
        page = request.args.get('page', 1, type=int)
        dipendenti = Dipendente.query.order_by(Dipendente.cognome, Dipendente.nome).paginate(
            page=page, per_page=10, error_out=False)
        
        return render_template('modulo8/dipendenti.html', title='Elenco Dipendenti', dipendenti=dipendenti)


    @app.route('/modulo8/dipendente/add', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def modulo8_dipendente_add():
        """Aggiunta dipendente (admin)"""
        form = DipendenteForm()
        if form.validate_on_submit():
            dipendente = Dipendente(
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
            
            # Aggiungi competenze selezionate
            if form.competenze.data:
                for comp_id in form.competenze.data:
                    competenza = Competenza.query.get(comp_id)
                    if competenza:
                        dipendente.competenze.append(competenza)
            
            db.session.add(dipendente)
            db.session.commit()
            flash(f'Dipendente {form.nome.data} {form.cognome.data} aggiunto con successo', 'success')
            return redirect(url_for('modulo8_dipendenti'))
        
        return render_template('modulo8/dipendente_form.html', title='Aggiungi Dipendente', form=form)


    @app.route('/modulo8/dipendente/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def modulo8_dipendente_edit(id):
        """Modifica dipendente (admin)"""
        dipendente = Dipendente.query.get_or_404(id)
        form = DipendenteForm()
        
        if form.validate_on_submit():
            dipendente.nome = form.nome.data
            dipendente.cognome = form.cognome.data
            dipendente.email = form.email.data
            dipendente.telefono = form.telefono.data
            dipendente.data_assunzione = form.data_assunzione.data
            dipendente.reparto = form.reparto.data
            dipendente.ruolo = form.ruolo.data
            dipendente.note = form.note.data
            
            # Aggiorna competenze
            dipendente.competenze = []
            if form.competenze.data:
                for comp_id in form.competenze.data:
                    competenza = Competenza.query.get(comp_id)
                    if competenza:
                        dipendente.competenze.append(competenza)
            
            db.session.commit()
            flash(f'Dipendente {dipendente.nome} {dipendente.cognome} aggiornato con successo', 'success')
            return redirect(url_for('modulo8_dipendenti'))
        
        # Pre-popola il form
        if request.method == 'GET':
            form.nome.data = dipendente.nome
            form.cognome.data = dipendente.cognome
            form.email.data = dipendente.email
            form.telefono.data = dipendente.telefono
            form.data_assunzione.data = dipendente.data_assunzione
            form.reparto.data = dipendente.reparto
            form.ruolo.data = dipendente.ruolo
            form.note.data = dipendente.note
            form.competenze.data = [c.id for c in dipendente.competenze]
        
        return render_template('modulo8/dipendente_form.html', title='Modifica Dipendente', form=form)


    @app.route('/modulo8/dipendente/view/<int:id>')
    @login_required
    @admin_required
    def modulo8_dipendente_view(id):
        """Visualizzazione dettagli dipendente (admin)"""
        dipendente = Dipendente.query.get_or_404(id)
        
        return render_template('modulo8/dipendente_view.html', 
                              title=f'Dettagli - {dipendente.nome} {dipendente.cognome}',
                              dipendente=dipendente)


    # --- Gestione Competenze ---

    @app.route('/modulo8/competenze')
    @login_required
    @admin_required
    def modulo8_competenze():
        """Elenco competenze (admin)"""
        competenze = Competenza.query.order_by(Competenza.nome).all()
        
        return render_template('modulo8/competenze.html', title='Elenco Competenze', competenze=competenze)


    @app.route('/modulo8/competenza/add', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def modulo8_competenza_add():
        """Aggiunta competenza (admin)"""
        form = CompetenzaForm()
        if form.validate_on_submit():
            competenza = Competenza(
                nome=form.nome.data,
                descrizione=form.descrizione.data,
                livello=form.livello.data,
                area=form.area.data,
                created_by_id=current_user.id
            )
            db.session.add(competenza)
            db.session.commit()
            flash(f'Competenza {form.nome.data} aggiunta con successo', 'success')
            return redirect(url_for('modulo8_competenze'))
        
        return render_template('modulo8/competenza_form.html', title='Aggiungi Competenza', form=form)


    @app.route('/modulo8/competenza/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def modulo8_competenza_edit(id):
        """Modifica competenza (admin)"""
        competenza = Competenza.query.get_or_404(id)
        form = CompetenzaForm()
        
        if form.validate_on_submit():
            competenza.nome = form.nome.data
            competenza.descrizione = form.descrizione.data
            competenza.livello = form.livello.data
            competenza.area = form.area.data
            
            db.session.commit()
            flash(f'Competenza {competenza.nome} aggiornata con successo', 'success')
            return redirect(url_for('modulo8_competenze'))
        
        # Pre-popola il form
        if request.method == 'GET':
            form.nome.data = competenza.nome
            form.descrizione.data = competenza.descrizione
            form.livello.data = competenza.livello
            form.area.data = competenza.area
        
        return render_template('modulo8/competenza_form.html', title='Modifica Competenza', form=form)


    @app.route('/modulo8/competenza/view/<int:id>')
    @login_required
    @admin_required
    def modulo8_competenza_view(id):
        """Visualizzazione dipendenti con competenza specifica (admin)"""
        competenza = Competenza.query.get_or_404(id)
        dipendenti = competenza.dipendenti.all()
        
        return render_template('modulo8/competenza_view.html', 
                              title=f'Dipendenti con competenza: {competenza.nome}',
                              competenza=competenza, dipendenti=dipendenti)


    @app.route('/modulo8/assegna-competenze', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def modulo8_assegna_competenze():
        """Assegnazione competenze a dipendenti (admin)"""
        form = AssegnaCompetenzaForm()
        if form.validate_on_submit():
            dipendente = Dipendente.query.get(form.dipendente_id.data)
            if not dipendente:
                flash('Dipendente non trovato', 'danger')
                return redirect(url_for('modulo8_assegna_competenze'))
            
            # Aggiorna competenze
            dipendente.competenze = []
            for comp_id in form.competenze.data:
                competenza = Competenza.query.get(comp_id)
                if competenza:
                    dipendente.competenze.append(competenza)
            
            db.session.commit()
            flash(f'Competenze aggiornate per {dipendente.nome} {dipendente.cognome}', 'success')
            return redirect(url_for('modulo8_dipendente_view', id=dipendente.id))
        
        return render_template('modulo8/assegna_competenze.html', title='Assegna Competenze', form=form)


# ======================================================
# Rotte per Modulo 9: Analisi dati da Excel (solo admin)
# ======================================================

    @app.route('/modulo9')
    @login_required
    @admin_required
    def modulo9_index():
        """Pagina principale Modulo 9 (admin)"""
        page = request.args.get('page', 1, type=int)
        excel_files = DatiExcel.query.order_by(DatiExcel.uploaded_at.desc()).paginate(
            page=page, per_page=10, error_out=False)
        
        return render_template('modulo9/index.html', title='Analisi Dati Excel', excel_files=excel_files)


    @app.route('/modulo9/upload', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def modulo9_upload():
        """Upload Excel per analisi dati (admin)"""
        form = Modulo9ExcelUploadForm()
        if form.validate_on_submit():
            file = form.excel_file.data
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_EXCEL_FOLDER'], f"modulo9_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}")
            file.save(filepath)
            
            # Registra il file nel database
            excel_db = DatiExcel(
                nome_file=filename,
                descrizione=form.descrizione.data,
                uploaded_by_id=current_user.id
            )
            db.session.add(excel_db)
            db.session.flush()  # Per ottenere l'ID
            
            # Processa il file Excel
            success, message = process_modulo9_excel(filepath, excel_db.id)
            
            if success:
                db.session.commit()
                flash(f'File caricato con successo: {message}', 'success')
                return redirect(url_for('modulo9_analyze', id=excel_db.id))
            else:
                db.session.rollback()
                flash(f'Errore nel caricamento: {message}', 'danger')
        
        return render_template('modulo9/upload.html', title='Carica Excel per Analisi', form=form)


    @app.route('/modulo9/analyze/<int:id>')
    @login_required
    @admin_required
    def modulo9_analyze(id):
        """Analisi dati Excel caricato (admin)"""
        excel_file = DatiExcel.query.get_or_404(id)
        
        # Recupera i record
        records = RecordExcel.query.filter_by(dati_excel_id=excel_file.id).all()
        
        # Estrai colonne uniche per l'analisi
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
        
        return render_template('modulo9/analyze.html', 
                              title=f'Analisi Excel - {excel_file.nome_file}',
                              excel_file=excel_file, records=records, columns=columns)


    @app.route('/modulo9/chart/<int:id>/<string:column>')
    @login_required
    @admin_required
    def modulo9_chart(id, column):
        """Genera grafico per una colonna specifica (admin)"""
        excel_file = DatiExcel.query.get_or_404(id)
        
        # Verifica che la colonna esista
        if not hasattr(RecordExcel, column):
            flash('Colonna non valida', 'danger')
            return redirect(url_for('modulo9_analyze', id=id))
        
        # Recupera i dati per il grafico
        if column in ['colonna3', 'colonna4']:  # Colonne numeriche
            data = db.session.query(
                getattr(RecordExcel, column)
            ).filter_by(dati_excel_id=excel_file.id).all()
            
            values = [float(d[0]) for d in data if d[0] is not None]
            
            # Crea grafico a barre
            plt.figure(figsize=(10, 6))
            plt.hist(values, bins=10)
            plt.title(f'Distribuzione {column}')
            plt.xlabel('Valore')
            plt.ylabel('Frequenza')
            plt.grid(True)
            
            # Salva il grafico in memoria
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            
            # Converti in base64 per visualizzazione HTML
            chart_url = base64.b64encode(img.getvalue()).decode()
            plt.close()
            
            return render_template('modulo9/chart.html', 
                                  title=f'Grafico {column} - {excel_file.nome_file}',
                                  chart_url=f'data:image/png;base64,{chart_url}',
                                  column=column, excel_file=excel_file)
        else:
            flash('Tipo di colonna non supportato per grafici', 'warning')
            return redirect(url_for('modulo9_analyze', id=id))


    # ======================================================
    # Rotte per gestione file e immagini
    # ======================================================

    @app.route('/uploads/<path:filename>')
    @login_required
    def uploaded_file(filename):
        """Accesso ai file caricati (controlla autorizzazioni)"""
        # Verifica autorizzazione in base al tipo di file
        if 'modulo1_' in filename or 'modulo5_' in filename:
            # Solo admin o l'utente che ha caricato il file
            photo_id = filename.split('_')[1]  # Estrai ID dalla convenzione di nome
            if current_user.is_admin():
                return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            else:
                # Verifica se l'utente è il proprietario
                if 'modulo1_' in filename:
                    entry = Modulo1Entry.query.get(photo_id)
                else:
                    entry = Modulo5Entry.query.get(photo_id)
                
                if entry and entry.user_id == current_user.id:
                    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                else:
                    abort(403)  # Forbidden
        elif current_user.is_admin():
            # Altri file solo per admin
            return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            abort(403)  # Forbidden


    # ======================================================
    # Gestione errori
    # ======================================================

    @app.errorhandler(404)
    def not_found_error(error):
        """Gestione errore 404"""
        return render_template('errors/404.html', title='Pagina non trovata'), 404


    @app.errorhandler(403)
    def forbidden_error(error):
        """Gestione errore 403"""
        return render_template('errors/403.html', title='Accesso negato'), 403


    @app.errorhandler(500)
    def internal_error(error):
        """Gestione errore 500"""
        db.session.rollback()  # In caso di errore DB
        return render_template('errors/500.html', title='Errore interno'), 500