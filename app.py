import streamlit as st
import requests

# 1️⃣ URL de l'API
API_URL = "https://cybertrust-africa.onrender.com/analyser"

# 2️⃣ Titre de la plateforme
st.title("🌍 CyberTrust Africa")
st.subheader("Analyse de fiabilité d'un compte")
st.markdown("---")

# 3️⃣ Formulaire utilisateur
st.markdown("### 📋 Informations du compte")

profile_pic = st.selectbox(
    "Le compte a-t-il une photo de profil ?",
    options=[1, 0],
    format_func=lambda x: "Oui" if x == 1 else "Non"
)

username = st.text_input("Nom d'utilisateur du compte (ex: staned_junior6)")

fullname = st.text_input("Nom complet du compte (ex: Mr.Stan6)")

name_equals_username = st.selectbox(
    "Le nom complet est-il identique au nom d'utilisateur ?",
    options=[0, 1],
    format_func=lambda x: "Oui" if x == 1 else "Non"
)

description_length = st.number_input(
    "Longueur de la bio (nombre de caractères)",
    min_value=0,
    max_value=500,
    step=1
)

external_url = st.selectbox(
    "Le compte a-t-il un lien externe ?",
    options=[0, 1],
    format_func=lambda x: "Oui" if x == 1 else "Non"
)

private = st.selectbox(
    "Le compte est-il privé ?",
    options=[0, 1],
    format_func=lambda x: "Oui" if x == 1 else "Non"
)

posts = st.number_input(
    "Nombre de publications",
    min_value=0,
    max_value=100000,
    step=1
)

followers = st.number_input(
    "Nombre de followers",
    min_value=0,
    max_value=10000000,
    step=1
)

follows = st.number_input(
    "Nombre d'abonnements",
    min_value=0,
    max_value=10000000,
    step=1
)

st.markdown("---")

# 4️⃣ Bouton d'analyse
if st.button("🔍 Analyser le compte"):

    # Vérifier que le nom d'utilisateur est rempli
    if username == "":
        st.warning("⚠️ Veuillez entrer un nom d'utilisateur")

    else:
        # Préparer les données à envoyer à l'API
        data = {
            "profile_pic": profile_pic,
            "username": username,
            "fullname": fullname,
            "name_equals_username": name_equals_username,
            "description_length": description_length,
            "external_url": external_url,
            "private": private,
            "posts": int(posts),
            "followers": int(followers),
            "follows": int(follows)
        }

        # 5️⃣ Envoyer les données à l'API Flask
        try:
            with st.spinner("Analyse en cours..."):
                response = requests.post(API_URL, json=data)
                result = response.json()

            # 6️⃣ Afficher le résultat
            st.markdown("---")
            st.markdown("### 📊 Résultat de l'analyse")

            # Compte analysé
            st.info(f"🔎 Compte analysé : **{result['compte_analyse']}**")

            # Scores
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    label="✅ Score Authenticité",
                    value=f"{result['score_authenticite']} %"
                )

            with col2:
                st.metric(
                    label="⚠️ Score Suspicion",
                    value=f"{result['score_suspicion']} %"
                )

            # Résultat final
            if result["score_authenticite"] >= 70:
                st.success(f"✅ {result['resultat']}")
                st.balloons()
            else:
                st.error(f"🚨 {result['resultat']}")
                st.warning("Soyez prudent avec ce compte !")

        except Exception as e:
            st.error("❌ Impossible de contacter l'API. Vérifiez que Flask est bien lancé.")