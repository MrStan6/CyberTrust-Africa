# ==============================
# CyberTrust Africa
# API Flask + Sécurité + Historique
# ==============================

from flask import Flask, request, jsonify, session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import joblib
import numpy as np
import csv
import os
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# 1️⃣ Créer l'application Flask
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "cybertrust_secret_2026")

# 2️⃣ Initialiser les extensions
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per day", "10 per minute"]
)

# 3️⃣ Charger le modèle IA
model = joblib.load("models/cybertrust_model.pkl")

# 4️⃣ Base de données simple (fichier CSV)
USERS_FILE = "users.csv"
HISTORIQUE_FILE = "historique.csv"

# Créer les fichiers si inexistants
def initialiser_fichiers():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "email", "mot_de_passe"])

    if not os.path.exists(HISTORIQUE_FILE):
        with open(HISTORIQUE_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "user_email",
                "date",
                "compte_analyse"
            ])

initialiser_fichiers()

# 5️⃣ Modèle utilisateur
class User(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email

def trouver_utilisateur_par_email(email):
    if not os.path.exists(USERS_FILE):
        return None
    with open(USERS_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["email"] == email:
                return row
    return None

def trouver_utilisateur_par_id(user_id):
    if not os.path.exists(USERS_FILE):
        return None
    with open(USERS_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["id"] == str(user_id):
                return row
    return None

@login_manager.user_loader
def load_user(user_id):
    user = trouver_utilisateur_par_id(user_id)
    if user:
        return User(user["id"], user["email"])
    return None

# 6️⃣ Route principale
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Bienvenue sur l'API CyberTrust Africa",
        "version": "3.0",
        "status": "En ligne ✅"
    })

# 7️⃣ Route d'inscription
@app.route("/inscription", methods=["POST"])
@limiter.limit("5 per hour")
def inscription():
    try:
        data = request.json
        email = data.get("email")
        mot_de_passe = data.get("mot_de_passe")

        if not email or not mot_de_passe:
            return jsonify({"erreur": "Email et mot de passe requis"}), 400

        # Vérifier si l'email existe déjà
        if trouver_utilisateur_par_email(email):
            return jsonify({"erreur": "Email déjà utilisé"}), 400

        # Hasher le mot de passe
        mot_de_passe_hash = bcrypt.generate_password_hash(
            mot_de_passe
        ).decode("utf-8")

        # Générer un ID unique
        user_id = str(datetime.now().timestamp()).replace(".", "")

        # Sauvegarder l'utilisateur
        with open(USERS_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([user_id, email, mot_de_passe_hash])

        return jsonify({
            "message": "Compte créé avec succès ✅",
            "email": email
        })

    except Exception as e:
        return jsonify({"erreur": str(e)}), 500

# 8️⃣ Route de connexion
@app.route("/connexion", methods=["POST"])
@limiter.limit("10 per hour")
def connexion():
    try:
        data = request.json
        email = data.get("email")
        mot_de_passe = data.get("mot_de_passe")

        if not email or not mot_de_passe:
            return jsonify({"erreur": "Email et mot de passe requis"}), 400

        # Trouver l'utilisateur
        user = trouver_utilisateur_par_email(email)

        if not user:
            return jsonify({"erreur": "Email ou mot de passe incorrect"}), 401

        # Vérifier le mot de passe
        if not bcrypt.check_password_hash(
            user["mot_de_passe"], mot_de_passe
        ):
            return jsonify({"erreur": "Email ou mot de passe incorrect"}), 401

        # Connecter l'utilisateur
        user_obj = User(user["id"], user["email"])
        login_user(user_obj)

        return jsonify({
            "message": "Connexion réussie ✅",
            "email": email
        })

    except Exception as e:
        return jsonify({"erreur": str(e)}), 500

# 9️⃣ Route de déconnexion
@app.route("/deconnexion", methods=["POST"])
@login_required
def deconnexion():
    logout_user()
    return jsonify({"message": "Déconnexion réussie"})

# 🔟 Route d'analyse
@app.route("/analyser", methods=["POST"])
@limiter.limit("20 per hour")
def analyser():
    try:
        data = request.json

        if "username" not in data:
            return jsonify({"erreur": "Nom d'utilisateur manquant"}), 400

        username = data["username"]
        fullname = data.get("fullname", "")

        # Calculer les proportions
        username_digits = sum(c.isdigit() for c in username)
        username_length = len(username) if len(username) > 0 else 1
        nums_length_username = username_digits / username_length

        fullname_digits = sum(c.isdigit() for c in fullname)
        fullname_length = len(fullname) if len(fullname) > 0 else 1
        nums_length_fullname = fullname_digits / fullname_length

        fullname_words = len(fullname.split())
        name_equals_username = 1 if fullname.lower() == username.lower() else 0

        # Préparer les données
        user_data = np.array([[
            data.get("profile_pic", 1),
            nums_length_username,
            fullname_words,
            nums_length_fullname,
            name_equals_username,
            data.get("description_length", 0),
            data.get("external_url", 0),
            data.get("private", 0),
            data.get("posts", 0),
            data.get("followers", 0),
            data.get("follows", 0)
        ]])

        # Prédiction
        prediction = model.predict(user_data)
        probability = model.predict_proba(user_data)

        score_authentique = round(probability[0][0] * 100, 2)
        score_fake = round(probability[0][1] * 100, 2)

        if prediction[0] == 0:
            resultat = "Compte authentique ✅"
        else:
            resultat = "Compte suspect 🚨"

        # Sauvegarder dans l'historique
        user_email = current_user.email if current_user.is_authenticated else "anonyme"

        with open(HISTORIQUE_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                user_email,
                datetime.now().strftime("%d/%m/%Y %H:%M"),
                username
            ])

        return jsonify({
            "compte_analyse": username,
            "resultat": resultat,
            "score_authenticite": score_authentique,
            "score_suspicion": score_fake
        })

    except Exception as e:
        return jsonify({"erreur": str(e)}), 500

# 1️⃣1️⃣ Route historique
@app.route("/historique", methods=["GET"])
@login_required
def historique():
    try:
        analyses = []
        user_email = current_user.email

        with open(HISTORIQUE_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["user_email"] == user_email:
                    analyses.append({
                        "date": row["date"],
                        "compte_analyse": row["compte_analyse"]
                    })

        return jsonify({
            "email": user_email,
            "total_analyses": len(analyses),
            "historique": analyses
        })

    except Exception as e:
        return jsonify({"erreur": str(e)}), 500

# 1️⃣2️⃣ Lancer l'API
if __name__ == "__main__":
    app.run(debug=True, port=5000)