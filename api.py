# ==============================
# CyberTrust Africa
# API Flask — v6.3 JWT lié au cookie
# ==============================

from flask import Flask, request, jsonify, send_file
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, decode_token
from flask_talisman import Talisman
from flask_cors import CORS
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, text
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import joblib
import numpy as np
import csv
import io
import os
import re
import secrets
import logging
import requests as http_requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.ERROR, format='%(asctime)s %(levelname)s %(message)s')

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501").split(",")
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)

bcrypt = Bcrypt(app)
jwt = JWTManager(app)

Talisman(app, force_https=False, strict_transport_security=True,
         x_content_type_options=True, frame_options='DENY', content_security_policy=False)


ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "").encode()
try:
    fernet = Fernet(ENCRYPTION_KEY)
except Exception:
    fernet = None

ADMIN_KEY = os.getenv("ADMIN_KEY", "")

# ==============================
# Vérification email
# ==============================
VERIFICATION_EMAIL_ACTIVE = True

# ==============================
# Brevo
# ==============================
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
BREVO_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL", "")
BREVO_SENDER_NAME = os.getenv("BREVO_SENDER_NAME", "CyberTrust Africa")

def envoyer_email_verification(email, token):
    try:
        if not BREVO_API_KEY or not BREVO_SENDER_EMAIL:
            return False
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = BREVO_API_KEY
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration))
        base_url = os.getenv("APP_URL", "http://localhost:5000")
        lien = f"{base_url}/verifier-email?token={token}"
        html_content = f"""
        <html><body style="font-family:Arial;max-width:600px;margin:0 auto;padding:20px;">
        <div style="background:#1a1a2e;padding:20px;border-radius:10px;text-align:center;">
            <h1 style="color:#00d4ff;">🌍 CyberTrust Africa</h1>
        </div>
        <div style="padding:30px;background:#f9f9f9;border-radius:10px;margin-top:20px;">
            <h2>Confirmez votre email</h2>
            <p>Cliquez sur le bouton ci-dessous pour confirmer votre adresse email :</p>
            <div style="text-align:center;margin:30px 0;">
                <a href="{lien}" style="background:#00d4ff;color:white;padding:15px 30px;
                   text-decoration:none;border-radius:5px;font-size:16px;font-weight:bold;">
                    ✅ Confirmer mon email
                </a>
            </div>
            <p style="color:#666;font-size:14px;">Ce lien expire dans <b>24 heures</b>.</p>
        </div>
        </body></html>"""
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": email}],
            sender={"name": BREVO_SENDER_NAME, "email": BREVO_SENDER_EMAIL},
            subject="✅ Confirmez votre email — CyberTrust Africa",
            html_content=html_content)
        api_instance.send_transac_email(send_smtp_email)
        return True
    except Exception as e:
        logging.error(f"Erreur email: {str(e)}")
        return False

# ✅ Chargement du modèle avec entraînement automatique si absent
def get_model():
    global _model
    if _model is not None:
        return _model
    model_path = "models/cybertrust_model.pkl"
    if not os.path.exists(model_path):
        logging.warning("Modèle absent — entraînement automatique en cours...")
        try:
            os.makedirs("models", exist_ok=True)
            import pandas as pd
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import LabelEncoder

            # Charger les datasets
            train = pd.read_csv("dataset/train.csv")
            test = pd.read_csv("dataset/test.csv")
            df = pd.concat([train, test], ignore_index=True)

            # Features
            feature_cols = [
                "profile pic", "nums/length username", "fullname words",
                "nums/length fullname", "name==username", "description length",
                "external URL", "private", "#posts", "#followers", "#follows"
            ]
            # Vérifier les colonnes disponibles
            available = [c for c in feature_cols if c in df.columns]
            target_col = "fake" if "fake" in df.columns else df.columns[-1]

            X = df[available].fillna(0)
            y = df[target_col]

            clf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
            clf.fit(X, y)
            joblib.dump(clf, model_path)
            logging.warning("Modèle entraîné et sauvegardé avec succès")
        except Exception as e:
            logging.error("Erreur entraînement: " + str(e))
            raise FileNotFoundError("Impossible de créer le modèle: " + str(e))
    _model = joblib.load(model_path)
    return _model

_model = None
# Charger le modèle au démarrage
try:
    _model = get_model()
    logging.warning("Modèle chargé avec succès")
except Exception as e:
    logging.error(f"Modèle non disponible au démarrage: {str(e)}")

DATABASE_URL = os.getenv("DATABASE_URL", "")
engine = None

def get_engine():
    global engine
    if engine is None and DATABASE_URL:
        try:
            # ✅ Neon.tech nécessite isolation_level AUTOCOMMIT
            engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                pool_recycle=300,
                connect_args={"connect_timeout": 10}
            )
        except Exception as e:
            logging.error(f"Erreur connexion DB: {str(e)}")
    return engine

