# ==============================
# CyberTrust Africa — v5.7
# Sécurité Complète
# ==============================

import streamlit as st
import requests
import re
import os
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_cookies_manager import EncryptedCookieManager
import pycountry
from datetime import datetime, timedelta

API_URL = "http://127.0.0.1:5000"

# ✅ Clé admin depuis variables d'environnement uniquement
ADMIN_KEY = os.getenv("ADMIN_KEY", "cybertrust_admin_2026_secure")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "CyberTrust@Admin2026!")

# Session timeout — 24 heures
SESSION_TIMEOUT_HEURES = 24

st.set_page_config(page_title="CyberTrust Africa", page_icon="🌍", layout="centered")

cookies = EncryptedCookieManager(prefix="cybertrust_", password="cybertrust_cookie_secret_2026")
if not cookies.ready():
    st.stop()

# ==============================
# ✅ Timeout de session — vérification automatique
# ==============================
def verifier_timeout_session():
    heure_connexion = cookies.get("heure_connexion", "")
    if heure_connexion and st.session_state.get("connecte"):
        try:
            heure_dt = datetime.strptime(heure_connexion, "%d/%m/%Y %H:%M")
            delta = datetime.now() - heure_dt
            if delta.total_seconds() > SESSION_TIMEOUT_HEURES * 3600:
                # Session expirée
                st.session_state.connecte = False
                st.session_state.email = ""
                st.session_state.pays = ""
                st.session_state.ville = ""
                cookies["connecte"] = "false"
                cookies["email"] = ""
                cookies["heure_connexion"] = ""
                cookies.save()
                st.warning("⚠️ Votre session a expiré — Reconnectez-vous")
                st.rerun()
        except Exception:
            pass

# 4️⃣ Session depuis cookies
if "connecte" not in st.session_state:
    if cookies.get("connecte") == "true":
        st.session_state.connecte = True
        st.session_state.email = cookies.get("email", "")
        st.session_state.pays = cookies.get("pays", "")
        st.session_state.ville = cookies.get("ville", "")
    else:
        st.session_state.connecte = False
        st.session_state.email = ""
        st.session_state.pays = ""
        st.session_state.ville = ""

if "dernier_resultat" not in st.session_state:
    st.session_state.dernier_resultat = None
if "admin_connecte" not in st.session_state:
    st.session_state.admin_connecte = False
if "tentatives_admin" not in st.session_state:
    st.session_state.tentatives_admin = 0

# Vérifier le timeout à chaque chargement
if st.session_state.connecte:
    verifier_timeout_session()

def get_tous_pays():
    return sorted([c.name for c in pycountry.countries])

PAYS = get_tous_pays()

PAYS_COORDS = {
    "Senegal": (14.4974, -14.4524), "France": (46.2276, 2.2137),
    "Nigeria": (9.0820, 8.6753), "Cameroon": (3.8480, 11.5021),
    "Morocco": (31.7917, -7.0926), "Algeria": (28.0339, 1.6596),
    "Ghana": (7.9465, -1.0232), "Belgium": (50.5039, 4.4699),
    "United States": (37.0902, -95.7129), "Canada": (56.1304, -106.3468),
    "United Kingdom": (55.3781, -3.4360), "Germany": (51.1657, 10.4515),
    "Italy": (41.8719, 12.5674), "Spain": (40.4637, -3.7492),
    "Portugal": (39.3999, -8.2245), "Brazil": (-14.2350, -51.9253),
    "South Africa": (-30.5595, 22.9375), "Kenya": (-0.0236, 37.9062),
    "Ethiopia": (9.1450, 40.4897), "Tanzania": (-6.3690, 34.8888),
    "Egypt": (26.8206, 30.8025), "Tunisia": (33.8869, 9.5375),
    "Rwanda": (-1.9403, 29.8739), "Uganda": (1.3733, 32.2903),
    "Burkina Faso": (12.3641, -1.5197), "Niger": (17.6078, 8.0817),
    "Guinea": (9.9456, -11.3247), "Benin": (9.3077, 2.3158),
    "Togo": (8.6195, 0.8248), "Gabon": (-0.8037, 11.6094),
    "Madagascar": (-18.7669, 46.8691), "Mali": (17.5707, -3.9962),
    "Congo": (-0.2280, 15.8277), "China": (35.8617, 104.1954),
    "India": (20.5937, 78.9629), "Ivory Coast": (7.5400, -5.5471),
}

