# api_complete.py
from flask import Flask,Blueprint, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, date, timedelta
import hashlib
import csv
from io import StringIO

from config import Config
from models import db, Utilisateur, Transaction, PortefeuilleAdmin, TauxJournalier, Notification

api_bp = Blueprint("api", __name__)

API_PREFIX = "/api/v1"

@app.route(f"{API_PREFIX}/register", methods=["POST"])
def api_register():
    data = request.get_json()
    email = data.get("email")
    mot_de_passe = data.get("mot_de_passe")
    nom = data.get("nom")
    telephone = data.get("telephone")
    pays = data.get("pays")

    if Utilisateur.query.filter_by(email=email).first():
        return jsonify({"success": False, "message": "Email déjà utilisé"}), 400
    if Utilisateur.query.filter_by(telephone=telephone).first():
        return jsonify({"success": False, "message": "Téléphone déjà utilisé"}), 400

    utilisateur = Utilisateur(
        nom=nom,
        email=email,
        telephone=telephone,
        pays=pays,
        mot_de_passe_hash=hashlib.sha256(mot_de_passe.encode()).hexdigest()
    )
    db.session.add(utilisateur)
    db.session.commit()

    return jsonify({"success": True, "message": "Inscription réussie"})


@app.route(f"{API_PREFIX}/login", methods=["POST"])
def api_login():
    data = request.get_json()
    email = data.get("email")
    mot_de_passe = data.get("mot_de_passe")
    utilisateur = Utilisateur.query.filter_by(email=email).first()

    if not utilisateur or utilisateur.mot_de_passe_hash != hashlib.sha256(mot_de_passe.encode()).hexdigest():
        return jsonify({"success": False, "message": "Email ou mot de passe incorrect"}), 401

    access_token = create_access_token(identity=utilisateur.id)
    return jsonify({"success": True, "access_token": access_token, "is_admin": utilisateur.est_admin})

def check_admin():
    user_id = get_jwt_identity()
    user = Utilisateur.query.get(user_id)
    if not user or not user.est_admin:
        return False
    return True

@app.route(f"{API_PREFIX}/transactions", methods=["GET"])
@jwt_required()
def api_transactions():
    user_id = get_jwt_identity()
    transactions = Transaction.query.filter_by(utilisateur_id=user_id).order_by(Transaction.date_creation.desc()).all()
    data = [
        {
            "id": t.identifiant_transaction,
            "type": t.type_transaction,
            "montant_usdt": t.montant_usdt,
            "montant_xaf": t.montant_xaf,
            "statut": t.statut,
            "date_creation": t.date_creation.isoformat(),
            "reseau": t.reseau,
            "adresse_wallet": t.adresse_wallet,
            "numero_marchand": t.numero_marchand,
            "motif_rejet": t.motif_rejet
        } for t in transactions
    ]
    return jsonify({"success": True, "transactions": data})


@app.route(f"{API_PREFIX}/transaction/<string:transaction_id>", methods=["GET"])
@jwt_required()
def api_transaction_detail(transaction_id):
    user_id = get_jwt_identity()
    transaction = Transaction.query.filter_by(identifiant_transaction=transaction_id, utilisateur_id=user_id).first()
    if not transaction:
        return jsonify({"success": False, "message": "Transaction non trouvée"}), 404
    data = {
        "id": transaction.identifiant_transaction,
        "type": transaction.type_transaction,
        "montant_usdt": transaction.montant_usdt,
        "montant_xaf": transaction.montant_xaf,
        "statut": transaction.statut,
        "date_creation": transaction.date_creation.isoformat(),
        "reseau": transaction.reseau,
        "adresse_wallet": transaction.adresse_wallet,
        "numero_marchand": transaction.numero_marchand,
        "motif_rejet": transaction.motif_rejet
    }
    return jsonify({"success": True, "transaction": data})