def execute_query(query, params=None, fetch=False):
    """Execute une requête SQL avec gestion robuste des transactions"""
    eng = get_engine()
    if not eng:
        logging.error("Pas de connexion DB disponible")
        return None
    try:
        # ✅ Utiliser begin() pour garantir le commit automatique
        with eng.begin() as conn:
            result = conn.execute(text(query), params or {})
            if fetch:
                return result.fetchall()
            return True
    except Exception as e:
        logging.error(f"Erreur SQL: {str(e)} | Query: {query[:100]}")
        # ✅ Réinitialiser le moteur en cas d'erreur de connexion
        global engine
        engine = None
        return None

def initialiser_tables():
    queries = [
        """CREATE TABLE IF NOT EXISTS utilisateurs (
            id VARCHAR(50) PRIMARY KEY, email TEXT NOT NULL,
            mot_de_passe TEXT NOT NULL, date_inscription VARCHAR(20),
            pays VARCHAR(100), ville VARCHAR(100),
            email_verifie BOOLEAN DEFAULT FALSE, token_verification VARCHAR(100))""",
        """CREATE TABLE IF NOT EXISTS historique (
            id SERIAL PRIMARY KEY, user_email TEXT, date VARCHAR(20),
            compte_analyse VARCHAR(100), resultat VARCHAR(50),
            score_authenticite FLOAT, score_suspicion FLOAT)""",
        """CREATE TABLE IF NOT EXISTS collecte (
            id SERIAL PRIMARY KEY, date VARCHAR(20), user_email TEXT,
            user_pays VARCHAR(100), user_ville VARCHAR(100), ip_address TEXT,
            pays_ip VARCHAR(100), ville_ip VARCHAR(100), compte_analyse VARCHAR(100),
            nom_complet VARCHAR(200), resultat VARCHAR(50),
            score_authenticite FLOAT, score_suspicion FLOAT)""",
        """CREATE TABLE IF NOT EXISTS regional (
            id SERIAL PRIMARY KEY, date VARCHAR(20), user_email TEXT,
            user_pays VARCHAR(100), user_ville VARCHAR(100), compte_analyse VARCHAR(100),
            nom_complet VARCHAR(200), resultat VARCHAR(50),
            score_authenticite FLOAT, score_suspicion FLOAT)""",
        """CREATE TABLE IF NOT EXISTS denonciations (
            id VARCHAR(50) PRIMARY KEY, date VARCHAR(20), user_email TEXT,
            compte_denonce VARCHAR(100), plateforme VARCHAR(50), type_arnaque VARCHAR(100),
            description TEXT, montant_escroqué FLOAT, date_incident VARCHAR(20),
            pays_victime VARCHAR(100), ville_victime VARCHAR(100),
            score_fiabilite FLOAT, statut VARCHAR(20))""",
        """CREATE TABLE IF NOT EXISTS tentatives (
            email TEXT PRIMARY KEY, nb_tentatives INTEGER DEFAULT 0,
            derniere_tentative VARCHAR(20))"""
    ]
    for q in queries:
        execute_query(q)
    execute_query("ALTER TABLE utilisateurs ADD COLUMN IF NOT EXISTS email_verifie BOOLEAN DEFAULT FALSE")
    execute_query("ALTER TABLE utilisateurs ADD COLUMN IF NOT EXISTS token_verification VARCHAR(100)")

try:
    initialiser_tables()
except Exception as e:
    logging.error(f"Erreur initialisation tables: {str(e)}")

def chiffrer(donnee):
    if fernet and donnee:
        try:
            return fernet.encrypt(str(donnee).encode()).decode()
        except Exception:
            return donnee
    return donnee

def dechiffrer(donnee):
    if fernet and donnee:
        try:
            return fernet.decrypt(str(donnee).encode()).decode()
        except Exception:
            return donnee
    return donnee

def nettoyer_entree(texte):
    if not texte:
        return ""
    texte = re.sub(r'<[^>]+>', '', str(texte))
    for c in ["'", '"', ";", "--", "/*", "*/", "DROP", "SELECT",
              "INSERT", "DELETE", "UPDATE", "UNION", "EXEC", "xp_",
              "<script>", "</script>", "javascript:"]:
        texte = texte.replace(c, "")
    return texte[:500].strip()

def valider_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Format d'email invalide"
    if len(email) > 100:
        return False, "Email trop long"
    return True, "OK"

def geolocalize_ip(ip):
    try:
        if ip in ["127.0.0.1", "localhost", "::1"]:
            return "Local", "Local"
        response = http_requests.get(f"http://ip-api.com/json/{ip}?fields=country,city", timeout=3)
        data = response.json()
        return data.get("country", "Inconnu"), data.get("city", "Inconnu")
    except Exception:
        return "Inconnu", "Inconnu"

def verifier_admin():
    key = request.headers.get("X-Admin-Key", "")
    if not ADMIN_KEY or key != ADMIN_KEY:
        return False
    return True

