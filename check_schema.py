from app import create_app, db
from sqlalchemy import inspect

app = create_app()

with app.app_context():
    inspector = inspect(db.engine)
    print("Table: dipendente")
    print("Columns:")
    for column in inspector.get_columns('dipendente'):
        print(f"- {column['name']}: {column['type']} (nullable: {column['nullable']})")
    print("\nUnique Constraints:")
    for constraint in inspector.get_unique_constraints('dipendente'):
        print(f"- {constraint}") 