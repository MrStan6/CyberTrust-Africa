# ==============================
# CyberTrust Africa
# Interface Streamlit + Auth + Historique
# ==============================

import streamlit as st
import requests

# 1️⃣ URL de l'API
API_URL = "https://cybertrust-africa.onrender.com"

# 2️⃣ Configuration de la page
st.set_page_config(
    page_title="CyberTrust Africa",
    page_icon="🌍",
    layout="centered"
)

# 3️⃣ Initialiser la session
if "connecte" not in st.session_state:
    st.session_state.connecte = False
if "email" not in st.session_state:
    st.session_state.email = ""

# 4️⃣ Fonctions d'authentification
def inscrire(email, mot_de_passe):
    response = requests.post(
        f"{API_URL}/inscription",
        json={
            "email": email,
            "mot_de_passe": mot_de_passe
        }
    )
    return response.json()

def connecter(email, mot_de_passe):
    response = requests.post(
        f"{API_URL}/connexion",
        json={
            "email": email,
            "mot_de_passe": mot_de_passe
        }
    )
    return response.json()

def get_historique():
    response = requests.get(
        f"{API_URL}/historique",
        cookies=st.session_state.get("cookies", {})
    )
    return response.json()

# 5️⃣ Page de connexion / inscription
def page_auth():
    st.title("🌍 CyberTrust Africa")
    st.subheader("Détection de faux comptes par IA")
    st.markdown("---")

    onglet1, onglet2 = st.tabs(["🔑 Connexion", "📝 Inscription"])

    # Onglet Connexion
    with onglet1:
        st.markdown("### Connectez-vous")
        email = st.text_input(
            "Email",
            placeholder="votre@email.com",
            key="login_email"
        )
        mot_de_passe = st.text_input(
            "Mot de passe",
            type="password",
            key="login_password"
        )

        if st.button("🔑 Se connecter", use_container_width=True):
            if email and mot_de_passe:
                with st.spinner("Connexion en cours..."):
                    result = connecter(email, mot_de_passe)

                if "erreur" in result:
                    st.error(f"❌ {result['erreur']}")
                else:
                    st.session_state.connecte = True
                    st.session_state.email = email
                    st.success("✅ Connexion réussie !")
                    st.rerun()
            else:
                st.warning("⚠️ Remplissez tous les champs")

    # Onglet Inscription
    with onglet2:
        st.markdown("### Créez votre compte")
        email_inscription = st.text_input(
            "Email",
            placeholder="votre@email.com",
            key="register_email"
        )
        mot_de_passe_inscription = st.text_input(
            "Mot de passe",
            type="password",
            key="register_password"
        )
        confirmer_mot_de_passe = st.text_input(
            "Confirmer le mot de passe",
            type="password",
            key="confirm_password"
        )

        if st.button("📝 S'inscrire", use_container_width=True):
            if email_inscription and mot_de_passe_inscription:
                if mot_de_passe_inscription != confirmer_mot_de_passe:
                    st.error("❌ Les mots de passe ne correspondent pas")
                else:
                    with st.spinner("Création du compte..."):
                        result = inscrire(
                            email_inscription,
                            mot_de_passe_inscription
                        )

                    if "erreur" in result:
                        st.error(f"❌ {result['erreur']}")
                    else:
                        st.success("✅ Compte créé ! Connectez-vous maintenant")
            else:
                st.warning("⚠️ Remplissez tous les champs")

# 6️⃣ Page principale après connexion
def page_principale():

    # Barre latérale
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.email}")
        st.markdown("---")

        page = st.radio(
            "Navigation",
            ["🔍 Analyser", "📊 Historique"]
        )

        st.markdown("---")
        if st.button("🚪 Se déconnecter", use_container_width=True):
            st.session_state.connecte = False
            st.session_state.email = ""
            st.rerun()

    # 7️⃣ Page Analyser
    if page == "🔍 Analyser":
        st.title("🌍 CyberTrust Africa")
        st.subheader("Analyse de fiabilité d'un compte")
        st.markdown("---")

        st.markdown("### 📋 Informations du compte")

        profile_pic = st.selectbox(
            "Le compte a-t-il une photo de profil ?",
            options=[1, 0],
            format_func=lambda x: "Oui" if x == 1 else "Non"
        )

        username = st.text_input(
            "Nom d'utilisateur",
            placeholder="ex: staned_junior6"
        )

        fullname = st.text_input(
            "Nom complet",
            placeholder="ex: Mr.Stan6"
        )

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

        if st.button("🔍 Analyser le compte", use_container_width=True):
            if username == "":
                st.warning("⚠️ Veuillez entrer un nom d'utilisateur")
            else:
                data = {
                    "profile_pic": profile_pic,
                    "username": username,
                    "fullname": fullname,
                    "name_equals_username": name_equals_username,
                    "description_length": int(description_length),
                    "external_url": external_url,
                    "private": private,
                    "posts": int(posts),
                    "followers": int(followers),
                    "follows": int(follows)
                }

                try:
                    with st.spinner("⏳ Analyse en cours..."):
                        response = requests.post(
                            f"{API_URL}/analyser",
                            json=data,
                            cookies=st.session_state.get("cookies", {})
                        )
                        result = response.json()

                    if "erreur" in result:
                        st.error(f"❌ {result['erreur']}")
                    else:
                        st.markdown("---")
                        st.markdown("### 📊 Résultat")

                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric(
                                "✅ Score Authenticité",
                                f"{result['score_authenticite']} %"
                            )
                        with col2:
                            st.metric(
                                "⚠️ Score Suspicion",
                                f"{result['score_suspicion']} %"
                            )

                        if result["score_authenticite"] >= 70:
                            st.success(f"✅ {result['resultat']}")
                            st.balloons()
                        else:
                            st.error(f"🚨 {result['resultat']}")
                            st.warning("Soyez prudent avec ce compte !")

                except Exception as e:
                    st.error("❌ Impossible de contacter l'API")

    # 8️⃣ Page Historique
    elif page == "📊 Historique":
        st.title("📊 Historique des analyses")
        st.markdown("---")

        try:
            with st.spinner("Chargement de l'historique..."):
                result = get_historique()

            if "erreur" in result:
                st.error(f"❌ {result['erreur']}")
            else:
                st.info(f"📈 Total analyses effectuées : **{result['total_analyses']}**")

                if result["total_analyses"] == 0:
                    st.warning("Aucune analyse effectuée pour le moment")
                else:
                    st.markdown("### 📋 Vos analyses")
                    for analyse in reversed(result["historique"]):
                        st.markdown(
                            f"📅 **{analyse['date']}** — "
                            f"@{analyse['compte_analyse']}"
                        )

        except Exception as e:
            st.error("❌ Impossible de charger l'historique")

# 9️⃣ Afficher la bonne page
if st.session_state.connecte:
    page_principale()
else:
    page_auth()