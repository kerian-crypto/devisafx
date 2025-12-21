from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user, logout_user
from flask_mail import Message
from datetime import datetime, date
import uuid
import os

from models import db, Utilisateur, Transaction, PortefeuilleAdmin, TauxJournalier, Notification
from forms import FormulaireInscription, FormulaireConnexion, FormulaireAchat, FormulaireVente, FormulaireCalculTaux
from utils import calculer_taux_vente_usdt, calculer_taux_achat_usdt, generer_numero_marchand, formater_montant
from auth import auth_bp
from config import Config

main_bp = Blueprint('main', __name__)
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@main_bp.route('/')
def index():
    """Page d'accueil"""
    if current_user.is_authenticated:
        if current_user.est_admin:
            return redirect(url_for('admin.admin_dashboard'))
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Inscription"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    formulaire = FormulaireInscription()
    
    if formulaire.validate_on_submit():
        # Vérifier si l'email existe déjà
        if Utilisateur.query.filter_by(email=formulaire.email.data).first():
            flash('Cet email est déjà utilisé.', 'error')
            return redirect(url_for('register'))
        
        # Vérifier si le téléphone existe déjà
        if Utilisateur.query.filter_by(telephone=formulaire.telephone.data).first():
            flash('Ce numéro de téléphone est déjà utilisé.', 'error')
            return redirect(url_for('register'))
        
        # Créer l'utilisateur
        utilisateur = Utilisateur(
            nom=formulaire.nom.data,
            telephone=formulaire.telephone.data,
            email=formulaire.email.data,
            pays=formulaire.pays.data,
            mot_de_passe_hash=formulaire.mot_de_passe.data  # À hasher en production
        )
        
        db.session.add(utilisateur)
        db.session.commit()
        
        flash('Inscription réussie! Veuillez vous connecter.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', formulaire=formulaire)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Connexion"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    formulaire = FormulaireConnexion()
    
    if formulaire.validate_on_submit():
        utilisateur = Utilisateur.query.filter_by(email=formulaire.email.data).first()
        
        if utilisateur and utilisateur.mot_de_passe_hash == formulaire.mot_de_passe.data:
            login_user(utilisateur)
            flash('Connexion réussie!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Email ou mot de passe incorrect.', 'error')
    
    return render_template('login.html', formulaire=formulaire)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Tableau de bord utilisateur"""
    transactions = Transaction.query.filter_by(
        utilisateur_id=current_user.id
    ).order_by(Transaction.date_creation.desc()).limit(10).all()
    
    solde_usdt = sum(t.montant_usdt for t in transactions if t.statut == 'complete' and t.type_transaction == 'achat')
    solde_usdt -= sum(t.montant_usdt for t in transactions if t.statut == 'complete' and t.type_transaction == 'vente')
    
    return render_template('dashboard.html', 
                         transactions=transactions,
                         solde_usdt=round(solde_usdt, 2),
                         formater_montant=formater_montant)

@main_bp.route('/buy', methods=['GET', 'POST'])
@login_required
def buy():
    """Achat de USDT"""
    formulaire = FormulaireAchat()
    
    taux_du_jour = TauxJournalier.query.order_by(TauxJournalier.date.desc()).first()
    taux_vente = taux_du_jour.taux_vente if taux_du_jour else Config.DEFAULT_USDT_RATE
    
    if formulaire.validate_on_submit():
        # Calculer le montant en USDT
        montant_xaf = formulaire.montant_xaf.data
        taux_final = taux_vente * (1 + Config.PROFIT_MARGIN)
        montant_usdt = montant_xaf / taux_final
        
        # Sélectionner un portefeuille mobile money admin actif
        portefeuille_mobile = PortefeuilleAdmin.query.filter_by(
            type_portefeuille='mobile_money',
            pays=current_user.pays,
            est_actif=True
        ).first()
        
        if not portefeuille_mobile:
            flash("Aucun portefeuille admin disponible pour le moment", "error")
            return redirect(url_for('main.buy'))
        
        # Créer la transaction
        transaction = Transaction(
            utilisateur_id=current_user.id,
            type_transaction='achat',
            montant_xaf=montant_xaf,
            montant_usdt=round(montant_usdt, 2),
            reseau=formulaire.reseau.data,
            adresse_wallet_utilisateur=formulaire.adresse_wallet.data,
            portefeuille_admin_mobile_id=portefeuille_mobile.id,
            taux_applique=taux_final,
            statut='en_attente'
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        # Notification pour l'admin
        notification = Notification(
            admin_id=1,
            type_notification='nouvelle_transaction',
            message=f"Nouvelle transaction d'achat: {montant_xaf} XAF par {current_user.nom}"
        )
        db.session.add(notification)
        db.session.commit()
        
        return redirect(url_for('main.transaction_status', transaction_id=transaction.identifiant_transaction))
    
    return render_template('buy.html', formulaire=formulaire, taux_vente=taux_vente)

@main_bp.route('/sell', methods=['GET', 'POST'])
@login_required
def sell():
    """Vente de USDT"""
    formulaire = FormulaireVente()
    
    taux_du_jour = TauxJournalier.query.order_by(TauxJournalier.date.desc()).first()
    taux_achat = taux_du_jour.taux_achat if taux_du_jour else Config.DEFAULT_USDT_RATE
    
    if formulaire.validate_on_submit():
        # Calculer le montant en XAF
        montant_usdt = formulaire.montant_usdt.data
        taux_final = taux_achat * (1 - Config.PROFIT_MARGIN)
        montant_xaf = montant_usdt * taux_final
        
        # Sélectionner un portefeuille crypto admin actif pour ce réseau
        portefeuille_crypto = PortefeuilleAdmin.query.filter_by(
            type_portefeuille='crypto',
            reseau=formulaire.reseau.data,
            est_actif=True
        ).first()
        
        if not portefeuille_crypto:
            flash("Aucun portefeuille admin disponible pour ce réseau", "error")
            return redirect(url_for('main.sell'))
        
        # Créer la transaction
        transaction = Transaction(
            utilisateur_id=current_user.id,
            type_transaction='vente',
            montant_xaf=round(montant_xaf, 2),
            montant_usdt=montant_usdt,
            reseau=formulaire.reseau.data,
            numero_mobile_utilisateur=formulaire.numero_mobile.data,
            portefeuille_admin_crypto_id=portefeuille_crypto.id,
            taux_applique=taux_final,
            statut='en_attente'
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        # Notification pour l'admin
        notification = Notification(
            admin_id=1,
            type_notification='nouvelle_transaction',
            message=f"Nouvelle transaction de vente: {montant_usdt} USDT par {current_user.nom}"
        )
        db.session.add(notification)
        db.session.commit()
        
        return redirect(url_for('main.transaction_status', transaction_id=transaction.identifiant_transaction))
    
    return render_template('sell.html', formulaire=formulaire, taux_achat=taux_achat)
@main_bp.route('/transaction/<transaction_id>')
@login_required
def transaction_status(transaction_id):
    """Statut de la transaction"""
    transaction = Transaction.query.filter_by(
        identifiant_transaction=transaction_id,
        utilisateur_id=current_user.id
    ).first_or_404()
    
    return render_template('transaction_status.html', 
                         transaction=transaction,
                         formater_montant=formater_montant)

@main_bp.route('/calculate', methods=['GET', 'POST'])
def calculate():
    """Calculateur de taux"""
    formulaire = FormulaireCalculTaux()
    resultat = None
    erreur = None
    
    if formulaire.validate_on_submit():
        if formulaire.type_calcul.data == 'vente':
            resultat, erreur = calculer_taux_vente_usdt(
                formulaire.taux_mondial.data,
                formulaire.benefice.data,
                formulaire.montant.data
            )
        else:
            resultat, erreur = calculer_taux_achat_usdt(
                formulaire.taux_mondial.data,
                formulaire.benefice.data,
                formulaire.montant.data
            )
    
    return render_template('calculate.html', 
                         formulaire=formulaire,
                         resultat=resultat,
                         erreur=erreur)

# Routes Admin
@admin_bp.route('/')
@login_required
def admin_dashboard():
    """Tableau de bord administrateur"""
    if not current_user.est_admin:
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('dashboard'))
    
    # Statistiques
    total_utilisateurs = Utilisateur.query.count()
    transactions_aujourdhui = Transaction.query.filter(
        db.func.date(Transaction.date_creation) == date.today()
    ).count()
    
    transactions_attente = Transaction.query.filter_by(statut='en_attente').count()
    transactions_complete = Transaction.query.filter_by(statut='complete').count()
    
    # Chiffre d'affaires
    ca_aujourdhui = db.session.query(
        db.func.sum(Transaction.montant_xaf)
    ).filter(
        db.func.date(Transaction.date_creation) == date.today(),
        Transaction.statut == 'complete'
    ).scalar() or 0
    
    ca_total = db.session.query(
        db.func.sum(Transaction.montant_xaf)
    ).filter(
        Transaction.statut == 'complete'
    ).scalar() or 0
    
    # Dernières transactions
    dernieres_transactions = Transaction.query.order_by(
        Transaction.date_creation.desc()
    ).limit(10).all()
    
    # Notifications non lues
    notifications = Notification.query.filter_by(
        admin_id=current_user.id,
        est_lue=False
    ).order_by(Notification.date_creation.desc()).all()
    
    return render_template('admin_dashboard.html',
                         total_utilisateurs=total_utilisateurs,
                         transactions_aujourdhui=transactions_aujourdhui,
                         transactions_attente=transactions_attente,
                         transactions_complete=transactions_complete,
                         ca_aujourdhui=formater_montant(ca_aujourdhui),
                         ca_total=formater_montant(ca_total),
                         dernieres_transactions=dernieres_transactions,
                         notifications=notifications,
                         formater_montant=formater_montant)

@admin_bp.route('/transactions')
@login_required
def admin_transactions():
    """Gestion des transactions par l'admin"""
    if not current_user.est_admin:
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('dashboard'))
    
    statut = request.args.get('statut', 'tous')
    
    if statut == 'tous':
        transactions = Transaction.query.order_by(Transaction.date_creation.desc()).all()
    else:
        transactions = Transaction.query.filter_by(statut=statut).order_by(
            Transaction.date_creation.desc()
        ).all()
    
    return render_template('admin_transactions.html',
                         transactions=transactions,
                         formater_montant=formater_montant)

