# scripts/init_db.py
from ..app import creer_app
from ..models import db
import os

app = creer_app()

with app.app_context():
    print("Création des tables de base de données...")
    db.create_all()
    print("Tables créées avec succès!")