def get_tentatives(email):
    rows = execute_query(
        "SELECT nb_tentatives, derniere_tentative FROM tentatives WHERE email = :email",
        {"email": email}, fetch=True)
    if rows and len(rows) > 0:
        return rows[0][0], rows[0][1]
    return 0, None

def incrementer_tentatives(email):
    tentatives, _ = get_tentatives(email)
    if tentatives == 0:
        execute_query(
            "INSERT INTO tentatives (email, nb_tentatives, derniere_tentative) VALUES (:email, 1, :date)",
            {"email": email, "date": datetime.now().strftime("%d/%m/%Y %H:%M")})
    else:
        execute_query(
            "UPDATE tentatives SET nb_tentatives = nb_tentatives + 1, derniere_tentative = :date WHERE email = :email",
            {"email": email, "date": datetime.now().strftime("%d/%m/%Y %H:%M")})

def reinitialiser_tentatives(email):
    execute_query("DELETE FROM tentatives WHERE email = :email", {"email": email})

def trouver_utilisateur_par_email(email):
    rows = execute_query(
        "SELECT id, email, mot_de_passe, date_inscription, pays, ville, email_verifie, token_verification FROM utilisateurs",
        fetch=True)
    if not rows:
        return None
    for row in rows:
        try:
            email_stocke = dechiffrer(row[1])
        except Exception:
            email_stocke = row[1]
        if email_stocke == email:
            return {"id": row[0], "email": row[1], "mot_de_passe": row[2],
                    "date_inscription": row[3], "pays": row[4], "ville": row[5],
                    "email_verifie": row[6], "token_verification": row[7]}
    return None

def compter_denonciations(username):
    rows = execute_query(
        "SELECT type_arnaque FROM denonciations WHERE LOWER(compte_denonce) = LOWER(:username) AND statut = 'valide'",
        {"username": username}, fetch=True)
    if not rows:
        return 0, []
    return len(rows), list(set([r[0] for r in rows if r[0]]))

def compter_analyses_compte(username):
    rows = execute_query(
        "SELECT COUNT(*) FROM historique WHERE LOWER(compte_analyse) = LOWER(:username)",
        {"username": username}, fetch=True)
    return rows[0][0] if rows else 0

def get_derniere_analyse_compte(username, user_email):
    rows = execute_query(
        "SELECT date, resultat, score_authenticite, score_suspicion, user_email FROM historique WHERE LOWER(compte_analyse) = LOWER(:username) ORDER BY id DESC",
        {"username": username}, fetch=True)
    if not rows:
        return None
    for row in rows:
        try:
            email_stocke = dechiffrer(row[4])
        except Exception:
            email_stocke = row[4]
        if email_stocke == user_email:
            return {"date": row[0], "resultat": row[1],
                    "score_authenticite": str(row[2]), "score_suspicion": str(row[3])}
    return None

def calculer_score_fiabilite(data):
    score = 0
    description = data.get("description", "")
    if len(description) > 100:
        score += 30
    elif len(description) > 50:
        score += 15
    if data.get("montant_escroqué", 0) > 0:
        score += 20
    if data.get("date_incident", ""):
        score += 15
    if data.get("plateforme", ""):
        score += 10
    if data.get("pays_victime", "") and data.get("ville_victime", ""):
        score += 15
    username = data.get("compte_denonce", "")
    if username:
        rows = execute_query(
            "SELECT id FROM regional WHERE LOWER(compte_analyse) = LOWER(:username) LIMIT 1",
            {"username": username}, fetch=True)
        if rows:
            score += 10
    return min(score, 100)

# ==============================
# Routes
# ==============================
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Bienvenue sur l'API CyberTrust Africa",
        "version": "6.3", "status": "En ligne ✅",
        "database": "PostgreSQL ✅", "jwt_cookie": "Activé ✅"
    })

# ✅ NOUVEAU — Vérification JWT token
@app.route("/verifier-token", methods=["POST"])
def verifier_token():
    try:
        token = request.json.get("token", "")
        if not token:
            return jsonify({"valide": False, "erreur": "Token manquant"}), 401
        decoded = decode_token(token)
        email = decoded.get("sub", "")
        # Vérifier que l'utilisateur existe toujours
        user = trouver_utilisateur_par_email(email)
        if not user:
            return jsonify({"valide": False, "erreur": "Utilisateur introuvable"}), 401
        return jsonify({
            "valide": True,
            "email": email,
            "pays": user.get("pays", ""),
            "ville": user.get("ville", "")
        })
    except Exception as e:
        return jsonify({"valide": False, "erreur": "Token invalide ou expiré"}), 401

