from main import app
from models import db, Utilisateur
import hashlib
import os

with app.app_context():
    if not Utilisateur.query.filter_by(est_admin=True).first():
        admin = Utilisateur(
            nom=os.environ.get("ADMIN_USERNAME"),
            telephone=os.environ.get("ADMIN_NUMBER"),
            email=os.environ.get("ADMIN_EMAIL"),
            pays="CM",
            mot_de_passe_hash=hashlib.sha256(
                os.environ.get("ADMIN_PASSWORD").encode()
            ).hexdigest(),
            email_verifie=True,
            est_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin créé")
    else:
        print("Admin existe déjà")
