from sqlalchemy import text
from app import db  # adapte si ton db est ailleurs

def update_numero_marchand_length():
    with db.engine.begin() as connection:
        connection.execute(text("""
            ALTER TABLE transactions
            ALTER COLUMN numero_marchand TYPE VARCHAR(100)
        """))
