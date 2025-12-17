from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
import uuid

db = SQLAlchemy()

class Utilisateur(UserMixin, db.Model):
    __tablename__ = 'utilisateurs'
    
    id = db.Column(db.Integer, primary_key=True)
    identifiant_unique = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    nom = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    pays = db.Column(db.String(50), nullable=False)
    mot_de_passe_hash = db.Column(db.String(200))
    email_verifie = db.Column(db.Boolean, default=False)
    token_verification = db.Column(db.String(100))
    google_id = db.Column(db.String(100), unique=True)
    date_inscription = db.Column(db.DateTime, default=datetime.utcnow)
    est_admin = db.Column(db.Boolean, default=False)
    est_actif = db.Column(db.Boolean, default=True)
    
    transactions = db.relationship('Transaction', backref='utilisateur', lazy=True)
    notifications_envoyees = db.relationship(
        'Notification', foreign_keys='Notification.admin_id', backref='admin', lazy=True
    )
    notifications_reçues = db.relationship(
        'Notification', foreign_keys='Notification.utilisateur_id', backref='destinataire', lazy=True
    )

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    identifiant_transaction = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    type_transaction = db.Column(
        db.Enum('achat', 'vente', name='type_transaction_enum'),
        nullable=False
    )
    montant_xaf = db.Column(db.Float, nullable=False)
    montant_usdt = db.Column(db.Float, nullable=False)
    reseau = db.Column(db.String(50), nullable=False)  # TRC20, USDT_TON, etc.
    adresse_wallet = db.Column(db.String(200))
    operateur_mobile = db.Column(db.String(50))
    numero_marchand = db.Column(db.String(20))
    statut = db.Column(
        db.Enum('en_attente', 'valide', 'rejete', 'complete', name='statut_enum'),
        default='en_attente'
    )
    motif_rejet = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_validation = db.Column(db.DateTime)
    
    preuve_paiement = db.Column(db.String(200))  # Chemin vers l'image
    reference_paiement = db.Column(db.String(100))
    
    taux_applique = db.Column(db.Float)  # Taux appliqué pour la transaction

class PortefeuilleAdmin(db.Model):
    __tablename__ = 'portefeuilles_admin'
    
    id = db.Column(db.Integer, primary_key=True)
    reseau = db.Column(db.String(50), nullable=False)
    adresse = db.Column(db.String(200), nullable=False)
    pays = db.Column(db.String(50))
    type_portefeuille = db.Column(
        db.Enum('crypto', 'mobile_money', name='type_portefeuille_enum'),
        nullable=False
    )
    est_actif = db.Column(db.Boolean, default=True)
    date_ajout = db.Column(db.DateTime, default=datetime.utcnow)

class TauxJournalier(db.Model):
    __tablename__ = 'taux_journaliers'
    
    id = db.Column(db.Integer, primary_key=True)
    taux_achat = db.Column(db.Float, nullable=False)
    taux_vente = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, unique=True, default=date.today)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'))
    admin_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'))
    type_notification = db.Column(db.String(50))
    message = db.Column(db.Text, nullable=False)
    est_lue = db.Column(db.Boolean, default=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
