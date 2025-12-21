from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Transaction, PortefeuilleAdmin, Utilisateur, TauxJournalier, Notification
from datetime import datetime

# Vos autres imports et blueprints...

@login_required
def transaction_status(transaction_id):
    """Afficher le statut d'une transaction"""
    transaction = Transaction.query.filter_by(identifiant_transaction=transaction_id).first_or_404()
    
    # Vérifier que l'utilisateur a accès à cette transaction
    if transaction.utilisateur_id != current_user.id and not current_user.est_admin:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Récupérer les informations du portefeuille admin correspondant au réseau
    portefeuille_admin = None
    numero_admin = None
    adresse_admin = None
    
    if transaction.type_transaction == 'achat':
        # Pour les achats, récupérer le numéro marchand mobile money
        portefeuille_admin = PortefeuilleAdmin.query.filter_by(
            type_portefeuille='mobile_money',
            est_actif=True
        ).first()
        if portefeuille_admin:
            numero_admin = portefeuille_admin.adresse  # Le numéro est stocké dans le champ adresse
    
    elif transaction.type_transaction == 'vente':
        # Pour les ventes, récupérer l'adresse crypto du réseau correspondant
        portefeuille_admin = PortefeuilleAdmin.query.filter_by(
            reseau=transaction.reseau,
            type_portefeuille='crypto',
            est_actif=True
        ).first()
        if portefeuille_admin:
            adresse_admin = portefeuille_admin.adresse
    
    return render_template('transaction_status.html',
                         transaction=transaction,
                         numero_admin=numero_admin,
                         adresse_admin=adresse_admin,
                         formater_montant=formater_montant)


# Route admin pour les détails de transaction
@login_required
def admin_transaction_details(transaction_id):
    """Retourner les détails d'une transaction pour l'admin"""
    if not current_user.est_admin:
        return jsonify({'success': False, 'message': 'Accès non autorisé'}), 403
    
    transaction = Transaction.query.filter_by(identifiant_transaction=transaction_id).first_or_404()
    
    # Récupérer l'adresse/numéro admin correspondant
    portefeuille_admin = None
    info_admin = None
    
    if transaction.type_transaction == 'achat':
        # Numéro marchand
        portefeuille_admin = PortefeuilleAdmin.query.filter_by(
            type_portefeuille='mobile_money',
            est_actif=True
        ).first()
        if portefeuille_admin:
            info_admin = {
                'type': 'numero_marchand',
                'label': 'Numéro marchand',
                'value': portefeuille_admin.adresse
            }
    else:
        # Adresse crypto
        portefeuille_admin = PortefeuilleAdmin.query.filter_by(
            reseau=transaction.reseau,
            type_portefeuille='crypto',
            est_actif=True
        ).first()
        if portefeuille_admin:
            info_admin = {
                'type': 'adresse_crypto',
                'label': f'Adresse {transaction.reseau}',
                'value': portefeuille_admin.adresse
            }
    
    html = render_template('admin_transaction_details.html',
                          transaction=transaction,
                          info_admin=info_admin,
                          formater_montant=formater_montant)
    
    return jsonify({'success': True, 'html': html})


def formater_montant(montant):
    """Formater un montant avec des espaces comme séparateurs de milliers"""
    return "{:,.0f}".format(montant).replace(',', ' ')
