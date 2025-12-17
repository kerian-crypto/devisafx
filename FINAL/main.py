from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
import os
import hashlib

from config import Config
from models import db, Utilisateur
from routes import main_bp, admin_bp
from auth import auth_bp


"""Factory pour créer l'application Flask"""
app = Flask(__name__)
app.config.from_object(Config)
    
# Initialiser les extensions
db.init_app(app)
    
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'main.login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'warning'
    

migrate = Migrate(app, db)
    
@login_manager.user_loader
def load_user(user_id):
    return Utilisateur.query.get(int(user_id))
    
# Enregistrer les blueprints
app.register_blueprint(main_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)

@app.route('/health-check')
def health_check():
    return 'OK', 200
    
        
    # Créer un admin par défaut si aucun n'existe
    if not Utilisateur.query.filter_by(est_admin=True).first():
        admin = Utilisateur(
            nom=app.config['ADMIN_USERNAME'],
            telephone=app.config['ADMIN_NUMBER'],
            email=app.config['ADMIN_EMAIL'],
            pays='CM',
            mot_de_passe_hash=hashlib.sha256(app.config['ADMIN_PASSWORD'].encode()).hexdigest(),  # À changer en production
            email_verifie=True,
            est_admin=True
        )
        db.session.add(admin)
        db.session.commit()
    

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

