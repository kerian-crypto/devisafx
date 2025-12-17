from flask import Blueprint, redirect, url_for, session, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from oauthlib.oauth2 import WebApplicationClient
import json
import os
from models import db, Utilisateur
from config import Config

client = WebApplicationClient(Config.GOOGLE_CLIENT_ID)
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login/google')
def login_google():
    """Redirige vers Google pour l'authentification"""
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@auth_bp.route('/login/google/callback')
def google_callback():
    """Callback Google OAuth"""
    code = request.args.get("code")
    
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(Config.GOOGLE_CLIENT_ID, Config.GOOGLE_CLIENT_SECRET),
    )
    
    client.parse_request_body_response(json.dumps(token_response.json()))
    
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    
    if userinfo_response.json().get("email_verified"):
        google_id = userinfo_response.json()["sub"]
        email = userinfo_response.json()["email"]
        nom = userinfo_response.json().get("name", "")
        
        # Chercher ou créer l'utilisateur
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        
        if not utilisateur:
            utilisateur = Utilisateur(
                nom=nom,
                email=email,
                google_id=google_id,
                email_verifie=True,
                pays='CM'  # Pays par défaut
            )
            db.session.add(utilisateur)
            db.session.commit()
        
        login_user(utilisateur)
        flash('Connexion réussie avec Google!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Email non vérifié par Google.', 'error')
        return redirect(url_for('login'))

def get_google_provider_cfg():
    """Récupère la configuration OAuth de Google"""
    import requests
    return requests.get(Config.GOOGLE_DISCOVERY_URL).json()

@auth_bp.route('/logout')
@login_required
def logout():
    """Déconnexion"""
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('main.index'))