@app.route("/verifier-email", methods=["GET"])
def verifier_email():
    token = request.args.get("token", "")
    if not token:
        return "<h1>❌ Token manquant</h1>", 400
    rows = execute_query(
        "SELECT id FROM utilisateurs WHERE token_verification = :token",
        {"token": token}, fetch=True)
    if not rows:
        return "<h1>❌ Token invalide ou expiré</h1>", 400
    execute_query(
        "UPDATE utilisateurs SET email_verifie = TRUE, token_verification = NULL WHERE token_verification = :token",
        {"token": token})
    return """
    <html><body style="font-family:Arial;text-align:center;padding:50px;background:#1a1a2e;color:white;">
        <h1>🌍 CyberTrust Africa</h1>
        <div style="background:#00d4ff;color:#000;padding:20px;border-radius:10px;display:inline-block;margin-top:20px;">
            <h2>✅ Email confirmé avec succès !</h2>
            <p>Vous pouvez maintenant vous connecter.</p>
        </div>
    </body></html>"""

@app.route("/renvoyer-verification", methods=["POST"])
def renvoyer_verification():
    try:
        data = request.json
        email = nettoyer_entree(data.get("email", ""))
        user = trouver_utilisateur_par_email(email)
        if not user:
            return jsonify({"erreur": "Email introuvable"}), 404
        if user.get("email_verifie"):
            return jsonify({"erreur": "Email déjà vérifié"}), 400
        token = secrets.token_urlsafe(32)
        execute_query(
            "UPDATE utilisateurs SET token_verification = :token WHERE id = :id",
            {"token": token, "id": user["id"]})
        envoyer_email_verification(email, token)
        return jsonify({"message": "Email de vérification renvoyé ✅"})
    except Exception as e:
        logging.error(f"Erreur renvoi vérification: {str(e)}")
        return jsonify({"erreur": "Erreur serveur"}), 500

@app.route("/inscription", methods=["POST"])
def inscription():
    try:
        data = request.json
        email = nettoyer_entree(data.get("email", ""))
        mot_de_passe = data.get("mot_de_passe", "")
        pays = nettoyer_entree(data.get("pays", ""))
        ville = nettoyer_entree(data.get("ville", ""))

        if not email or not mot_de_passe:
            return jsonify({"erreur": "Email et mot de passe requis"}), 400
        valide, message = valider_email(email)
        if not valide:
            return jsonify({"erreur": message}), 400
        if trouver_utilisateur_par_email(email):
            return jsonify({"erreur": "Email déjà utilisé"}), 400

        mot_de_passe_hash = bcrypt.generate_password_hash(mot_de_passe).decode("utf-8")
        user_id = str(datetime.now().timestamp()).replace(".", "")
        token = secrets.token_urlsafe(32)
        email_verifie_initial = not VERIFICATION_EMAIL_ACTIVE

        execute_query(
            "INSERT INTO utilisateurs (id, email, mot_de_passe, date_inscription, pays, ville, email_verifie, token_verification) VALUES (:id, :email, :mdp, :date, :pays, :ville, :verifie, :token)",
            {"id": user_id, "email": chiffrer(email), "mdp": mot_de_passe_hash,
             "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
             "pays": pays, "ville": ville, "verifie": email_verifie_initial, "token": token})

        if VERIFICATION_EMAIL_ACTIVE:
            envoyer_email_verification(email, token)
            return jsonify({
                "message": "Compte créé ✅ — Vérifiez votre email",
                "email": email, "pays": pays, "ville": ville,
                "verification_requise": True
            })

        access_token = create_access_token(identity=email)
        return jsonify({
            "message": "Compte créé avec succès ✅",
            "email": email, "token": access_token,
            "pays": pays, "ville": ville, "connexion_auto": True
        })

    except Exception as e:
        logging.error(f"Erreur inscription: {str(e)}")
        return jsonify({"erreur": "Erreur serveur"}), 500

@app.route("/connexion", methods=["POST"])
def connexion():
    try:
        data = request.json
        email = nettoyer_entree(data.get("email", ""))
        mot_de_passe = data.get("mot_de_passe", "")

        if not email or not mot_de_passe:
            return jsonify({"erreur": "Email et mot de passe requis"}), 400

        tentatives, derniere = get_tentatives(email)
        if tentatives >= 5 and derniere:
            derniere_dt = datetime.strptime(derniere, "%d/%m/%Y %H:%M")
            if datetime.now() - derniere_dt < timedelta(minutes=30):
                return jsonify({"erreur": "Compte bloqué — réessayez dans 30 minutes"}), 429
            else:
                reinitialiser_tentatives(email)

        user = trouver_utilisateur_par_email(email)
        if not user:
            return jsonify({"erreur": "Cet email n'existe pas — Créez un compte",
                            "email_inexistant": True}), 404

        if not bcrypt.check_password_hash(user["mot_de_passe"], mot_de_passe):
            incrementer_tentatives(email)
            tentatives_restantes = max(0, 4 - tentatives)
            if tentatives_restantes > 0:
                return jsonify({"erreur": f"Mot de passe incorrect — {tentatives_restantes} tentatives restantes"}), 401
            else:
                return jsonify({"erreur": "Compte bloqué — réessayez dans 30 minutes"}), 429

        if VERIFICATION_EMAIL_ACTIVE and not user.get("email_verifie"):
            return jsonify({
                "erreur": "Email non vérifié — Consultez votre boîte mail",
                "email_non_verifie": True, "email": email}), 403

        reinitialiser_tentatives(email)
        access_token = create_access_token(identity=email)

        return jsonify({
            "message": "Connexion réussie ✅",
            "email": email, "token": access_token,
            "expire_dans": "24 heures",
            "pays": user.get("pays", ""),
            "ville": user.get("ville", ""),
            "heure_connexion": datetime.now().strftime("%d/%m/%Y %H:%M")
        })

    except Exception as e:
        logging.error(f"Erreur connexion: {str(e)}")
        return jsonify({"erreur": "Erreur serveur"}), 500

