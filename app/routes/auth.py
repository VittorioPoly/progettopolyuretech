from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse as url_parse
from datetime import datetime

from app import db
from app.models import User
from app.forms import LoginForm, RegistrationForm, ChangePasswordForm
from app.utils import admin_required

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Username o password non validi', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)
        user.last_login = datetime.utcnow()
        db.session.commit()

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('dashboard.index')

        flash(f'Benvenuto, {user.username}!', 'success')
        return redirect(next_page)

    return render_template('auth/login.html', title='Accesso', form=form)


@auth.route('/logout')
def logout():
    logout_user()
    flash('Hai effettuato il logout correttamente', 'success')
    return redirect(url_for('auth.login'))


@auth.route('/register', methods=['GET', 'POST'])
@login_required
@admin_required
def register():
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
        return redirect(url_for('dashboard.index'))

    return render_template('auth/register.html', title='Registrazione', form=form)


@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.old_password.data):
            flash('Password attuale non corretta', 'danger')
            return redirect(url_for('auth.change_password'))

        current_user.set_password(form.password.data)
        db.session.commit()
        flash('Password aggiornata con successo', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/change_password.html', title='Cambio Password', form=form)


@auth.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', title='Profilo')