def nettoyer_entree(texte):
    if not texte:
        return ""
    texte = re.sub(r'<[^>]+>', '', str(texte))
    for c in ["'", '"', ";", "--", "/*", "*/", "xp_", "DROP", "SELECT",
              "INSERT", "DELETE", "UPDATE", "UNION", "EXEC"]:
        texte = texte.replace(c, "")
    return texte[:500].strip()

def valider_mot_de_passe(mdp):
    if len(mdp) < 12:
        return False, "Le mot de passe doit contenir au moins 12 caractères"
    if not any(c.isupper() for c in mdp):
        return False, "Le mot de passe doit contenir au moins une majuscule"
    if not any(c.islower() for c in mdp):
        return False, "Le mot de passe doit contenir au moins une minuscule"
    if not any(c.isdigit() for c in mdp):
        return False, "Le mot de passe doit contenir au moins un chiffre"
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in mdp):
        return False, "Le mot de passe doit contenir au moins un symbole"
    return True, "OK"

def inscrire(email, mdp, pays, ville):
    r = requests.post(f"{API_URL}/inscription",
                      json={"email": email, "mot_de_passe": mdp, "pays": pays, "ville": ville})
    return r.json()

def connecter(email, mdp):
    r = requests.post(f"{API_URL}/connexion", json={"email": email, "mot_de_passe": mdp})
    return r.json()

def get_historique():
    r = requests.get(f"{API_URL}/historique", params={"email": st.session_state.email})
    return r.json()

def get_historique_denonciations():
    r = requests.get(f"{API_URL}/historique/denonciations", params={"email": st.session_state.email})
    return r.json()

def get_carte_stats():
    r = requests.get(f"{API_URL}/carte/stats")
    return r.json()

def get_admin_collecte():
    r = requests.get(f"{API_URL}/admin/collecte", headers={"X-Admin-Key": ADMIN_KEY})
    return r.json()

def get_admin_utilisateurs():
    r = requests.get(f"{API_URL}/admin/utilisateurs", headers={"X-Admin-Key": ADMIN_KEY})
    return r.json()

def get_admin_regional():
    r = requests.get(f"{API_URL}/admin/regional", headers={"X-Admin-Key": ADMIN_KEY})
    return r.json()

def get_admin_denonciations():
    r = requests.get(f"{API_URL}/admin/denonciations", headers={"X-Admin-Key": ADMIN_KEY})
    return r.json()

def soumettre_denonciation(data):
    r = requests.post(f"{API_URL}/denoncer", json=data)
    return r.json()

def creer_carte(stats):
    m = folium.Map(location=[20, 10], zoom_start=2, tiles="CartoDB positron")
    for item in stats:
        pays = item.get("pays", "")
        suspects = item.get("comptes_suspects", 0)
        denonciations = item.get("denonciations", 0)
        total = suspects + denonciations
        coords = None
        for key, val in PAYS_COORDS.items():
            if key.lower() in pays.lower() or pays.lower() in key.lower():
                coords = val
                break
        if coords and total > 0:
            couleur = "#ff4444" if total >= 5 else "#ff8800" if total >= 2 else "#ffcc00"
            folium.CircleMarker(
                location=coords, radius=max(8, total * 3),
                color=couleur, fill=True, fill_color=couleur, fill_opacity=0.7,
                popup=folium.Popup(
                    f"<b>🌍 {pays}</b><br>🚨 {suspects} suspect(s)<br>📢 {denonciations} dénonciation(s)",
                    max_width=200),
                tooltip=f"{pays}: {suspects} suspects | {denonciations} dénonciations"
            ).add_to(m)
    return m

