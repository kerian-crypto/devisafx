from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, FloatField, TextAreaField, SubmitField,DateField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange, Optional
import re

class FormulaireInscription(FlaskForm):
    nom = StringField('Nom complet', validators=[
        DataRequired(message='Le nom est requis'),
        Length(min=3, max=100)
    ])
    telephone = StringField('Numéro de téléphone', validators=[
        DataRequired(message='Le numéro de téléphone est requis'),
        Length(min=9, max=15)
    ])
    email = StringField('Email', validators=[
        DataRequired(message='L\'email est requis'),
        Email(message='Email invalide')
    ])
    pays = SelectField('Pays', choices=[
        ('CM', 'Cameroun'),
        ('TG', 'Togo'),
        ('GA', 'Gabon'),
        ('CF', 'République Centrafricaine'),
        ('CD', 'RD Congo')
    ], validators=[DataRequired()])
    mot_de_passe = PasswordField('Mot de passe', validators=[
        DataRequired(message='Le mot de passe est requis'),
        Length(min=8, message='Minimum 8 caractères'),
        EqualTo('confirmation_mot_de_passe', message='Les mots de passe doivent correspondre')
    ])
    confirmation_mot_de_passe = PasswordField('Confirmer le mot de passe')
    soumettre = SubmitField('S\'inscrire')
    
    def validate_telephone(self, field):
        if not re.match(r'^\+?[\d\s\-\(\)]+$', field.data):
            raise ValidationError('Numéro de téléphone invalide')

class FormulaireConnexion(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='L\'email est requis'),
        Email(message='Email invalide')
    ])
    mot_de_passe = PasswordField('Mot de passe', validators=[
        DataRequired(message='Le mot de passe est requis')
    ])
    soumettre = SubmitField('Se connecter')

class FormulaireAchat(FlaskForm):
    montant_xaf = FloatField('Montant en XAF', validators=[
        DataRequired(message='Le montant est requis'),
        NumberRange(min=5000, max=500000, message='Montant entre 5,000 et 500,000 XAF')
    ])
    adresse_wallet = StringField('Adresse de votre wallet USDT', validators=[
        DataRequired(message='L\'adresse du wallet est requise'),
        Length(min=20, max=200)
    ])
    reseau = SelectField('Réseau', choices=[
        ('TRC20', 'TRC20 (Tron)'),
        ('USDT_TON', 'USDT_TON (Toncoin)'),
        ('USDT_APTOS', 'USDT_APTOS (Aptos)'),
        ('ETHEREUM', 'Ethereum'),
        ('SOL', 'Solana')
    ], validators=[DataRequired()])
    operateur_mobile = SelectField('Opérateur mobile', choices=[
        ('MTN', 'MTN'),
        ('ORANGE', 'Orange'),
        ('MOOV', 'Moov'),
        ('TOGOCEL', 'Togocel')
    ], validators=[DataRequired()])
    soumettre = SubmitField('Confirmer l\'achat')

class FormulaireVente(FlaskForm):
    montant_usdt = FloatField('Montant en USDT', validators=[
        DataRequired(message='Le montant est requis'),
        NumberRange(min=1, max=1000, message='Montant entre 1 et 1000 USDT')
    ])
    reseau = SelectField('Réseau d\'envoi', choices=[
        ('TRC20', 'TRC20 (Tron)'),
        ('USDT_TON', 'USDT_TON (Toncoin)'),
        ('USDT_APTOS', 'USDT_APTOS (Aptos)'),
        ('ETHEREUM', 'Ethereum'),
        ('SOL', 'Solana')
    ], validators=[DataRequired()])
    adresse_wallet = StringField('Votre adresse wallet (pour vérification)', validators=[
        Length(max=200)
    ])
    operateur_mobile = SelectField('Opérateur de réception', choices=[
        ('MTN', 'MTN'),
        ('ORANGE', 'Orange'),
        ('MOOV', 'Moov'),
        ('TOGOCEL', 'Togocel')
    ], validators=[DataRequired()])
    numero_mobile = StringField('Numéro mobile pour recevoir les XAF', validators=[
        DataRequired(message='Le numéro mobile est requis'),
        Length(min=9, max=15)
    ])
    soumettre = SubmitField('Confirmer la vente')

class FormulaireCalculTaux(FlaskForm):
    type_calcul = SelectField('Type de calcul', choices=[
        ('vente', 'Calculer le taux de vente USDT'),
        ('achat', 'Calculer le taux d\'achat USDT')
    ], validators=[DataRequired()])
    taux_mondial = FloatField('Taux mondial du jour (XAF)', validators=[
        DataRequired(message='Le taux mondial est requis'),
        NumberRange(min=1, message='Taux invalide')
    ])
    benefice = FloatField('Bénéfice souhaité (XAF)', validators=[
        DataRequired(message='Le bénéfice est requis'),
        NumberRange(min=0, message='Bénéfice invalide')
    ])
    montant = FloatField('Montant à échanger', validators=[
        DataRequired(message='Le montant est requis'),
        NumberRange(min=1, message='Montant invalide')
    ])
    soumettre = SubmitField('Calculer')

# forms.py - Ajouter cette classe
class FormulaireTaux(FlaskForm):
    taux_achat = FloatField('Taux d\'achat USDT (XAF)', validators=[
        DataRequired(message='Le taux d\'achat est requis'),
        NumberRange(min=1, max=2000, message='Taux invalide')
    ])
    taux_vente = FloatField('Taux de vente USDT (XAF)', validators=[
        DataRequired(message='Le taux de vente est requis'),
        NumberRange(min=1, max=2000, message='Taux invalide')
    ])
    date_application = DateField('Date d\'application (optionnel)', 
                                format='%Y-%m-%d',
                                validators=[Optional()])
    soumettre = SubmitField('Mettre à jour les taux')