@app.route("/analyser", methods=["POST"])
def analyser():
    try:
        data = request.json
        if "username" not in data:
            return jsonify({"erreur": "Nom d'utilisateur manquant"}), 400

        username = nettoyer_entree(data["username"])
        fullname = nettoyer_entree(data.get("fullname", ""))
        user_email = nettoyer_entree(data.get("user_email", "anonyme"))
        user_pays = nettoyer_entree(data.get("user_pays", ""))
        user_ville = nettoyer_entree(data.get("user_ville", ""))

        derniere_analyse = get_derniere_analyse_compte(username, user_email)
        nb_analyses_total = compter_analyses_compte(username)

        username_digits = sum(c.isdigit() for c in username)
        username_length = len(username) if len(username) > 0 else 1
        nums_length_username = username_digits / username_length
        fullname_digits = sum(c.isdigit() for c in fullname)
        fullname_length = len(fullname) if len(fullname) > 0 else 1
        nums_length_fullname = fullname_digits / fullname_length
        fullname_words = len(fullname.split())
        name_equals_username = 1 if (fullname.lower().strip() == username.lower().strip() and username != "") else 0

        user_data = np.array([[
            data.get("profile_pic", 1), nums_length_username, fullname_words,
            nums_length_fullname, name_equals_username, data.get("description_length", 0),
            data.get("external_url", 0), data.get("private", 0),
            data.get("posts", 0), data.get("followers", 0), data.get("follows", 0)
        ]])

        model = get_model()
        prediction = model.predict(user_data)
        probability = model.predict_proba(user_data)
        score_authentique = float(round(probability[0][0] * 100, 2))
        score_fake = float(round(probability[0][1] * 100, 2))
        resultat = "Compte authentique ✅" if prediction[0] == 0 else "Compte suspect 🚨"

        ip_address = request.remote_addr or "inconnue"
        pays_ip, ville_ip = geolocalize_ip(ip_address)
        date_maintenant = datetime.now().strftime("%d/%m/%Y %H:%M")

        execute_query(
            "INSERT INTO historique (user_email, date, compte_analyse, resultat, score_authenticite, score_suspicion) VALUES (:email, :date, :compte, :resultat, :auth, :susp)",
            {"email": chiffrer(user_email), "date": date_maintenant, "compte": username,
             "resultat": resultat, "auth": score_authentique, "susp": score_fake})

        execute_query(
            "INSERT INTO collecte (date, user_email, user_pays, user_ville, ip_address, pays_ip, ville_ip, compte_analyse, nom_complet, resultat, score_authenticite, score_suspicion) VALUES (:date, :email, :pays, :ville, :ip, :pays_ip, :ville_ip, :compte, :nom, :resultat, :auth, :susp)",
            {"date": date_maintenant, "email": chiffrer(user_email), "pays": user_pays,
             "ville": user_ville, "ip": chiffrer(ip_address), "pays_ip": pays_ip,
             "ville_ip": ville_ip, "compte": username, "nom": fullname,
             "resultat": resultat, "auth": score_authentique, "susp": score_fake})

        if prediction[0] == 1:
            rows = execute_query(
                "SELECT id FROM regional WHERE LOWER(compte_analyse) = LOWER(:username) LIMIT 1",
                {"username": username}, fetch=True)
            if not rows:
                execute_query(
                    "INSERT INTO regional (date, user_email, user_pays, user_ville, compte_analyse, nom_complet, resultat, score_authenticite, score_suspicion) VALUES (:date, :email, :pays, :ville, :compte, :nom, :resultat, :auth, :susp)",
                    {"date": date_maintenant, "email": chiffrer(user_email), "pays": user_pays,
                     "ville": user_ville, "compte": username, "nom": fullname,
                     "resultat": resultat, "auth": score_authentique, "susp": score_fake})

        signalements_region = 0
        if user_pays:
            rows = execute_query(
                "SELECT COUNT(*) FROM regional WHERE user_pays = :pays",
                {"pays": user_pays}, fetch=True)
            if rows:
                signalements_region = rows[0][0]

        nb_denonciations, types_arnaque = compter_denonciations(username)

        return jsonify({
            "compte_analyse": username, "resultat": resultat,
            "score_authenticite": score_authentique, "score_suspicion": score_fake,
            "signalements_region": signalements_region,
            "region_utilisateur": f"{user_ville}, {user_pays}" if user_ville and user_pays else user_pays,
            "nb_denonciations": nb_denonciations, "types_arnaque": types_arnaque,
            "nb_analyses_total": nb_analyses_total,
            "deja_analyse_par_user": derniere_analyse is not None,
            "derniere_analyse": derniere_analyse
        })

    except Exception as e:
        err_msg = str(e)
        logging.error("Erreur analyse: " + err_msg)
        return jsonify({"erreur": "Erreur serveur: " + err_msg}), 500