def sauvegarder_session(email, pays, ville):
    """Sauvegarder session avec heure de connexion"""
    st.session_state.connecte = True
    st.session_state.email = email
    st.session_state.pays = pays
    st.session_state.ville = ville
    cookies["connecte"] = "true"
    cookies["email"] = email
    cookies["pays"] = pays
    cookies["ville"] = ville
    cookies["heure_connexion"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    cookies.save()

def effacer_session():
    """Effacer session complètement"""
    st.session_state.connecte = False
    st.session_state.email = ""
    st.session_state.pays = ""
    st.session_state.ville = ""
    st.session_state.dernier_resultat = None
    st.session_state.admin_connecte = False
    cookies["connecte"] = "false"
    cookies["email"] = ""
    cookies["pays"] = ""
    cookies["ville"] = ""
    cookies["heure_connexion"] = ""
    cookies.save()

# ==============================
# Page Auth
# ==============================
def page_auth():
    st.title("🌍 CyberTrust Africa")
    st.subheader("Détection de faux comptes par IA")
    st.markdown("---")

    onglet1, onglet2 = st.tabs(["🔑 Connexion", "📝 Inscription"])

    with onglet1:
        st.markdown("### Connectez-vous")
        email = st.text_input("Email", placeholder="votre@email.com", key="login_email")
        mdp = st.text_input("Mot de passe", type="password", key="login_password")

        if st.button("🔑 Se connecter", use_container_width=True):
            if email and mdp:
                with st.spinner("Connexion..."):
                    result = connecter(email, mdp)
                if "erreur" in result:
                    st.error(f"❌ {result['erreur']}")
                    if result.get("email_inexistant"):
                        st.info("👉 Pas encore de compte ? Cliquez sur **📝 Inscription**")
                else:
                    sauvegarder_session(email, result.get("pays", ""), result.get("ville", ""))
                    st.success("✅ Connexion réussie !")
                    st.rerun()
            else:
                st.warning("⚠️ Remplissez tous les champs")

    with onglet2:
        st.markdown("### Créez votre compte")
        email_i = st.text_input("Email", placeholder="votre@email.com", key="register_email")
        mdp_i = st.text_input("Mot de passe", type="password", key="register_password")

        if mdp_i:
            ind = st.columns(5)
            with ind[0]:
                if len(mdp_i) >= 12:
                    st.success("12+")
                else:
                    st.error("12+")
            with ind[1]:
                if any(c.isupper() for c in mdp_i):
                    st.success("Maj.")
                else:
                    st.error("Maj.")
            with ind[2]:
                if any(c.islower() for c in mdp_i):
                    st.success("Min.")
                else:
                    st.error("Min.")
            with ind[3]:
                if any(c.isdigit() for c in mdp_i):
                    st.success("Chiff.")
                else:
                    st.error("Chiff.")
            with ind[4]:
                if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in mdp_i):
                    st.success("Symb.")
                else:
                    st.error("Symb.")

        confirmer = st.text_input("Confirmer le mot de passe", type="password", key="confirm_password")
        pays_i = st.selectbox("🌍 Votre pays", ["Sélectionnez votre pays"] + PAYS, key="register_pays")
        ville_i = st.text_input("🏙️ Votre ville", placeholder="ex: Dakar", key="register_ville")

        if st.button("📝 S'inscrire", use_container_width=True):
            if email_i and mdp_i:
                if mdp_i != confirmer:
                    st.error("❌ Les mots de passe ne correspondent pas")
                elif pays_i == "Sélectionnez votre pays":
                    st.error("❌ Sélectionnez votre pays")
                elif not ville_i:
                    st.error("❌ Entrez votre ville")
                else:
                    valide, msg = valider_mot_de_passe(mdp_i)
                    if not valide:
                        st.error(f"❌ {msg}")
                    else:
                        with st.spinner("Création du compte..."):
                            result = inscrire(email_i, mdp_i, pays_i, ville_i)
                        if "erreur" in result:
                            st.error(f"❌ {result['erreur']}")
                        else:
                            sauvegarder_session(email_i, pays_i, ville_i)
                            st.success("✅ Compte créé — Connexion automatique !")
                            st.rerun()
            else:
                st.warning("⚠️ Remplissez tous les champs")