@app.route(f"{API_PREFIX}/buy", methods=["POST"])
@jwt_required()
def api_buy():
    user_id = get_jwt_identity()
    data = request.get_json()
    montant_xaf = data.get("montant_xaf")
    operateur_mobile = data.get("operateur_mobile")
    adresse_wallet = data.get("adresse_wallet")
    reseau = data.get("reseau")

    taux_du_jour = TauxJournalier.query.filter_by(date=date.today()).first()
    if not taux_du_jour:
        return jsonify({"success": False, "message": "Taux du jour non défini"}), 400

    montant_usdt = montant_xaf / taux_du_jour.taux_vente
    portefeuille = PortefeuilleAdmin.get_numero_marchand(operateur_mobile)
    if not portefeuille:
        return jsonify({"success": False, "message": "Portefeuille non trouvé"}), 400

    transaction = Transaction(
        utilisateur_id=user_id,
        type_transaction="achat",
        montant_xaf=montant_xaf,
        montant_usdt=round(montant_usdt, 2),
        taux_applique=taux_du_jour.taux_vente,
        reseau=reseau,
        adresse_wallet=adresse_wallet,
        operateur_mobile=operateur_mobile,
        numero_marchand=portefeuille.adresse,
        statut="en_attente"
    )
    db.session.add(transaction)
    db.session.commit()

    notif = Notification(
        admin_id=1,
        type_notification="nouvelle_transaction",
        message=f"Nouvel achat : {montant_xaf} XAF"
    )
    db.session.add(notif)
    db.session.commit()

    return jsonify({
        "success": True,
        "transaction_id": transaction.identifiant_transaction,
        "numero": portefeuille.adresse
    })


@app.route(f"{API_PREFIX}/sell", methods=["POST"])
@jwt_required()
def api_sell():
    user_id = get_jwt_identity()
    data = request.get_json()
    montant_usdt = data.get("montant_usdt")
    adresse_wallet = data.get("adresse_wallet")
    reseau = data.get("reseau")

    taux_du_jour = TauxJournalier.query.filter_by(date=date.today()).first()
    if not taux_du_jour:
        return jsonify({"success": False, "message": "Taux du jour non défini"}), 400

    montant_xaf = montant_usdt * taux_du_jour.taux_achat
    portefeuille = PortefeuilleAdmin.get_adresse_crypto(reseau)
    if not portefeuille:
        return jsonify({"success": False, "message": "Portefeuille non trouvé"}), 400

    transaction = Transaction(
        utilisateur_id=user_id,
        type_transaction="vente",
        montant_usdt=montant_usdt,
        montant_xaf=round(montant_xaf, 2),
        taux_applique=taux_du_jour.taux_achat,
        reseau=reseau,
        adresse_wallet=adresse_wallet,
        numero_marchand=None,
        statut="en_attente"
    )
    db.session.add(transaction)
    db.session.commit()

    notif = Notification(
        admin_id=1,
        type_notification="nouvelle_transaction",
        message=f"Nouvelle vente : {montant_usdt} USDT"
    )
    db.session.add(notif)
    db.session.commit()

    return jsonify({
        "success": True,
        "transaction_id": transaction.identifiant_transaction,
        "adresse": portefeuille.adresse
    })


@app.route(f"{API_PREFIX}/admin/transactions/<string:transaction_id>/validate", methods=["POST"])
@jwt_required()
def api_validate_transaction(transaction_id):
    if not check_admin():
        return jsonify({"success": False, "message": "Non autorisé"}), 403

    transaction = Transaction.query.filter_by(identifiant_transaction=transaction_id).first_or_404()
    transaction.statut = "complete"
    transaction.date_validation = datetime.utcnow()
    db.session.add(transaction)
    db.session.commit()

    # Notification utilisateur
    notif = Notification(
        utilisateur_id=transaction.utilisateur_id,
        type_notification="transaction_validee",
        message=f"Transaction validée: {transaction.montant_usdt} USDT"
    )
    db.session.add(notif)
    db.session.commit()

    return jsonify({"success": True})


@app.route(f"{API_PREFIX}/admin/transactions/<string:transaction_id>/reject", methods=["POST"])
@jwt_required()
def api_reject_transaction(transaction_id):
    if not check_admin():
        return jsonify({"success": False, "message": "Non autorisé"}), 403

    data = request.get_json()
    motif = data.get("motif", "")
    transaction = Transaction.query.filter_by(identifiant_transaction=transaction_id).first_or_404()
    transaction.statut = "rejete"
    transaction.motif_rejet = motif
    transaction.date_validation = datetime.utcnow()
    db.session.add(transaction)
    db.session.commit()

    notif = Notification(
        utilisateur_id=transaction.utilisateur_id,
        type_notification="transaction_rejetee",
        message=f"Transaction rejetée. Motif: {motif}"
    )
    db.session.add(notif)
    db.session.commit()

    return jsonify({"success": True})