@app.route("/denoncer", methods=["POST"])
def denoncer():
    try:
        data = request.json
        for champ in ["compte_denonce", "plateforme", "type_arnaque", "description", "date_incident"]:
            if not data.get(champ, ""):
                return jsonify({"erreur": f"Champ obligatoire manquant : {champ}"}), 400
        description = nettoyer_entree(data.get("description", ""))
        if len(description) < 50:
            return jsonify({"erreur": "La description doit contenir au moins 50 caractères"}), 400
        score_fiabilite = calculer_score_fiabilite(data)
        statut = "valide" if score_fiabilite >= 50 else "en_verification"
        denonciation_id = str(datetime.now().timestamp()).replace(".", "")
        execute_query(
            "INSERT INTO denonciations (id, date, user_email, compte_denonce, plateforme, type_arnaque, description, montant_escroqué, date_incident, pays_victime, ville_victime, score_fiabilite, statut) VALUES (:id, :date, :email, :compte, :plateforme, :type, :desc, :montant, :date_inc, :pays, :ville, :score, :statut)",
            {"id": denonciation_id, "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
             "email": chiffrer(nettoyer_entree(data.get("user_email", "anonyme"))),
             "compte": nettoyer_entree(data.get("compte_denonce", "")),
             "plateforme": nettoyer_entree(data.get("plateforme", "")),
             "type": nettoyer_entree(data.get("type_arnaque", "")),
             "desc": description, "montant": data.get("montant_escroqué", 0),
             "date_inc": nettoyer_entree(data.get("date_incident", "")),
             "pays": nettoyer_entree(data.get("pays_victime", "")),
             "ville": nettoyer_entree(data.get("ville_victime", "")),
             "score": score_fiabilite, "statut": statut})
        message = "✅ Dénonciation enregistrée" if statut == "valide" else "⚠️ Dénonciation en vérification"
        return jsonify({"message": message, "score_fiabilite": score_fiabilite,
                        "statut": statut, "id": denonciation_id})
    except Exception as e:
        logging.error(f"Erreur dénonciation: {str(e)}")
        return jsonify({"erreur": "Erreur serveur"}), 500

@app.route("/historique", methods=["GET"])
def historique():
    try:
        user_email = nettoyer_entree(request.args.get("email", ""))
        if not user_email:
            return jsonify({"erreur": "Email manquant"}), 400
        rows = execute_query(
            "SELECT date, compte_analyse, resultat, score_authenticite, score_suspicion, user_email FROM historique ORDER BY id DESC",
            fetch=True)
        analyses = []
        if rows:
            for row in rows:
                try:
                    email_stocke = dechiffrer(row[5])
                except Exception:
                    email_stocke = row[5]
                if email_stocke == user_email:
                    analyses.append({"date": row[0], "compte_analyse": row[1],
                                     "resultat": row[2], "score_authenticite": str(row[3]),
                                     "score_suspicion": str(row[4])})
        return jsonify({"email": user_email, "total_analyses": len(analyses), "historique": analyses})
    except Exception as e:
        logging.error(f"Erreur historique: {str(e)}")
        return jsonify({"erreur": "Erreur serveur"}), 500

@app.route("/historique/denonciations", methods=["GET"])
def historique_denonciations():
    try:
        user_email = nettoyer_entree(request.args.get("email", ""))
        if not user_email:
            return jsonify({"erreur": "Email manquant"}), 400
        maintenant = datetime.now()
        un_mois = timedelta(days=30)
        denonciations = []
        rows = execute_query(
            "SELECT date, compte_denonce, type_arnaque, statut, user_email FROM denonciations ORDER BY id DESC",
            fetch=True)
        if rows:
            for row in rows:
                try:
                    email_stocke = dechiffrer(row[4])
                except Exception:
                    email_stocke = row[4]
                if email_stocke == user_email:
                    try:
                        date_denon = datetime.strptime(row[0], "%d/%m/%Y %H:%M")
                        if maintenant - date_denon <= un_mois:
                            denonciations.append({"date": row[0], "compte_denonce": row[1],
                                                  "type_arnaque": row[2], "statut": row[3]})
                    except Exception:
                        pass
        return jsonify({"total": len(denonciations), "denonciations": denonciations})
    except Exception as e:
        logging.error(f"Erreur historique dénonciations: {str(e)}")
        return jsonify({"erreur": "Erreur serveur"}), 500