# ==============================
# Page Dénoncer
# ==============================
def page_denoncer():
    st.title("🚨 Dénoncer un cybercriminel")
    st.markdown("---")

    try:
        hist = get_historique_denonciations()
        if hist.get("total", 0) > 0:
            st.markdown("### 📋 Vos dénonciations du mois")
            st.caption("⚠️ Cet historique se supprime automatiquement après 30 jours")
            for d in reversed(hist["denonciations"]):
                statut_icon = "✅" if d["statut"] == "valide" else "⏳"
                st.markdown(f"{statut_icon} **@{d['compte_denonce']}** — {d['type_arnaque']} — {d['date']}")
            st.markdown("---")
    except Exception:
        pass

    st.warning("""
⚠️ **Informations importantes :**
- Ce formulaire est réservé aux **vraies victimes**
- Toute **fausse dénonciation** est une infraction grave
- Si validée, publiée sur les **pages officielles de Cyber Africa Culture**
    """)

    st.markdown("---")
    st.markdown("### 📋 Formulaire de dénonciation")

    st.markdown("#### Étape 1 — Identifier le compte")
    compte_denonce = st.text_input("Nom du compte suspect *", placeholder="ex: fake_account123")
    plateforme = st.selectbox("Plateforme *",
        ["Sélectionnez", "Instagram", "Facebook", "TikTok",
         "Twitter/X", "WhatsApp", "Telegram", "Snapchat", "LinkedIn", "Autre"])

    st.markdown("#### Étape 2 — Type de cybercriminalité")
    type_arnaque = st.selectbox("Type d'arnaque *",
        ["Sélectionnez", "Arnaque financière", "Harcèlement",
         "Extorsion / Chantage", "Usurpation d'identité",
         "Faux profil romantique", "Escroquerie à la vente",
         "Phishing / Liens malveillants", "Autre"])

    st.markdown("#### Étape 3 — Description")
    description = st.text_area("Décrivez ce qui s'est passé *",
        placeholder="Exemple : Le compte m'a contacté en prétendant vendre...", height=150)
    if description:
        nb = len(description)
        if nb < 50:
            st.error(f"❌ {nb}/50 caractères minimum")
        elif nb < 100:
            st.warning(f"⚠️ {nb} caractères — Ajoutez plus de détails")
        else:
            st.success(f"✅ {nb} caractères")

    montant = 0
    if type_arnaque == "Arnaque financière":
        montant = st.number_input("Montant escroqué", min_value=0, step=1000)

    st.markdown("#### Étape 5 — Date et localisation")
    col1, col2 = st.columns(2)
    with col1:
        date_incident = st.date_input("Date de l'incident *")
    with col2:
        pays_victime = st.selectbox("Votre pays *", ["Sélectionnez"] + PAYS, key="denonce_pays")
    ville_victime = st.text_input("Votre ville *", placeholder="ex: Dakar", key="denonce_ville")

    st.markdown("---")
    st.markdown("#### Étape 6 — Questionnaire de vérification")

    q1 = st.radio("Avez-vous effectué une transaction avec ce compte ?",
                  ["Oui", "Non", "Je préfère ne pas répondre"])
    q2 = st.radio("Avez-vous des preuves ?",
                  ["Oui, j'ai des preuves", "Non, je n'ai pas de preuves", "J'ai quelques éléments"])
    q3 = st.radio("Avez-vous signalé ce compte à la plateforme ?",
                  ["Oui", "Non, pas encore", "Je ne sais pas comment"])
    q4 = st.radio("Connaissez-vous personnellement ce compte ?",
                  ["Non, c'est un inconnu", "Oui, je le connais", "Je ne suis pas sûr"])
    q5 = st.checkbox("Je certifie sur l'honneur que les informations sont véridiques", value=False)

    st.markdown("---")

    if st.button("🚨 Soumettre la dénonciation", use_container_width=True, type="primary"):
        erreurs = []
        if not compte_denonce:
            erreurs.append("Nom du compte obligatoire")
        if plateforme == "Sélectionnez":
            erreurs.append("Sélectionnez la plateforme")
        if type_arnaque == "Sélectionnez":
            erreurs.append("Sélectionnez le type d'arnaque")
        if len(description) < 50:
            erreurs.append("Description trop courte (min 50 caractères)")
        if pays_victime == "Sélectionnez":
            erreurs.append("Sélectionnez votre pays")
        if not ville_victime:
            erreurs.append("Entrez votre ville")
        if not q5:
            erreurs.append("Vous devez certifier les informations")
        if q2 == "Non, je n'ai pas de preuves" and q1 == "Non":
            erreurs.append("Signalement insuffisant — pas de preuves ni de transaction")

        if erreurs:
            for e in erreurs:
                st.error(f"❌ {e}")
        else:
            data = {
                "compte_denonce": nettoyer_entree(compte_denonce),
                "plateforme": plateforme, "type_arnaque": type_arnaque,
                "description": nettoyer_entree(description),
                "montant_escroqué": montant,
                "date_incident": str(date_incident),
                "pays_victime": pays_victime,
                "ville_victime": nettoyer_entree(ville_victime),
                "user_email": st.session_state.email
            }
            with st.spinner("Envoi..."):
                result = soumettre_denonciation(data)
            if "erreur" in result:
                st.error(f"❌ {result['erreur']}")
            else:
                st.success(f"✅ {result['message']}")
                st.info(f"📊 Score de fiabilité : **{result['score_fiabilite']}/100**")
                st.markdown("""
---
### 📢 Information importante
Votre dénonciation a bien été enregistrée.
Notre équipe va l'étudier attentivement. **Si validée**, elle sera publiée sur les **pages officielles de Cyber Africa Culture** 🌍
                """)
                if result.get("statut") == "valide":
                    st.balloons()

