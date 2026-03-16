
from flask import Flask, request, jsonify
import joblib
import numpy as np

# 1️⃣ Créer l'application Flask
app = Flask(__name__)

# 2️⃣ Charger le modèle IA
model = joblib.load("models/cybertrust_model.pkl")

# 3️⃣ Route principale
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Bienvenue sur l'API CyberTrust Africa",
        "version": "1.0",
        "status": "En ligne ✅"
    })

# 4️⃣ Route d'analyse
@app.route("/analyser", methods=["POST"])
def analyser():

    try:
        # Recevoir les données
        data = request.json

        # Vérifier que toutes les données sont présentes
        champs_requis = [
            "profile_pic",
            "username",
            "fullname",
            "name_equals_username",
            "description_length",
            "external_url",
            "private",
            "posts",
            "followers",
            "follows"
        ]

        for champ in champs_requis:
            if champ not in data:
                return jsonify({
                    "erreur": f"Champ manquant : {champ}"
                }), 400

        # Calculer automatiquement les proportions
        username = data["username"]
        fullname = data["fullname"]

        username_digits = sum(c.isdigit() for c in username)
        username_length = len(username) if len(username) > 0 else 1
        nums_length_username = username_digits / username_length

        fullname_digits = sum(c.isdigit() for c in fullname)
        fullname_length = len(fullname) if len(fullname) > 0 else 1
        nums_length_fullname = fullname_digits / fullname_length

        fullname_words = len(fullname.split())

        # Préparer les données pour le modèle
        user_data = np.array([[
            data["profile_pic"],
            nums_length_username,
            fullname_words,
            nums_length_fullname,
            data["name_equals_username"],
            data["description_length"],
            data["external_url"],
            data["private"],
            data["posts"],
            data["followers"],
            data["follows"]
        ]])

        # 5️⃣ Prédiction
        prediction = model.predict(user_data)
        probability = model.predict_proba(user_data)

        score_authentique = round(probability[0][0] * 100, 2)
        score_fake = round(probability[0][1] * 100, 2)

        # 6️⃣ Résultat
        if prediction[0] == 0:
            resultat = "Compte authentique ✅"
        else:
            resultat = "Compte suspect 🚨"

        return jsonify({
            "resultat": resultat,
            "score_authenticite": score_authentique,
            "score_suspicion": score_fake,
            "compte_analyse": data["username"]
        })

    except Exception as e:
        return jsonify({
            "erreur": str(e)
        }), 500

# 7️⃣ Lancer l'API
if __name__ == "__main__":
    app.run(debug=True, port=5000)