@admin_bp.route('/transaction/<transaction_id>/validate', methods=['POST'])
@login_required
def validate_transaction(transaction_id):
    """Valider une transaction"""
    if not current_user.est_admin:
        return jsonify({'success': False, 'message': 'Non autorisé'}), 403
    
    transaction = Transaction.query.filter_by(
        identifiant_transaction=transaction_id
    ).first_or_404()
    
    transaction.statut = 'complete'
    transaction.date_validation = datetime.utcnow()
    
    # Notifier l'utilisateur
    notification = Notification(
        utilisateur_id=transaction.utilisateur_id,
        type_notification='transaction_validee',
        message=f'Votre transaction de {transaction.montant_usdt} USDT a été validée.'
    )
    db.session.add(notification)
    db.session.commit()
    
    flash('Transaction validée avec succès.', 'success')
    return jsonify({'success': True})

@admin_bp.route('/transaction/<transaction_id>/reject', methods=['POST'])
@login_required
def reject_transaction(transaction_id):
    """Rejeter une transaction"""
    if not current_user.est_admin:
        return jsonify({'success': False, 'message': 'Non autorisé'}), 403
    
    motif = request.form.get('motif', '')
    
    transaction = Transaction.query.filter_by(
        identifiant_transaction=transaction_id
    ).first_or_404()
    
    transaction.statut = 'rejete'
    transaction.motif_rejet = motif
    transaction.date_validation = datetime.utcnow()
    
    # Notifier l'utilisateur
    notification = Notification(
        utilisateur_id=transaction.utilisateur_id,
        type_notification='transaction_rejetee',
        message=f'Votre transaction a été rejetée. Motif: {motif}'
    )
    db.session.add(notification)
    db.session.commit()
    
    flash('Transaction rejetée.', 'success')
    return jsonify({'success': True})