# ==============================
# Page Carte publique
# ==============================
def page_carte_publique():
    st.title("🗺️ Carte des signalements")
    st.subheader("Comptes suspects et dénonciations par zone")
    st.markdown("---")
    try:
        with st.spinner("Chargement..."):
            result = get_carte_stats()
        stats = result.get("stats", [])
        if not stats:
            st.warning("Aucune donnée disponible")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🚨 Comptes suspects (score > 60%)", sum(s.get("comptes_suspects", 0) for s in stats))
            with col2:
                st.metric("📢 Dénonciations validées", sum(s.get("denonciations", 0) for s in stats))
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("🟡 Faible activité")
            with col2:
                st.markdown("🟠 Activité modérée")
            with col3:
                st.markdown("🔴 Activité élevée")
            m = creer_carte(stats)
            st_folium(m, width=700, height=500)
            st.markdown("---")
            df = pd.DataFrame(stats)
            df = df.rename(columns={"pays": "Pays", "comptes_suspects": "Suspects (IA)", "denonciations": "Dénonciations"})
            df = df[df[["Suspects (IA)", "Dénonciations"]].sum(axis=1) > 0]
            st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"❌ {str(e)}")

# ==============================
# Page Admin Login
# ==============================
def page_admin_login():
    st.title("🔐 Espace Administrateur")
    st.markdown("---")
    if st.session_state.tentatives_admin >= 3:
        st.error("🚨 Accès bloqué")
        return
    st.warning("⚠️ Accès réservé aux administrateurs")
    mdp = st.text_input("Mot de passe admin", type="password", key="admin_pwd")
    st.caption(f"⚠️ {3 - st.session_state.tentatives_admin} tentative(s) restante(s)")
    if st.button("🔐 Accéder", use_container_width=True):
        if mdp == ADMIN_PASSWORD:
            st.session_state.admin_connecte = True
            st.session_state.tentatives_admin = 0
            st.rerun()
        else:
            st.session_state.tentatives_admin += 1
            r = 3 - st.session_state.tentatives_admin
            if r > 0:
                st.error(f"❌ Mot de passe incorrect — {r} tentative(s) restante(s)")
            else:
                st.error("🚨 Accès bloqué définitivement")

