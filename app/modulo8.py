@modulo8.route('/dipendenti/nuovo_step', methods=['GET', 'POST'])
def nuovo_dipendente_step():
    step = int(request.args.get('step', 1))
    
    if step < 1 or step > 5:
        return redirect(url_for('modulo8.dipendenti'))
    
    form_classes = [DipendenteStep1Form, DipendenteStep2Form, DipendenteStep3Form, DipendenteStep4Form, DipendenteStep5Form]
    form = form_classes[step - 1]()

    if form.validate_on_submit():
        action = request.form.get('action')
        
        if action == 'prev':
            return redirect(url_for('modulo8.nuovo_dipendente_step', step=step-1))
        elif action == 'next':
            # Salva i dati nella sessione
            session[f'step{step}_data'] = form.data
            return redirect(url_for('modulo8.nuovo_dipendente_step', step=step+1))
        elif action == 'submit':
            # Recupera tutti i dati dalla sessione
            dipendente_data = {}
            for i in range(1, 6):
                step_data = session.get(f'step{i}_data', {})
                dipendente_data.update(step_data)
            
            # Crea il nuovo dipendente
            dipendente = Dipendente(
                nome=dipendente_data.get('nome'),
                cognome=dipendente_data.get('cognome'),
                anno_nascita=dipendente_data.get('anno_nascita'),
                luogo_nascita=dipendente_data.get('luogo_nascita'),
                provincia_nascita=dipendente_data.get('provincia_nascita'),
                codice_fiscale=dipendente_data.get('codice_fiscale'),
                email=dipendente_data.get('email'),
                telefono=dipendente_data.get('telefono'),
                matricola=dipendente_data.get('matricola'),
                reparto=dipendente_data.get('reparto'),
                ruolo=dipendente_data.get('ruolo'),
                data_assunzione_somministrazione=dipendente_data.get('data_assunzione_somministrazione'),
                agenzia_somministrazione=dipendente_data.get('agenzia_somministrazione'),
                data_assunzione_indeterminato=dipendente_data.get('data_assunzione_indeterminato'),
                legge_104=dipendente_data.get('legge_104'),
                donatore_avis=dipendente_data.get('donatore_avis'),
                indirizzo_residenza=dipendente_data.get('indirizzo_residenza'),
                citta_residenza=dipendente_data.get('citta_residenza'),
                provincia_residenza=dipendente_data.get('provincia_residenza'),
                cap_residenza=dipendente_data.get('cap_residenza')
            )
            
            db.session.add(dipendente)
            db.session.commit()
            
            # Aggiungi le competenze
            for competenza_id in dipendente_data.get('competenze', []):
                dipendente_competenza = DipendenteCompetenza(
                    dipendente_id=dipendente.id,
                    competenza_id=competenza_id
                )
                db.session.add(dipendente_competenza)
            
            # Aggiungi il vestiario
            for vestiario_id in dipendente_data.get('vestiario', []):
                prelievo = PrelievoVestiario(
                    dipendente_id=dipendente.id,
                    vestiario_id=vestiario_id,
                    data_prelievo=datetime.now()
                )
                db.session.add(prelievo)
            
            db.session.commit()
            
            # Pulisci la sessione
            for i in range(1, 6):
                session.pop(f'step{i}_data', None)
            
            flash('Dipendente aggiunto con successo!', 'success')
            return redirect(url_for('modulo8.dipendenti'))
    
    # Precompila il form con i dati della sessione se presenti
    if request.method == 'GET':
        step_data = session.get(f'step{step}_data', {})
        for field in form:
            if field.name in step_data:
                field.data = step_data[field.name]
    
    return render_template('modulo8/dipendenti/nuovo_step.html', form=form, step=step)

@bp.route('/formazione')
@login_required
def formazione():
    courses = TrainingCourse.query.order_by(TrainingCourse.date.desc()).all()
    return render_template('modulo8/formazione/courses.html', courses=courses)

@bp.route('/formazione/nuovo', methods=['GET', 'POST'])
@login_required
def nuovo_corso():
    form = TrainingCourseForm()
    form.employees.choices = [(e.id, f"{e.nome} {e.cognome}") for e in Employee.query.all()]
    
    if form.validate_on_submit():
        course = TrainingCourse(
            name=form.name.data,
            description=form.description.data,
            date=form.date.data
        )
        db.session.add(course)
        
        for employee_id in form.employees.data:
            completion = CourseCompletion(
                course=course,
                employee_id=employee_id
            )
            db.session.add(completion)
        
        db.session.commit()
        flash('Corso creato con successo!', 'success')
        return redirect(url_for('modulo8.formazione'))
    
    return render_template('modulo8/formazione/course_form.html', form=form, title='Nuovo Corso')

@bp.route('/formazione/<int:id>')
@login_required
def dettaglio_corso(id):
    course = TrainingCourse.query.get_or_404(id)
    return render_template('modulo8/formazione/course_detail.html', course=course)

@bp.route('/formazione/completati')
@login_required
def corsi_completati():
    completions = CourseCompletion.query.filter_by(status='completed').all()
    return render_template('modulo8/formazione/completed_courses.html', completions=completions)

@bp.route('/formazione/da-svolgere')
@login_required
def corsi_da_svolgere():
    completions = CourseCompletion.query.filter_by(status='pending').all()
    return render_template('modulo8/formazione/pending_courses.html', completions=completions)

@bp.route('/formazione/completamento/<int:id>', methods=['GET', 'POST'])
@login_required
def aggiorna_completamento(id):
    completion = CourseCompletion.query.get_or_404(id)
    form = CourseCompletionForm()
    
    if form.validate_on_submit():
        completion.status = form.status.data
        if form.status.data == 'completed':
            completion.completed_at = datetime.utcnow()
        db.session.commit()
        flash('Stato del corso aggiornato con successo!', 'success')
        return redirect(url_for('modulo8.dettaglio_corso', id=completion.course_id))
    
    form.status.data = completion.status
    return render_template('modulo8/formazione/update_completion.html', form=form, completion=completion) 