@admin_bp.route('/wallets')
@login_required
def admin_wallets():
    """Gestion des adresses wallet par l'admin"""
    if not current_user.est_admin:
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('dashboard'))
    
    portefeuilles = PortefeuilleAdmin.query.all()
    
    return render_template('admin_wallets.html', portefeuilles=portefeuilles)

@admin_bp.route('/wallets/add', methods=['GET', 'POST'])
@login_required
def wallets():
    """Gestion des portefeuilles admin"""
    if request.method == 'POST':
        reseau = request.form.get('reseau')
        adresse = request.form.get('adresse')
        pays = request.form.get('pays')
        type_portefeuille = request.form.get('type_portefeuille')
        
        portefeuille = PortefeuilleAdmin(
            reseau=reseau,
            adresse=adresse,
            pays=pays,
            type_portefeuille=type_portefeuille
        )
        
        db.session.add(portefeuille)
        db.session.commit()
        flash("Portefeuille ajouté avec succès", "success")
        return redirect(url_for('admin.admin_wallets'))
    
    portefeuilles = PortefeuilleAdmin.query.all()
    return render_template('admin_wallets.html', portefeuilles=portefeuilles)

@admin_bp.route('/admin/wallet/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_portefeuille(id):
    """Activer/désactiver un portefeuille"""
    portefeuille = PortefeuilleAdmin.query.get_or_404(id)
    portefeuille.est_actif = not portefeuille.est_actif
    db.session.commit()
    return jsonify({'success': True, 'est_actif': portefeuille.est_actif})
@admin_bp.route('/notification/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Marquer une notification comme lue"""
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.admin_id != current_user.id and notification.utilisateur_id != current_user.id:
        return jsonify({'success': False, 'message': 'Non autorisé'}), 403
    
    notification.est_lue = True
    db.session.commit()
    
    return jsonify({'success': True})

# routes.py - Ajouter ces routes dans la section admin_bp
from forms import FormulaireTaux
from datetime import datetime, date, timedelta
import json

@admin_bp.route('/rates', methods=['GET', 'POST'])
@login_required
def admin_rates():
    """Gestion des taux de change par l'admin"""
    if not current_user.est_admin:
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('main.dashboard'))
    
    formulaire = FormulaireTaux()
    
    # Récupérer les taux d'aujourd'hui
    taux_aujourdhui = TauxJournalier.query.filter_by(date=date.today()).first()
    
    # Récupérer l'historique des taux (30 derniers jours)
    historique_taux = TauxJournalier.query.order_by(
        TauxJournalier.date.desc()
    ).limit(30).all()
    
    # Statistiques des taux
    taux_moyen_achat = db.session.query(db.func.avg(TauxJournalier.taux_achat)).scalar() or 0
    taux_moyen_vente = db.session.query(db.func.avg(TauxJournalier.taux_vente)).scalar() or 0
    
    if formulaire.validate_on_submit():
        taux_achat = formulaire.taux_achat.data
        taux_vente = formulaire.taux_vente.data
        date_application = formulaire.date_application.data or date.today()
        
        # Validation : taux de vente doit être supérieur au taux d'achat
        if taux_vente <= taux_achat:
            flash('Le taux de vente doit être supérieur au taux d\'achat.', 'error')
            return render_template('admin_rates.html',
                                 formulaire=formulaire,
                                 taux_aujourdhui=taux_aujourdhui,
                                 historique_taux=historique_taux,
                                 taux_moyen_achat=round(taux_moyen_achat, 2),
                                 taux_moyen_vente=round(taux_moyen_vente, 2),
                                 today=date.today())
        
        # Vérifier si un taux existe déjà pour cette date
        taux_existant = TauxJournalier.query.filter_by(date=date_application).first()
        
        if taux_existant:
            # Mettre à jour le taux existant
            taux_existant.taux_achat = taux_achat
            taux_existant.taux_vente = taux_vente
            taux_existant.timestamp = datetime.utcnow()
            message = 'Taux mis à jour avec succès pour le '
        else:
            # Créer un nouveau taux
            nouveau_taux = TauxJournalier(
                taux_achat=taux_achat,
                taux_vente=taux_vente,
                date=date_application
            )
            db.session.add(nouveau_taux)
            message = 'Nouveau taux ajouté avec succès pour le '
        
        db.session.commit()
        
        # Notifier tous les utilisateurs via notification
        if date_application == date.today():
            utilisateurs = Utilisateur.query.filter_by(est_actif=True).all()
            for utilisateur in utilisateurs:
                notification = Notification(
                    utilisateur_id=utilisateur.id,
                    type_notification='taux_mis_a_jour',
                    message=f'Nouveaux taux disponibles : Achat {taux_achat} XAF | Vente {taux_vente} XAF'
                )
                db.session.add(notification)
            db.session.commit()
        
        flash(f'{message} {date_application.strftime("%d/%m/%Y")}.', 'success')
        return redirect(url_for('admin.admin_rates'))
    
    # Pré-remplir le formulaire avec les taux d'aujourd'hui
    if taux_aujourdhui and not formulaire.is_submitted():
        formulaire.taux_achat.data = taux_aujourdhui.taux_achat
        formulaire.taux_vente.data = taux_aujourdhui.taux_vente
    
    return render_template('admin_rates.html',
                         formulaire=formulaire,
                         taux_aujourdhui=taux_aujourdhui,
                         historique_taux=historique_taux,
                         taux_moyen_achat=round(taux_moyen_achat, 2),
                         taux_moyen_vente=round(taux_moyen_vente, 2),
                         today=date.today())

@admin_bp.route('/api/rates/history')
@login_required
def rates_history_api():
    """API pour obtenir l'historique des taux (pour graphique)"""
    if not current_user.est_admin:
        return jsonify({'error': 'Non autorisé'}), 403
    
    # Récupérer les 60 derniers jours
    jours = request.args.get('days', 30, type=int)
    date_debut = date.today() - timedelta(days=jours)
    
    historique = TauxJournalier.query.filter(
        TauxJournalier.date >= date_debut
    ).order_by(TauxJournalier.date).all()
    
    data = {
        'dates': [t.date.strftime('%Y-%m-%d') for t in historique],
        'achat': [float(t.taux_achat) for t in historique],
        'vente': [float(t.taux_vente) for t in historique],
        'ecart': [float(t.taux_vente - t.taux_achat) for t in historique]
    }
    
    return jsonify(data)

@admin_bp.route('/api/rates/update', methods=['POST'])
@login_required
def update_rates_api():
    """API pour mettre à jour les taux (AJAX)"""
    if not current_user.est_admin:
        return jsonify({'success': False, 'message': 'Non autorisé'}), 403
    
    data = request.get_json()
    
    taux_achat = data.get('taux_achat')
    taux_vente = data.get('taux_vente')
    date_application = data.get('date_application')
    
    if not taux_achat or not taux_vente:
        return jsonify({'success': False, 'message': 'Données manquantes'})
    
    try:
        taux_achat = float(taux_achat)
        taux_vente = float(taux_vente)
        
        if taux_vente <= taux_achat:
            return jsonify({'success': False, 'message': 'Le taux de vente doit être supérieur au taux d\'achat'})
        
        if date_application:
            date_application = datetime.strptime(date_application, '%Y-%m-%d').date()
        else:
            date_application = date.today()
        
        # Vérifier si un taux existe déjà pour cette date
        taux_existant = TauxJournalier.query.filter_by(date=date_application).first()
        
        if taux_existant:
            taux_existant.taux_achat = taux_achat
            taux_existant.taux_vente = taux_vente
            taux_existant.timestamp = datetime.utcnow()
            message = 'Taux mis à jour'
        else:
            nouveau_taux = TauxJournalier(
                taux_achat=taux_achat,
                taux_vente=taux_vente,
                date=date_application
            )
            db.session.add(nouveau_taux)
            message = 'Nouveau taux ajouté'
        
        db.session.commit()
        
        # Si c'est pour aujourd'hui, notifier les utilisateurs
        if date_application == date.today():
            from email_utils import send_rate_update_notification
            # Envoyer des notifications push ou emails aux utilisateurs actifs
            pass
        
        return jsonify({
            'success': True,
            'message': f'{message} avec succès',
            'taux': {
                'achat': taux_achat,
                'vente': taux_vente,
                'date': date_application.strftime('%Y-%m-%d')
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/rates/delete/<int:rate_id>', methods=['POST'])
@login_required
def delete_rate(rate_id):
    """Supprimer un taux de l'historique"""
    if not current_user.est_admin:
        return jsonify({'success': False, 'message': 'Non autorisé'}), 403
    
    taux = TauxJournalier.query.get_or_404(rate_id)
    
    # Ne pas permettre la suppression du taux d'aujourd'hui
    if taux.date == date.today():
        return jsonify({'success': False, 'message': 'Impossible de supprimer le taux du jour actuel'})
    
    try:
        db.session.delete(taux)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Taux supprimé avec succès'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/rates/duplicate/<int:rate_id>', methods=['POST'])
@login_required
def duplicate_rate(rate_id):
    """Dupliquer un taux pour une nouvelle date"""
    if not current_user.est_admin:
        return jsonify({'success': False, 'message': 'Non autorisé'}), 403
    
    taux_source = TauxJournalier.query.get_or_404(rate_id)
    nouvelle_date = request.form.get('nouvelle_date')
    
    if not nouvelle_date:
        return jsonify({'success': False, 'message': 'Date manquante'})
    
    try:
        nouvelle_date = datetime.strptime(nouvelle_date, '%Y-%m-%d').date()
        
        # Vérifier si un taux existe déjà pour cette date
        taux_existant = TauxJournalier.query.filter_by(date=nouvelle_date).first()
        
        if taux_existant:
            return jsonify({'success': False, 'message': 'Un taux existe déjà pour cette date'})
        
        nouveau_taux = TauxJournalier(
            taux_achat=taux_source.taux_achat,
            taux_vente=taux_source.taux_vente,
            date=nouvelle_date
        )
        
        db.session.add(nouveau_taux)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Taux dupliqué pour le {nouvelle_date.strftime("%d/%m/%Y")}',
            'taux': {
                'achat': taux_source.taux_achat,
                'vente': taux_source.taux_vente,
                'date': nouvelle_date.strftime('%Y-%m-%d')
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/rates/export')
@login_required
def export_rates():
    """Exporter l'historique des taux en CSV/Excel"""
    if not current_user.est_admin:
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Récupérer tous les taux
    taux = TauxJournalier.query.order_by(TauxJournalier.date.desc()).all()
    
    # Créer un CSV
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # En-têtes
    writer.writerow(['Date', 'Taux Achat (XAF)', 'Taux Vente (XAF)', 'Écart (XAF)', 'Marge (%)'])
    
    # Données
    for t in taux:
        ecart = t.taux_vente - t.taux_achat
        marge = (ecart / t.taux_achat) * 100 if t.taux_achat > 0 else 0
        writer.writerow([
            t.date.strftime('%Y-%m-%d'),
            t.taux_achat,
            t.taux_vente,
            round(ecart, 2),
            round(marge, 2)
        ])
    
    output.seek(0)
    
    from flask import make_response
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=taux_devisa_fx.csv"
    response.headers["Content-type"] = "text/csv"
    return response