# ==============================
# Page Admin Dashboard
# ==============================
def page_admin_dashboard():
    st.title("🔐 Dashboard Administrateur")
    with st.sidebar:
        st.markdown("### 🔐 Admin")
        st.markdown("---")
        onglet_admin = st.radio("Navigation", [
            "📊 Analyses", "👥 Utilisateurs", "📍 Régional",
            "🚨 Dénonciations", "🗺️ Carte Admin", "⬇️ Télécharger"
        ])
        st.markdown("---")
        if st.button("🚪 Déconnexion", use_container_width=True):
            st.session_state.admin_connecte = False
            st.rerun()

    if onglet_admin == "📊 Analyses":
        st.markdown("### 📊 Toutes les analyses")
        try:
            result = get_admin_collecte()
            if "erreur" in result:
                st.error(f"❌ {result['erreur']}")
            else:
                st.info(f"📈 Total : **{result['total']}**")
                if result["total"] > 0:
                    df = pd.DataFrame(result["donnees"])
                    df = df.rename(columns={
                        "date": "Date", "user_email": "Email", "user_pays": "Pays",
                        "user_ville": "Ville", "ip_address": "IP", "pays_ip": "Pays IP",
                        "ville_ip": "Ville IP", "compte_analyse": "Nom utilisateur",
                        "nom_complet": "Nom complet", "resultat": "Résultat",
                        "score_authenticite": "Auth %", "score_suspicion": "Susp %"
                    })
                    st.dataframe(df, use_container_width=True)
                    total = result["total"]
                    suspects = sum(1 for d in result["donnees"] if "suspect" in d.get("resultat", "").lower())
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total", total)
                    with col2:
                        st.metric("✅ Authentiques", total - suspects)
                    with col3:
                        st.metric("🚨 Suspects", suspects)
        except Exception as e:
            st.error(f"❌ {str(e)}")

    elif onglet_admin == "👥 Utilisateurs":
        st.markdown("### 👥 Utilisateurs inscrits")
        try:
            result = get_admin_utilisateurs()
            if "erreur" in result:
                st.error(f"❌ {result['erreur']}")
            else:
                st.info(f"👥 Total : **{result['total']}**")
                if result["total"] > 0:
                    df = pd.DataFrame(result["utilisateurs"])
                    df = df.rename(columns={"email": "Email", "date_inscription": "Date", "pays": "Pays", "ville": "Ville"})
                    st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"❌ {str(e)}")

    elif onglet_admin == "📍 Régional":
        st.markdown("### 📍 Signalements régionaux IA")
        try:
            result = get_admin_regional()
            if "erreur" in result:
                st.error(f"❌ {result['erreur']}")
            else:
                st.info(f"🚨 Total suspects uniques : **{result['total_signalements']}**")
                col1, col2 = st.columns(2)
                with col1:
                    if result["top_pays"]:
                        df_p = pd.DataFrame(result["top_pays"])
                        df_p.columns = ["Pays", "Signalements"]
                        st.dataframe(df_p, use_container_width=True)
                with col2:
                    if result["top_villes"]:
                        df_v = pd.DataFrame(result["top_villes"])
                        df_v.columns = ["Ville", "Signalements"]
                        st.dataframe(df_v, use_container_width=True)
        except Exception as e:
            st.error(f"❌ {str(e)}")

    elif onglet_admin == "🚨 Dénonciations":
        st.markdown("### 🚨 Base de données des dénonciations")
        try:
            result = get_admin_denonciations()
            if "erreur" in result:
                st.error(f"❌ {result['erreur']}")
            else:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total", result["total"])
                with col2:
                    st.metric("✅ Validées", result["valides"])
                with col3:
                    st.metric("⏳ En vérification", result["en_verification"])
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    if result["top_pays"]:
                        df_p = pd.DataFrame(result["top_pays"])
                        df_p.columns = ["Pays", "Dénonciations"]
                        st.dataframe(df_p, use_container_width=True)
                with col2:
                    if result["top_villes"]:
                        df_v = pd.DataFrame(result["top_villes"])
                        df_v.columns = ["Ville", "Dénonciations"]
                        st.dataframe(df_v, use_container_width=True)
                col1, col2 = st.columns(2)
                with col1:
                    if result["top_types"]:
                        df_t = pd.DataFrame(result["top_types"])
                        df_t.columns = ["Type", "Dénonciations"]
                        st.dataframe(df_t, use_container_width=True)
                with col2:
                    if result["top_plateformes"]:
                        df_pl = pd.DataFrame(result["top_plateformes"])
                        df_pl.columns = ["Plateforme", "Dénonciations"]
                        st.dataframe(df_pl, use_container_width=True)
                if result["denonciations"]:
                    st.markdown("---")
                    df = pd.DataFrame(result["denonciations"])
                    st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"❌ {str(e)}")

    elif onglet_admin == "🗺️ Carte Admin":
        st.markdown("### 🗺️ Carte complète Admin")
        try:
            result = get_carte_stats()
            stats = result.get("stats", [])
            if stats:
                m = creer_carte(stats)
                st_folium(m, width=700, height=500)
                df_carte = pd.DataFrame(stats)
                df_carte = df_carte.rename(columns={"pays": "Pays", "comptes_suspects": "Suspects", "denonciations": "Dénonciations"})
                st.download_button("⬇️ Télécharger données carte", df_carte.to_csv(index=False),
                                   "cybertrust_carte.csv", "text/csv", use_container_width=True)
        except Exception as e:
            st.error(f"❌ {str(e)}")

    elif onglet_admin == "⬇️ Télécharger":
        st.markdown("### ⬇️ Télécharger les données")
        try:
            result = get_admin_collecte()
            if result.get("total", 0) > 0:
                st.download_button("⬇️ Analyses complètes", pd.DataFrame(result["donnees"]).to_csv(index=False),
                                   "cybertrust_analyses.csv", "text/csv", use_container_width=True)
            result_u = get_admin_utilisateurs()
            if result_u.get("total", 0) > 0:
                st.download_button("⬇️ Utilisateurs", pd.DataFrame(result_u["utilisateurs"]).to_csv(index=False),
                                   "cybertrust_utilisateurs.csv", "text/csv", use_container_width=True)
            result_r = get_admin_regional()
            if result_r.get("total_signalements", 0) > 0:
                st.download_button("⬇️ Données régionales", pd.DataFrame(result_r["donnees"]).to_csv(index=False),
                                   "cybertrust_regional.csv", "text/csv", use_container_width=True)
            result_d = get_admin_denonciations()
            if result_d.get("total", 0) > 0:
                st.download_button("⬇️ Dénonciations complètes", pd.DataFrame(result_d["denonciations"]).to_csv(index=False),
                                   "cybertrust_denonciations.csv", "text/csv", use_container_width=True)
        except Exception as e:
            st.error(f"❌ {str(e)}")

