from app import db
from app.models import Dipendente, dipendente_competenza
from sqlalchemy import text

def recreate_dipendente_table():
    # Backup dei dati esistenti
    existing_dipendenti = []
    try:
        existing_dipendenti = [(d.nome, d.cognome, d.email, d.telefono, 
                              d.data_assunzione, d.reparto, d.ruolo, 
                              d.note, d.created_at, d.created_by_id) 
                             for d in Dipendente.query.all()]
    except:
        pass

    # Drop existing indexes first
    try:
        db.session.execute(text('DROP INDEX IF EXISTS ix_dipendente_email'))
    except:
        pass

    # Elimina le tabelle nell'ordine corretto
    db.session.execute(text('DROP TABLE IF EXISTS dipendente_competenza'))
    db.session.execute(text('DROP TABLE IF EXISTS dipendente'))
    
    # Ricrea le tabelle senza vincoli di unicità
    db.session.execute(text('''
    CREATE TABLE dipendente (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        nome VARCHAR(64) NOT NULL,
        cognome VARCHAR(64) NOT NULL,
        email VARCHAR(120) NULL,
        telefono VARCHAR(20) NULL,
        data_assunzione DATETIME NULL,
        reparto VARCHAR(64) NULL,
        ruolo VARCHAR(64) NULL,
        note TEXT NULL,
        created_at DATETIME NULL,
        created_by_id INTEGER NULL REFERENCES users(id)
    )
    '''))
    
    db.session.execute(text('''
    CREATE TABLE dipendente_competenza (
        dipendente_id INTEGER NOT NULL,
        competenza_id INTEGER NOT NULL,
        PRIMARY KEY (dipendente_id, competenza_id),
        FOREIGN KEY(dipendente_id) REFERENCES dipendente (id),
        FOREIGN KEY(competenza_id) REFERENCES competenza (id)
    )
    '''))
    
    # Reinserisce i dati
    for d in existing_dipendenti:
        db.session.execute(
            text('''INSERT INTO dipendente 
               (nome, cognome, email, telefono, data_assunzione, 
                reparto, ruolo, note, created_at, created_by_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''),
            d
        )
    
    db.session.commit()

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        recreate_dipendente_table() 