@app.route("/carte/stats", methods=["GET"])
def carte_stats():
    try:
        stats_pays_suspects = {}
        stats_pays_denonciations = {}
        rows_r = execute_query("SELECT user_pays, score_suspicion FROM regional", fetch=True)
        if rows_r:
            for row in rows_r:
                pays = row[0] or ""
                try:
                    score = float(row[1])
                except Exception:
                    score = 0
                if pays and score > 60:
                    stats_pays_suspects[pays] = stats_pays_suspects.get(pays, 0) + 1
        rows_d = execute_query("SELECT pays_victime FROM denonciations WHERE statut = 'valide'", fetch=True)
        if rows_d:
            for row in rows_d:
                pays = row[0] or ""
                if pays:
                    stats_pays_denonciations[pays] = stats_pays_denonciations.get(pays, 0) + 1
        tous_pays = set(list(stats_pays_suspects.keys()) + list(stats_pays_denonciations.keys()))
        stats_combines = [{"pays": p, "comptes_suspects": stats_pays_suspects.get(p, 0),
                           "denonciations": stats_pays_denonciations.get(p, 0)} for p in tous_pays]
        return jsonify({"stats": sorted(stats_combines, key=lambda x: x["denonciations"] + x["comptes_suspects"], reverse=True)})
    except Exception as e:
        logging.error(f"Erreur carte stats: {str(e)}")
        return jsonify({"erreur": "Erreur serveur"}), 500

@app.route("/admin/collecte", methods=["GET"])
def admin_collecte():
    if not verifier_admin():
        return jsonify({"erreur": "Accès non autorisé"}), 403
    try:
        rows = execute_query(
            "SELECT date, user_email, user_pays, user_ville, ip_address, pays_ip, ville_ip, compte_analyse, nom_complet, resultat, score_authenticite, score_suspicion FROM collecte ORDER BY id DESC",
            fetch=True)
        donnees = []
        if rows:
            for row in rows:
                try:
                    email = dechiffrer(row[1])
                    ip = dechiffrer(row[4])
                except Exception:
                    email = row[1]
                    ip = row[4]
                donnees.append({
                    "date": row[0], "user_email": email, "user_pays": row[2],
                    "user_ville": row[3], "ip_address": ip, "pays_ip": row[5],
                    "ville_ip": row[6], "compte_analyse": row[7], "nom_complet": row[8],
                    "resultat": row[9], "score_authenticite": str(row[10]), "score_suspicion": str(row[11])})
        return jsonify({"total": len(donnees), "donnees": donnees})
    except Exception as e:
        logging.error(f"Erreur admin collecte: {str(e)}")
        return jsonify({"erreur": "Erreur serveur"}), 500

@app.route("/admin/utilisateurs", methods=["GET"])
def admin_utilisateurs():
    if not verifier_admin():
        return jsonify({"erreur": "Accès non autorisé"}), 403
    try:
        rows = execute_query(
            "SELECT email, date_inscription, pays, ville, email_verifie FROM utilisateurs",
            fetch=True)
        utilisateurs = []
        if rows:
            for row in rows:
                try:
                    email = dechiffrer(row[0])
                except Exception:
                    email = row[0]
                utilisateurs.append({"email": email, "date_inscription": row[1],
                                     "pays": row[2], "ville": row[3],
                                     "email_verifie": "✅" if row[4] else "❌"})
        return jsonify({"total": len(utilisateurs), "utilisateurs": utilisateurs})
    except Exception as e:
        logging.error(f"Erreur admin utilisateurs: {str(e)}")
        return jsonify({"erreur": "Erreur serveur"}), 500

@app.route("/admin/regional", methods=["GET"])
def admin_regional():
    if not verifier_admin():
        return jsonify({"erreur": "Accès non autorisé"}), 403
    try:
        rows = execute_query(
            "SELECT date, user_email, user_pays, user_ville, compte_analyse, nom_complet, resultat, score_authenticite, score_suspicion FROM regional ORDER BY id DESC",
            fetch=True)
        donnees = []
        stats_pays = {}
        stats_ville = {}
        if rows:
            for row in rows:
                try:
                    email = dechiffrer(row[1])
                except Exception:
                    email = row[1]
                donnees.append({"date": row[0], "user_email": email, "user_pays": row[2],
                                "user_ville": row[3], "compte_analyse": row[4], "nom_complet": row[5],
                                "resultat": row[6], "score_authenticite": str(row[7]), "score_suspicion": str(row[8])})
                pays = row[2] or "Inconnu"
                ville = row[3] or "Inconnue"
                stats_pays[pays] = stats_pays.get(pays, 0) + 1
                stats_ville[ville] = stats_ville.get(ville, 0) + 1
        top_pays = sorted(stats_pays.items(), key=lambda x: x[1], reverse=True)
        top_villes = sorted(stats_ville.items(), key=lambda x: x[1], reverse=True)
        return jsonify({
            "total_signalements": len(donnees),
            "top_pays": [{"pays": p, "signalements": n} for p, n in top_pays[:10]],
            "top_villes": [{"ville": v, "signalements": n} for v, n in top_villes[:10]],
            "donnees": donnees})
    except Exception as e:
        logging.error(f"Erreur admin régional: {str(e)}")
        return jsonify({"erreur": "Erreur serveur"}), 500