@app.route(f"{API_PREFIX}/admin/users", methods=["GET"])
@jwt_required()
def api_list_users():
    if not check_admin():
        return jsonify({"success": False, "message": "Non autorisé"}), 403
    users = Utilisateur.query.order_by(Utilisateur.date_inscription.desc()).all()
    data = [{
        "id": u.id,
        "nom": u.nom,
        "email": u.email,
        "telephone": u.telephone,
        "pays": u.pays,
        "admin": u.est_admin
    } for u in users]
    return jsonify({"success": True, "users": data})


@app.route(f"{API_PREFIX}/admin/wallets", methods=["GET", "POST"])
@jwt_required()
def api_wallets():
    if not check_admin():
        return jsonify({"success": False, "message": "Non autorisé"}), 403

    if request.method == "POST":
        data = request.get_json()
        wallet = PortefeuilleAdmin(
            reseau=data.get("reseau"),
            adresse=data.get("adresse"),
            pays=data.get("pays"),
            type_portefeuille=data.get("type")
        )
        db.session.add(wallet)
        db.session.commit()
        return jsonify({"success": True, "message": "Wallet ajouté"})
    wallets = PortefeuilleAdmin.query.all()
    data = [{"id": w.id, "reseau": w.reseau, "adresse": w.adresse, "pays": w.pays, "type": w.type_portefeuille} for w in wallets]
    return jsonify({"success": True, "wallets": data})


@app.route(f"{API_PREFIX}/admin/rates", methods=["GET", "POST"])
@jwt_required()
def api_rates():
    if not check_admin():
        return jsonify({"success": False, "message": "Non autorisé"}), 403

    if request.method == "POST":
        data = request.get_json()
        taux_achat = data.get("taux_achat")
        taux_vente = data.get("taux_vente")
        date_app = datetime.strptime(data.get("date_application", str(date.today())), "%Y-%m-%d").date()

        taux_existant = TauxJournalier.query.filter_by(date=date_app).first()
        if taux_existant:
            taux_existant.taux_achat = taux_achat
            taux_existant.taux_vente = taux_vente
        else:
            taux = TauxJournalier(taux_achat=taux_achat, taux_vente=taux_vente, date=date_app)
            db.session.add(taux)
        db.session.commit()
        return jsonify({"success": True, "message": "Taux mis à jour"})

    rates = TauxJournalier.query.order_by(TauxJournalier.date.desc()).all()
    data = [{"id": r.id, "date": r.date.isoformat(), "achat": r.taux_achat, "vente": r.taux_vente} for r in rates]
    return jsonify({"success": True, "rates": data})


@app.route(f"{API_PREFIX}/admin/rates/export", methods=["GET"])
@jwt_required()
def api_export_rates():
    if not check_admin():
        return jsonify({"success": False, "message": "Non autorisé"}), 403

    rates = TauxJournalier.query.order_by(TauxJournalier.date.desc()).all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Taux Achat", "Taux Vente", "Écart", "Marge (%)"])
    for t in rates:
        ecart = t.taux_vente - t.taux_achat
        marge = (ecart / t.taux_achat) * 100 if t.taux_achat else 0
        writer.writerow([t.date.isoformat(), t.taux_achat, t.taux_vente, round(ecart,2), round(marge,2)])
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=taux_devisa_fx.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@app.route(f"{API_PREFIX}/notifications", methods=["GET"])
@jwt_required()
def api_notifications():
    user_id = get_jwt_identity()
    notifications = Notification.query.filter(
        (Notification.utilisateur_id==user_id) | (Notification.admin_id==user_id)
    ).order_by(Notification.date_creation.desc()).all()
    data = [{"id": n.id, "type": n.type_notification, "message": n.message, "est_lue": n.est_lue, "date": n.date_creation.isoformat()} for n in notifications]
    return jsonify({"success": True, "notifications": data})


@app.route(f"{API_PREFIX}/notifications/<int:notif_id>/read", methods=["POST"])
@jwt_required()
def api_mark_notification_read(notif_id):
    user_id = get_jwt_identity()
    notif = Notification.query.get_or_404(notif_id)
    if notif.utilisateur_id != user_id and notif.admin_id != user_id:
        return jsonify({"success": False, "message": "Non autorisé"}), 403
    notif.est_lue = True
    db.session.commit()
    return jsonify({"success": True})

@app.route(f"{API_PREFIX}/health-check", methods=["GET"])
def health_check():
    return jsonify({"success": True, "status": "OK"})


