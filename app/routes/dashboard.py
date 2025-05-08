from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func

from app import db
from app.models import Modulo1Entry, Modulo5Entry, Fatturato, Cliente, User


dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/')
@dashboard.route('/index')
@login_required
def index():
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
        stats['modulo1_count'] = Modulo1Entry.query.count()
        stats['modulo1_unviewed'] = Modulo1Entry.query.filter_by(viewed=False).count()

        stats['modulo5_count'] = Modulo5Entry.query.count()
        stats['modulo5_unviewed'] = Modulo5Entry.query.filter_by(viewed=False).count()

        stats['fatturato_totale'] = db.session.query(func.sum(Fatturato.importo)).scalar() or 0
        stats['clienti_count'] = Cliente.query.count()

        stats['users_count'] = User.query.count()
        stats['admin_count'] = User.query.filter_by(role='admin').count()
        stats['operatori_count'] = User.query.filter_by(role='operatore').count()

    recent_activities = []  # opzionalmente da implementare

    return render_template('dashboard/index.html', title='Dashboard', stats=stats, recent_activities=recent_activities)