# ==============================
# Page principale
# ==============================
def page_principale():

    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.email}")
        if st.session_state.pays:
            st.caption(f"📍 {st.session_state.ville}, {st.session_state.pays}")

        # Afficher le temps restant de session
        heure_connexion = cookies.get("heure_connexion", "")
        if heure_connexion:
            try:
                heure_dt = datetime.strptime(heure_connexion, "%d/%m/%Y %H:%M")
                delta = datetime.now() - heure_dt
                restant = timedelta(hours=SESSION_TIMEOUT_HEURES) - delta
                heures = int(restant.total_seconds() // 3600)
                minutes = int((restant.total_seconds() % 3600) // 60)
                if heures >= 0:
                    st.caption(f"⏱️ Session expire dans {heures}h{minutes:02d}m")
            except Exception:
                pass

        st.markdown("---")
        page = st.radio("Navigation", [
            "🔍 Analyser", "🚨 Dénoncer", "🗺️ Carte",
            "📊 Historique", "🔐 Admin"
        ])
        st.markdown("---")
        if st.button("🚪 Se déconnecter", use_container_width=True):
            effacer_session()
            st.rerun()

    if page == "🔍 Analyser":
        st.title("🌍 CyberTrust Africa")
        st.subheader("Analyse de fiabilité d'un compte")
        st.markdown("---")
        st.markdown("### 📋 Informations du compte")

        profile_pic = st.selectbox("Photo de profil ?", options=[1, 0],
                                   format_func=lambda x: "Oui" if x == 1 else "Non")
        username_raw = st.text_input("Nom d'utilisateur", placeholder="ex: staned_junior6")
        username = nettoyer_entree(username_raw)
        fullname_raw = st.text_input("Nom complet", placeholder="ex: Mr.Stan6")
        fullname = nettoyer_entree(fullname_raw)

        name_equals = 1 if (username.lower().strip() == fullname.lower().strip() and username != "") else 0
        if username and fullname:
            st.info("ℹ️ Identique" if name_equals == 1 else "ℹ️ Différent")

        description_length = st.number_input("Longueur de la bio", min_value=0, max_value=500, step=1)
        external_url = st.selectbox("Lien externe ?", options=[0, 1],
                                    format_func=lambda x: "Oui" if x == 1 else "Non")
        private = st.selectbox("Compte privé ?", options=[0, 1],
                                format_func=lambda x: "Oui" if x == 1 else "Non")
        posts = st.number_input("Publications", min_value=0, max_value=100000, step=1)
        followers = st.number_input("Followers", min_value=0, max_value=10000000, step=1)
        follows = st.number_input("Abonnements", min_value=0, max_value=10000000, step=1)

        st.markdown("---")

        if st.button("🔍 Analyser le compte", use_container_width=True):
            if not username:
                st.warning("⚠️ Entrez un nom d'utilisateur")
            else:
                data = {
                    "profile_pic": profile_pic, "username": username,
                    "fullname": fullname, "name_equals_username": name_equals,
                    "description_length": int(description_length),
                    "external_url": external_url, "private": private,
                    "posts": int(posts), "followers": int(followers),
                    "follows": int(follows), "user_email": st.session_state.email,
                    "user_pays": st.session_state.pays, "user_ville": st.session_state.ville
                }
                try:
                    with st.spinner("⏳ Analyse en cours..."):
                        response = requests.post(f"{API_URL}/analyser", json=data)
                        result = response.json()
                    if "erreur" in result:
                        st.error(f"❌ {result['erreur']}")
                    else:
                        st.session_state.dernier_resultat = result
                        st.markdown("---")
                        st.markdown("### 📊 Résultat")

                        if result.get("deja_analyse_par_user") and result.get("derniere_analyse"):
                            da = result["derniere_analyse"]
                            st.info(f"📌 **Déjà analysé !** {da['date']} | {da['resultat']} | Auth: {da['score_authenticite']}% | Susp: {da['score_suspicion']}%")

                        nb_analyses = result.get("nb_analyses_total", 0)
                        if nb_analyses > 0:
                            st.caption(f"📊 Analysé **{nb_analyses} fois** sur CyberTrust Africa")

                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("✅ Score Authenticité", f"{result['score_authenticite']} %")
                        with col2:
                            st.metric("⚠️ Score Suspicion", f"{result['score_suspicion']} %")

                        nb_denon = result.get("nb_denonciations", 0)
                        types_arnaque = result.get("types_arnaque", [])
                        if nb_denon > 0:
                            st.error(f"🚨 **ALERTE — Dénoncé {nb_denon} fois !**\nTypes : **{', '.join(types_arnaque)}**")

                        if result["score_authenticite"] >= 70:
                            st.success(f"✅ {result['resultat']}")
                            if nb_denon == 0:
                                st.balloons()
                        else:
                            st.error(f"🚨 {result['resultat']}")
                            sig = result.get("signalements_region", 0)
                            region = result.get("region_utilisateur", "")
                            if sig > 0 and region:
                                st.warning(f"📍 **{sig} compte(s) suspect(s) unique(s)** dans votre région ({region})")
                            if result["score_suspicion"] >= 70:
                                st.markdown("---")
                                st.markdown("### ⚠️ Recommandations")
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.markdown("**🚫 Arrêter**\n- Cessez tout contact\n- Ne partagez rien")
                                with col2:
                                    st.markdown("**🔒 Bloquer**\n- Bloquez ce compte\n- Signalez à la plateforme")
                                with col3:
                                    st.markdown("**📢 Signaler**\n- Dénoncez sur CyberTrust\n- Portez plainte")
                                st.warning("📞 **En cas d'urgence :** Portez plainte immédiatement")
                            else:
                                st.warning("⚠️ Soyez prudent avec ce compte !")
                except Exception as e:
                    st.error("❌ Impossible de contacter l'API")

        if st.session_state.dernier_resultat and not username:
            result = st.session_state.dernier_resultat
            st.markdown("---")
            st.markdown("### 🕘 Dernier résultat")
            st.info(f"🔎 **@{result['compte_analyse']}**")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("✅ Authenticité", f"{result['score_authenticite']} %")
            with col2:
                st.metric("⚠️ Suspicion", f"{result['score_suspicion']} %")
            if result["score_authenticite"] >= 70:
                st.success(f"✅ {result['resultat']}")
            else:
                st.error(f"🚨 {result['resultat']}")

    elif page == "🚨 Dénoncer":
        page_denoncer()

    elif page == "🗺️ Carte":
        page_carte_publique()

    elif page == "📊 Historique":
        st.title("📊 Historique des analyses")
        st.markdown("---")
        try:
            result = get_historique()
            if "erreur" in result:
                st.error(f"❌ {result['erreur']}")
            else:
                st.info(f"📈 Total : **{result['total_analyses']}**")
                if result["total_analyses"] == 0:
                    st.warning("Aucune analyse effectuée")
                else:
                    for analyse in reversed(result["historique"]):
                        resultat = analyse.get("resultat", "")
                        icon = "✅" if "authentique" in resultat.lower() else "🚨"
                        st.markdown(
                            f"{icon} **{analyse['date']}** — @{analyse['compte_analyse']} "
                            f"| Auth: {analyse.get('score_authenticite', '')}% "
                            f"| Susp: {analyse.get('score_suspicion', '')}%"
                        )
        except Exception as e:
            st.error("❌ Impossible de charger l'historique")

    elif page == "🔐 Admin":
        if st.session_state.admin_connecte:
            page_admin_dashboard()
        else:
            page_admin_login()

# ==============================
# Afficher la bonne page
# ==============================
if st.session_state.connecte:
    page_principale()
else:
    page_auth()