from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
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
migrate = Migrate(app, db)

    
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'main.login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'warning'
    


    
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
    

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)