@app.route("/admin/denonciations", methods=["GET"])
def admin_denonciations():
    if not verifier_admin():
        return jsonify({"erreur": "Accès non autorisé"}), 403
    try:
        rows = execute_query(
            "SELECT id, date, user_email, compte_denonce, plateforme, type_arnaque, description, montant_escroqué, date_incident, pays_victime, ville_victime, score_fiabilite, statut FROM denonciations ORDER BY id DESC",
            fetch=True)
        denonciations = []
        stats_pays = {}
        stats_ville = {}
        stats_type = {}
        stats_plateforme = {}
        if rows:
            for row in rows:
                try:
                    email = dechiffrer(row[2])
                except Exception:
                    email = row[2]
                d = {"id": row[0], "date": row[1], "user_email": email,
                     "compte_denonce": row[3], "plateforme": row[4], "type_arnaque": row[5],
                     "description": row[6], "montant_escroqué": str(row[7]), "date_incident": row[8],
                     "pays_victime": row[9], "ville_victime": row[10],
                     "score_fiabilite": str(row[11]), "statut": row[12]}
                denonciations.append(d)
                if row[12] == "valide":
                    for val, dct in [(row[9], stats_pays), (row[10], stats_ville),
                                     (row[5], stats_type), (row[4], stats_plateforme)]:
                        if val:
                            dct[val] = dct.get(val, 0) + 1
        return jsonify({
            "total": len(denonciations),
            "valides": sum(1 for d in denonciations if d.get("statut") == "valide"),
            "en_verification": sum(1 for d in denonciations if d.get("statut") == "en_verification"),
            "top_pays": [{"pays": p, "denonciations": n} for p, n in sorted(stats_pays.items(), key=lambda x: x[1], reverse=True)[:10]],
            "top_villes": [{"ville": v, "denonciations": n} for v, n in sorted(stats_ville.items(), key=lambda x: x[1], reverse=True)[:10]],
            "top_types": [{"type": t, "denonciations": n} for t, n in sorted(stats_type.items(), key=lambda x: x[1], reverse=True)],
            "top_plateformes": [{"plateforme": p, "denonciations": n} for p, n in sorted(stats_plateforme.items(), key=lambda x: x[1], reverse=True)],
            "denonciations": denonciations})
    except Exception as e:
        logging.error(f"Erreur admin dénonciations: {str(e)}")
        return jsonify({"erreur": "Erreur serveur"}), 500

@app.route("/admin/telecharger", methods=["GET"])
def admin_telecharger():
    if not verifier_admin():
        return jsonify({"erreur": "Accès non autorisé"}), 403
    try:
        fichier = request.args.get("fichier", "collecte")
        queries = {
            "collecte": "SELECT date, user_email, user_pays, user_ville, ip_address, pays_ip, ville_ip, compte_analyse, nom_complet, resultat, score_authenticite, score_suspicion FROM collecte",
            "regional": "SELECT date, user_email, user_pays, user_ville, compte_analyse, nom_complet, resultat, score_authenticite, score_suspicion FROM regional",
            "denonciations": "SELECT id, date, user_email, compte_denonce, plateforme, type_arnaque, description, montant_escroqué, date_incident, pays_victime, ville_victime, score_fiabilite, statut FROM denonciations",
            "utilisateurs": "SELECT email, date_inscription, pays, ville, email_verifie FROM utilisateurs"
        }
        if fichier not in queries:
            return jsonify({"erreur": "Fichier inconnu"}), 400
        rows = execute_query(queries[fichier], fetch=True)
        if not rows:
            return jsonify({"erreur": "Aucune donnée"}), 404
        output = io.StringIO()
        csv.writer(output).writerows(rows)
        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode("utf-8")),
                         mimetype="text/csv", as_attachment=True,
                         download_name=f"cybertrust_{fichier}.csv")
    except Exception as e:
        logging.error(f"Erreur téléchargement: {str(e)}")
        return jsonify({"erreur": "Erreur serveur"}), 500

if __name__ == "__main__":
    app.run(debug=False, port=5000)