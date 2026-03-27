# ==============================
# CyberTrust Africa — v7.0
# Design + Historique personnel + Bugfixes
# ==============================

import streamlit as st
import requests
import requests.exceptions
import re
import os
import json
import hashlib
import pandas as pd
import folium
from streamlit_folium import st_folium
import pycountry
from datetime import datetime, timedelta

# ==============================
# Config
# ==============================
API_URL = os.getenv("API_URL", "http://127.0.0.1:5000")
ADMIN_KEY = os.getenv("ADMIN_KEY", "cybertrust_admin_2026_secure")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "CyberTrust@Admin2026!")
SESSION_TIMEOUT_HEURES = 24
CACHE_DIR = ".ct_cache"

st.set_page_config(
    page_title="CyberTrust Africa",
    page_icon="🌍",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ==============================
# Cache JSON local — Historique personnel
# ==============================
def _get_cache_file(email):
    if not email:
        return None
    os.makedirs(CACHE_DIR, exist_ok=True)
    h = hashlib.md5(email.strip().lower().encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{h}.json")

def charger_cache(email):
    path = _get_cache_file(email)
    if not path or not os.path.exists(path):
        return {"historique": [], "dernier_resultat": None}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"historique": [], "dernier_resultat": None}

def sauvegarder_cache(email, data):
    path = _get_cache_file(email)
    if not path:
        return
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def ajouter_au_cache(email, analyse):
    cache = charger_cache(email)
    hist = cache.get("historique", [])
    cle = analyse.get("compte_analyse","") + analyse.get("date","")
    existants = {a.get("compte_analyse","") + a.get("date","") for a in hist}
    if cle not in existants:
        hist.insert(0, analyse)
    cache["historique"] = hist[:200]
    sauvegarder_cache(email, cache)

def sauvegarder_dernier(email, resultat):
    cache = charger_cache(email)
    cache["dernier_resultat"] = resultat
    sauvegarder_cache(email, cache)

# ==============================
# CSS Design Africain Dark Mode
# ==============================
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

    .stApp {
        background: #0a0a0f !important;
        background-image:
            repeating-linear-gradient(45deg, rgba(245,158,11,0.015) 0, rgba(245,158,11,0.015) 1px, transparent 0, transparent 50%),
            repeating-linear-gradient(-45deg, rgba(245,158,11,0.015) 0, rgba(245,158,11,0.015) 1px, transparent 0, transparent 50%);
        background-size: 24px 24px;
    }

    [data-testid="stSidebar"] {
        background: #111827 !important;
        border-right: 0.5px solid rgba(245,158,11,0.2) !important;
    }
    [data-testid="stSidebar"] * { color: #d1d5db !important; }

    /* Bouton hamburger sidebar */
    [data-testid="collapsedControl"] {
        background: #111827 !important;
        border: 0.5px solid rgba(245,158,11,0.3) !important;
        border-radius: 8px !important;
        color: #f59e0b !important;
        display: flex !important;
        visibility: visible !important;
    }
    [data-testid="collapsedControl"] svg { fill: #f59e0b !important; }

    h1 {
        background: linear-gradient(135deg, #f59e0b, #ef4444) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        font-weight: 600 !important;
    }
    h2, h3 { color: #f9fafb !important; font-weight: 500 !important; }
    p, label, .stMarkdown { color: #d1d5db !important; }

    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: #0a0a0f !important;
        border: 0.5px solid rgba(255,255,255,0.1) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: rgba(245,158,11,0.5) !important;
        box-shadow: 0 0 0 2px rgba(245,158,11,0.1) !important;
    }
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder { color: #4b5563 !important; }

    .stSelectbox > div > div {
        background: #0a0a0f !important;
        border: 0.5px solid rgba(255,255,255,0.1) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #f59e0b, #d97706) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        opacity: 0.9 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 15px rgba(245,158,11,0.3) !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #ef4444, #f97316) !important;
    }
    .stButton > button[kind="secondary"] {
        background: #1f2937 !important;
        border: 0.5px solid rgba(255,255,255,0.1) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        background: #0a0a0f !important;
        border-radius: 10px !important;
        padding: 4px !important;
        border-bottom: none !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border-radius: 8px !important;
        color: #6b7280 !important;
        font-weight: 500 !important;
        border: none !important;
    }
    .stTabs [data-baseweb="tab"]:first-child[aria-selected="true"] {
        background: #111827 !important;
        color: #f59e0b !important;
        border: 0.5px solid rgba(245,158,11,0.3) !important;
    }
    .stTabs [data-baseweb="tab"]:last-child[aria-selected="true"] {
        background: #111827 !important;
        color: #10b981 !important;
        border: 0.5px solid rgba(16,185,129,0.3) !important;
    }
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] { display: none !important; }

    [data-testid="stMetric"] {
        background: #111827 !important;
        border: 0.5px solid rgba(245,158,11,0.15) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }
    [data-testid="stMetricLabel"] { color: #9ca3af !important; }
    [data-testid="stMetricValue"] { color: #f59e0b !important; font-weight: 600 !important; }

    .stSuccess { background: rgba(16,185,129,0.1) !important; border: 0.5px solid rgba(16,185,129,0.3) !important; border-radius: 8px !important; color: #10b981 !important; }
    .stError { background: rgba(239,68,68,0.1) !important; border: 0.5px solid rgba(239,68,68,0.3) !important; border-radius: 8px !important; color: #ef4444 !important; }
    .stWarning { background: rgba(245,158,11,0.1) !important; border: 0.5px solid rgba(245,158,11,0.3) !important; border-radius: 8px !important; color: #f59e0b !important; }
    .stInfo { background: rgba(59,130,246,0.1) !important; border: 0.5px solid rgba(59,130,246,0.3) !important; border-radius: 8px !important; color: #60a5fa !important; }

    .stDataFrame { border: 0.5px solid rgba(245,158,11,0.15) !important; border-radius: 8px !important; }
    .stRadio > div > label { color: #9ca3af !important; }
    .stCheckbox > label { color: #9ca3af !important; }
    .stCaption { color: #6b7280 !important; }
    .stDownloadButton > button { background: rgba(16,185,129,0.1) !important; border: 0.5px solid rgba(16,185,129,0.3) !important; color: #10b981 !important; }

    #MainMenu, footer, header { visibility: hidden; }
    hr { border-color: rgba(245,158,11,0.15) !important; }
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: #0a0a0f; }
    ::-webkit-scrollbar-thumb { background: rgba(245,158,11,0.3); border-radius: 2px; }

    .ct-card {
        background: #111827;
        border: 0.5px solid rgba(245,158,11,0.15);
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
    }
    .ct-card-red {
        background: #111827;
        border: 0.5px solid rgba(239,68,68,0.2);
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
    }
    .ct-section-title {
        font-size: 11px; font-weight: 500; color: #f59e0b;
        letter-spacing: 1px; text-transform: uppercase;
        margin-bottom: 0.75rem; display: block;
    }
    .ct-section-title-red {
        font-size: 11px; font-weight: 500; color: #ef4444;
        letter-spacing: 1px; text-transform: uppercase;
        margin-bottom: 0.75rem; display: block;
    }
    .ct-hist-item {
        background: #0a0a0f; border-radius: 10px; padding: 12px 14px;
        margin-bottom: 6px; display: flex; align-items: center;
        justify-content: space-between;
    }
    .ct-hist-item.suspect { border-left: 3px solid #ef4444; border: 0.5px solid rgba(239,68,68,0.15); border-left: 3px solid #ef4444; }
    .ct-hist-item.authentique { border-left: 3px solid #10b981; border: 0.5px solid rgba(16,185,129,0.15); border-left: 3px solid #10b981; }
    .ct-badge-secure {
        display: inline-flex; align-items: center; gap: 6px;
        background: rgba(16,185,129,0.1); border: 0.5px solid rgba(16,185,129,0.3);
        border-radius: 20px; padding: 4px 12px; font-size: 12px; color: #10b981;
    }
    </style>
    """, unsafe_allow_html=True)

inject_css()

# ==============================
# API Helper — Gestion robuste erreurs
# ==============================
def api_call(func):
    try:
        r = func()
        try:
            data = r.json()
        except Exception:
            return {"erreur": f"Réponse invalide (status {r.status_code})"}
        return data
    except requests.exceptions.Timeout:
        return {"erreur": "⏳ Serveur en cours de démarrage — réessayez dans 30 secondes"}
    except requests.exceptions.ConnectionError:
        return {"erreur": "❌ API non disponible — vérifiez que Flask tourne"}
    except Exception as e:
        return {"erreur": str(e)}

def api_get(path, params=None, headers=None):
    return api_call(lambda: requests.get(f"{API_URL}{path}", params=params, headers=headers, timeout=30))

def api_post(path, json_data=None, headers=None):
    return api_call(lambda: requests.post(f"{API_URL}{path}", json=json_data, headers=headers, timeout=30))

# ==============================
# Session via query_params
# ==============================
if "connecte" not in st.session_state:
    p = st.query_params
    email = p.get("ct_email", "")
    token = p.get("ct_token", "")
    if p.get("ct_ok") == "1" and email and token:
        st.session_state.connecte = True
        st.session_state.email = email
        st.session_state.pays = p.get("ct_pays", "")
        st.session_state.ville = p.get("ct_ville", "")
        st.session_state.jwt_token = token
        # Charger cache personnel
        cache = charger_cache(email)
        st.session_state.historique_perso = cache.get("historique", [])
        st.session_state.dernier_resultat = cache.get("dernier_resultat", None)
    else:
        st.session_state.connecte = False
        st.session_state.email = ""
        st.session_state.pays = ""
        st.session_state.ville = ""
        st.session_state.jwt_token = ""
        st.session_state.historique_perso = []
        st.session_state.dernier_resultat = None

if "page_active" not in st.session_state:
    st.session_state.page_active = "analyser"
if "admin_connecte" not in st.session_state:
    st.session_state.admin_connecte = False
if "tentatives_admin" not in st.session_state:
    st.session_state.tentatives_admin = 0
if "selected_types" not in st.session_state:
    st.session_state.selected_types = []

# ==============================
# Helpers
# ==============================
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
    "Egypt": (26.8206, 30.8025), "Tunisia": (33.8869, 9.5375),
    "Burkina Faso": (12.3641, -1.5197), "Benin": (9.3077, 2.3158),
    "Togo": (8.6195, 0.8248), "Mali": (17.5707, -3.9962),
    "Ivory Coast": (7.5400, -5.5471), "Congo": (-0.2280, 15.8277),
    "Guinea": (9.9456, -11.3247), "Niger": (17.6078, 8.0817),
    "Madagascar": (-18.7669, 46.8691), "Rwanda": (-1.9403, 29.8739),
    "Ethiopia": (9.1450, 40.4897), "Tanzania": (-6.3690, 34.8888),
    "Uganda": (1.3733, 32.2903), "India": (20.5937, 78.9629),
    "China": (35.8617, 104.1954), "Gabon": (-0.8037, 11.6094),
}

def nettoyer(texte):
    if not texte:
        return ""
    texte = re.sub(r'<[^>]+>', '', str(texte))
    for c in ["'", '"', ";", "--", "DROP", "SELECT", "INSERT", "DELETE", "UPDATE", "UNION", "EXEC"]:
        texte = texte.replace(c, "")
    return texte[:500].strip()

def valider_mdp(mdp):
    if len(mdp) < 12: return False, "Au moins 12 caractères"
    if not any(c.isupper() for c in mdp): return False, "Au moins une majuscule"
    if not any(c.islower() for c in mdp): return False, "Au moins une minuscule"
    if not any(c.isdigit() for c in mdp): return False, "Au moins un chiffre"
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in mdp): return False, "Au moins un symbole"
    return True, "OK"

def sauvegarder_session(email, pays, ville, token):
    st.session_state.connecte = True
    st.session_state.email = email
    st.session_state.pays = pays
    st.session_state.ville = ville
    st.session_state.jwt_token = token
    # Charger historique personnel depuis cache
    cache = charger_cache(email)
    st.session_state.historique_perso = cache.get("historique", [])
    st.session_state.dernier_resultat = cache.get("dernier_resultat", None)
    # Persister dans query_params
    try:
        st.query_params["ct_ok"] = "1"
        st.query_params["ct_email"] = email
        st.query_params["ct_pays"] = pays
        st.query_params["ct_ville"] = ville
        st.query_params["ct_token"] = token
    except Exception:
        pass

def effacer_session():
    st.session_state.connecte = False
    st.session_state.email = ""
    st.session_state.pays = ""
    st.session_state.ville = ""
    st.session_state.jwt_token = ""
    st.session_state.historique_perso = []
    st.session_state.dernier_resultat = None
    st.session_state.admin_connecte = False
    st.session_state.page_active = "analyser"
    try:
        for k in ["ct_ok","ct_email","ct_pays","ct_ville","ct_token"]:
            if k in st.query_params:
                del st.query_params[k]
    except Exception:
        pass

def creer_carte(stats):
    m = folium.Map(location=[20, 10], zoom_start=2, tiles="CartoDB dark_matter")
    for item in stats:
        pays = item.get("pays", "")
        suspects = item.get("comptes_suspects", 0)
        denons = item.get("denonciations", 0)
        total = suspects + denons
        coords = None
        for key, val in PAYS_COORDS.items():
            if key.lower() in pays.lower() or pays.lower() in key.lower():
                coords = val
                break
        if coords and total > 0:
            couleur = "#ef4444" if total >= 5 else "#f59e0b" if total >= 2 else "#10b981"
            folium.CircleMarker(
                location=coords, radius=max(8, total * 3),
                color=couleur, fill=True, fill_color=couleur, fill_opacity=0.8,
                popup=folium.Popup(f"<b style='color:#f59e0b'>🌍 {pays}</b><br>🚨 {suspects} suspect(s)<br>📢 {denons} dénonciation(s)", max_width=200),
                tooltip=f"{pays}: {suspects} suspects | {denons} dénonciations"
            ).add_to(m)
    return m

# ==============================
# Page Auth
# ==============================
def page_auth():
    st.markdown("""
    <div style="text-align:center;margin-bottom:0.5rem;">
        <div style="width:56px;height:56px;background:linear-gradient(135deg,#f59e0b,#ef4444);border-radius:14px;display:inline-flex;align-items:center;justify-content:center;font-size:28px;">🌍</div>
    </div>
    """, unsafe_allow_html=True)
    st.title("CyberTrust Africa")
    st.markdown("<p style='text-align:center;color:#f59e0b;font-size:11px;letter-spacing:2px;text-transform:uppercase;'>Détection de faux comptes par IA</p>", unsafe_allow_html=True)
    st.markdown("""
    <div style="display:flex;justify-content:center;margin:1rem 0;">
        <div class="ct-badge-secure">
            <span style="width:6px;height:6px;background:#10b981;border-radius:50%;display:inline-block;"></span>
            Système sécurisé — v7.0
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    tab1, tab2 = st.tabs(["🔑 Connexion", "📝 Inscription"])

    with tab1:
        email = st.text_input("Email", placeholder="votre@email.com", key="login_email")
        mdp = st.text_input("Mot de passe", type="password", key="login_mdp")
        if st.button("🔑 Se connecter", use_container_width=True):
            if not email or not mdp:
                st.warning("⚠️ Remplissez tous les champs")
            else:
                with st.spinner("Connexion en cours..."):
                    result = api_post("/connexion", {"email": email, "mot_de_passe": mdp})
                if "erreur" in result:
                    msg = result["erreur"]
                    st.error(f"❌ {msg}")
                    if "n'existe pas" in msg:
                        st.info("👉 Pas encore de compte ? Cliquez sur **📝 Inscription**")
                    if "non vérifié" in msg:
                        st.warning("📧 Vérifiez votre boîte mail et cliquez sur le lien")
                        if st.button("📨 Renvoyer l'email", use_container_width=True):
                            r = api_post("/renvoyer-verification", {"email": email})
                            st.success("✅ Email renvoyé") if "erreur" not in r else st.error(f"❌ {r['erreur']}")
                    if "bloqué" in msg:
                        st.warning("⏳ Trop de tentatives — réessayez dans 30 minutes")
                else:
                    sauvegarder_session(email, result.get("pays",""), result.get("ville",""), result.get("token",""))
                    st.success("✅ Connexion réussie !")
                    st.rerun()

    with tab2:
        email_i = st.text_input("Email", placeholder="votre@email.com", key="reg_email")
        mdp_i = st.text_input("Mot de passe", type="password", key="reg_mdp")
        if mdp_i:
            cols = st.columns(5)
            checks = [
                (len(mdp_i)>=12, "12+"),
                (any(c.isupper() for c in mdp_i), "Maj."),
                (any(c.islower() for c in mdp_i), "Min."),
                (any(c.isdigit() for c in mdp_i), "Chiff."),
                (any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in mdp_i), "Symb.")
            ]
            for i, (ok, label) in enumerate(checks):
                with cols[i]:
                    if ok: st.success(label)
                    else: st.error(label)
        confirmer = st.text_input("Confirmer le mot de passe", type="password", key="reg_confirm")
        pays_i = st.selectbox("🌍 Votre pays", ["Sélectionnez"] + PAYS, key="reg_pays")
        ville_i = st.text_input("🏙️ Votre ville", placeholder="ex: Dakar", key="reg_ville")
        if st.button("📝 Créer mon compte", use_container_width=True):
            if not email_i or not mdp_i:
                st.warning("⚠️ Remplissez tous les champs")
            elif mdp_i != confirmer:
                st.error("❌ Les mots de passe ne correspondent pas")
            elif pays_i == "Sélectionnez":
                st.error("❌ Sélectionnez votre pays")
            elif not ville_i:
                st.error("❌ Entrez votre ville")
            else:
                valide, msg = valider_mdp(mdp_i)
                if not valide:
                    st.error(f"❌ {msg}")
                else:
                    with st.spinner("Création du compte..."):
                        result = api_post("/inscription", {"email": email_i, "mot_de_passe": mdp_i, "pays": pays_i, "ville": ville_i})
                    if "erreur" in result:
                        st.error(f"❌ {result['erreur']}")
                    elif result.get("connexion_auto") or result.get("token"):
                        sauvegarder_session(email_i, pays_i, ville_i, result.get("token",""))
                        st.success("✅ Compte créé — Connexion automatique !")
                        st.rerun()
                    else:
                        st.success("✅ Compte créé !")
                        st.info(f"📧 Email de confirmation envoyé à **{email_i}**\n\n> Vérifiez aussi vos **spams**")

# ==============================
# Page Analyser
# ==============================
def page_analyser():
    st.title("🔍 Analyser un compte")

    st.markdown('<div class="ct-card">', unsafe_allow_html=True)
    st.markdown('<span class="ct-section-title">👤 Identité du compte</span>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        username_raw = st.text_input("Nom d'utilisateur *", placeholder="ex: staned_junior6")
    with col2:
        fullname_raw = st.text_input("Nom complet", placeholder="ex: Mr.Stan6")
    username = nettoyer(username_raw)
    fullname = nettoyer(fullname_raw)
    name_equals = 1 if username and fullname and username.lower().strip() == fullname.lower().strip() else 0
    if username and fullname:
        if name_equals:
            st.warning("⚠️ Nom complet identique au nom d'utilisateur — indicateur suspect")
        else:
            st.info("✅ Nom complet différent du nom d'utilisateur")
    profile_pic = st.selectbox("Photo de profil", options=[1,0], format_func=lambda x: "✅ Oui" if x==1 else "Non", key="profile_pic")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="ct-card">', unsafe_allow_html=True)
    st.markdown('<span class="ct-section-title">📊 Statistiques</span>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1: posts = st.number_input("Publications", min_value=0, max_value=100000, step=1)
    with col2: followers = st.number_input("Followers", min_value=0, max_value=10000000, step=1)
    with col3: follows = st.number_input("Abonnements", min_value=0, max_value=10000000, step=1)
    bio_len = st.number_input("Longueur de la bio", min_value=0, max_value=500, step=1)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="ct-card">', unsafe_allow_html=True)
    st.markdown('<span class="ct-section-title">⚙️ Paramètres</span>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        ext_url = st.selectbox("Lien externe dans la bio", options=[0,1], format_func=lambda x: "✅ Oui" if x==1 else "Non", key="ext_url")
    with col2:
        private = st.selectbox("Compte privé", options=[0,1], format_func=lambda x: "🔒 Oui" if x==1 else "🌐 Non", key="private")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🔍 Lancer l'analyse IA", use_container_width=True):
        if not username:
            st.warning("⚠️ Entrez un nom d'utilisateur")
        else:
            data = {
                "profile_pic": profile_pic, "username": username, "fullname": fullname,
                "name_equals_username": name_equals, "description_length": int(bio_len),
                "external_url": ext_url, "private": private,
                "posts": int(posts), "followers": int(followers), "follows": int(follows),
                "user_email": st.session_state.email,
                "user_pays": st.session_state.pays, "user_ville": st.session_state.ville
            }
            with st.spinner("⏳ Analyse IA en cours..."):
                result = api_post("/analyser", data)
            if "erreur" in result:
                st.error(f"❌ {result['erreur']}")
            else:
                # ✅ Sauvegarder dans cache personnel
                entree = {
                    "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "compte_analyse": result.get("compte_analyse",""),
                    "resultat": result.get("resultat",""),
                    "score_authenticite": result.get("score_authenticite", 0),
                    "score_suspicion": result.get("score_suspicion", 0),
                }
                email = st.session_state.email
                ajouter_au_cache(email, entree)
                sauvegarder_dernier(email, result)
                st.session_state.dernier_resultat = result
                if "historique_perso" not in st.session_state:
                    st.session_state.historique_perso = []
                st.session_state.historique_perso.insert(0, entree)

                st.markdown("---")
                st.markdown("### 📊 Résultat")

                if result.get("deja_analyse_par_user") and result.get("derniere_analyse"):
                    da = result["derniere_analyse"]
                    st.info(f"📌 Déjà analysé le {da['date']} — {da['resultat']}")

                nb = result.get("nb_analyses_total", 0)
                if nb:
                    st.markdown(f'<div style="display:inline-flex;align-items:center;gap:4px;background:rgba(59,130,246,0.1);border:0.5px solid rgba(59,130,246,0.25);border-radius:20px;padding:3px 10px;font-size:11px;color:#60a5fa;margin-bottom:1rem;">📊 Analysé <strong>{nb} fois</strong> sur CyberTrust Africa</div>', unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                auth = result["score_authenticite"]
                susp = result["score_suspicion"]
                with col1: st.metric("✅ Authenticité", f"{auth}%")
                with col2: st.metric("⚠️ Suspicion", f"{susp}%")

                st.markdown(f"""
                <div style="margin:0.75rem 0;">
                    <div style="display:flex;justify-content:space-between;font-size:11px;color:#6b7280;margin-bottom:6px;">
                        <span style="color:#10b981">Authentique</span><span style="color:#ef4444">Suspect</span>
                    </div>
                    <div style="height:6px;background:#1f2937;border-radius:3px;overflow:hidden;">
                        <div style="width:{susp}%;height:100%;background:linear-gradient(90deg,#10b981,#f59e0b,#ef4444);border-radius:3px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                nb_denon = result.get("nb_denonciations", 0)
                if nb_denon > 0:
                    types = result.get("types_arnaque", [])
                    st.error(f"🚨 **ALERTE — Dénoncé {nb_denon} fois !** Types : {', '.join(types)}")

                if auth >= 70:
                    st.success(f"✅ {result['resultat']}")
                    if not nb_denon: st.balloons()
                else:
                    st.error(f"🚨 {result['resultat']}")
                    sig = result.get("signalements_region", 0)
                    region = result.get("region_utilisateur", "")
                    if sig and region:
                        st.warning(f"📍 **{sig} compte(s) suspect(s)** dans votre région ({region})")
                    if susp >= 70:
                        st.markdown('<div class="ct-card-red">', unsafe_allow_html=True)
                        st.markdown('<span class="ct-section-title-red">⚠️ Recommandations</span>', unsafe_allow_html=True)
                        col1, col2, col3 = st.columns(3)
                        with col1: st.markdown("**🚫 Arrêter**\n- Cessez tout contact\n- Ne partagez rien")
                        with col2: st.markdown("**🔒 Bloquer**\n- Bloquez ce compte\n- Signalez la plateforme")
                        with col3: st.markdown("**📢 Signaler**\n- Dénoncez ici\n- Portez plainte")
                        st.markdown('</div>', unsafe_allow_html=True)

    # ✅ Dernier résultat persistant en bas
    dr = st.session_state.get("dernier_resultat")
    if not dr:
        cache = charger_cache(st.session_state.email)
        dr = cache.get("dernier_resultat")
        if dr:
            st.session_state.dernier_resultat = dr

    if dr and not username:
        st.markdown("---")
        st.markdown('<div style="font-size:11px;color:#6b7280;margin-bottom:8px;">🕘 Dernier résultat enregistré</div>', unsafe_allow_html=True)
        auth = dr.get("score_authenticite", 0)
        susp = dr.get("score_suspicion", 0)
        is_susp = "suspect" in dr.get("resultat","").lower()
        couleur = "rgba(239,68,68,0.3)" if is_susp else "rgba(16,185,129,0.3)"
        icon = "🚨" if is_susp else "✅"
        st.markdown(f"""
        <div style="background:#111827;border:0.5px solid {couleur};border-radius:14px;padding:1.25rem 1.5rem;">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;">
                <div style="font-size:15px;font-weight:500;color:#f9fafb;">{icon} @{dr.get('compte_analyse','')}</div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:1rem;">
                <div style="background:rgba(16,185,129,0.1);border:0.5px solid rgba(16,185,129,0.3);border-radius:10px;padding:12px;text-align:center;">
                    <div style="font-size:11px;color:#10b981;margin-bottom:4px;">✅ Authenticité</div>
                    <div style="font-size:26px;font-weight:600;color:#10b981;">{auth}%</div>
                </div>
                <div style="background:rgba(245,158,11,0.1);border:0.5px solid rgba(245,158,11,0.3);border-radius:10px;padding:12px;text-align:center;">
                    <div style="font-size:11px;color:#f59e0b;margin-bottom:4px;">⚠️ Suspicion</div>
                    <div style="font-size:26px;font-weight:600;color:#f59e0b;">{susp}%</div>
                </div>
            </div>
            <div style="height:6px;background:#1f2937;border-radius:3px;overflow:hidden;">
                <div style="width:{susp}%;height:100%;background:linear-gradient(90deg,#10b981,#f59e0b,#ef4444);border-radius:3px;"></div>
            </div>
            <div style="text-align:center;margin-top:1rem;font-size:14px;font-weight:500;color:{'#ef4444' if is_susp else '#10b981'};">
                {dr.get('resultat','')}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==============================
# Page Historique — Personnel par utilisateur
# ==============================
def page_historique():
    st.title("📊 Historique de mes analyses")
    st.markdown("---")

    email = st.session_state.get("email", "")

    # ✅ Charger historique personnel depuis cache JSON
    cache = charger_cache(email)
    historique_cache = cache.get("historique", [])

    # Fusionner avec session
    session_hist = st.session_state.get("historique_perso", [])
    cles_session = {a.get("compte_analyse","") + a.get("date","") for a in session_hist}
    for a in historique_cache:
        cle = a.get("compte_analyse","") + a.get("date","")
        if cle not in cles_session:
            session_hist.append(a)
    st.session_state.historique_perso = session_hist

    historique = session_hist
    total = len(historique)
    suspects = sum(1 for a in historique if "suspect" in a.get("resultat","").lower())
    authentiques = total - suspects

    col1, col2, col3 = st.columns(3)
    with col1: st.metric("📊 Total", total)
    with col2: st.metric("✅ Authentiques", authentiques)
    with col3: st.metric("🚨 Suspects", suspects)

    if total == 0:
        st.markdown("""
        <div style="text-align:center;padding:3rem 1rem;">
            <div style="font-size:40px;margin-bottom:1rem;">🔍</div>
            <div style="font-size:14px;color:#4b5563;">Aucune analyse effectuée.<br>Allez sur <b>🔍 Analyser</b> pour commencer !</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("---")
        filtre = st.radio("Filtrer", ["Tous", "🚨 Suspects", "✅ Authentiques"], horizontal=True)
        nb = 0
        for a in historique:
            resultat = a.get("resultat","")
            is_susp = "suspect" in resultat.lower()
            if filtre == "🚨 Suspects" and not is_susp: continue
            if filtre == "✅ Authentiques" and is_susp: continue
            nb += 1
            type_class = "suspect" if is_susp else "authentique"
            icon = "🚨" if is_susp else "✅"
            auth = a.get("score_authenticite", 0)
            susp = a.get("score_suspicion", 0)
            bar_color = "#ef4444" if is_susp else "#10b981"
            st.markdown(f"""
            <div class="ct-hist-item {type_class}">
                <div style="flex:1;">
                    <div style="font-size:14px;font-weight:500;color:#f9fafb;">{icon} @{a.get('compte_analyse','')}</div>
                    <div style="font-size:11px;color:#6b7280;margin-top:2px;">{a.get('date','')}</div>
                    <div style="height:3px;background:#1f2937;border-radius:2px;margin-top:6px;overflow:hidden;">
                        <div style="width:{susp}%;height:100%;background:{bar_color};border-radius:2px;"></div>
                    </div>
                </div>
                <div style="text-align:right;margin-left:12px;">
                    <div style="font-size:12px;color:#10b981;font-weight:500;">Auth: {auth}%</div>
                    <div style="font-size:12px;color:#f59e0b;font-weight:500;">Susp: {susp}%</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        if nb == 0:
            st.info("Aucune analyse dans cette catégorie")

        # ✅ Bouton pour effacer l'historique personnel
        st.markdown("---")
        if st.button("🗑️ Effacer mon historique", use_container_width=True):
            cache = charger_cache(email)
            cache["historique"] = []
            sauvegarder_cache(email, cache)
            st.session_state.historique_perso = []
            st.success("✅ Historique effacé")
            st.rerun()

# ==============================
# Page Dénoncer
# ==============================
def page_denoncer():
    st.title("🚨 Dénoncer un cybercriminel")
    st.markdown("---")

    try:
        hist = api_get("/historique/denonciations", params={"email": st.session_state.email})
        if hist.get("total", 0) > 0:
            st.markdown('<div class="ct-card-red">', unsafe_allow_html=True)
            st.markdown('<span class="ct-section-title-red">📋 Vos dénonciations du mois</span>', unsafe_allow_html=True)
            st.caption("⚠️ Cet historique se supprime automatiquement après 30 jours")
            for d in reversed(hist.get("denonciations",[])):
                icon = "✅" if d["statut"] == "valide" else "⏳"
                st.markdown(f"{icon} **@{d['compte_denonce']}** — {d['type_arnaque']} — {d['date']}")
            st.markdown('</div>', unsafe_allow_html=True)
    except Exception:
        pass

    st.warning("⚠️ Réservé aux vraies victimes. Toute fausse dénonciation est une infraction grave. Si validée, publiée sur les **pages officielles de Cyber Africa Culture** 🌍")
    st.markdown("---")

    st.markdown('<div class="ct-card-red">', unsafe_allow_html=True)
    st.markdown('<span class="ct-section-title-red">👤 Identifier le compte</span>', unsafe_allow_html=True)
    compte_denonce = st.text_input("Nom du compte suspect *", placeholder="ex: fake_account123")
    plateforme = st.selectbox("Plateforme *", ["Sélectionnez","Instagram","Facebook","TikTok","Twitter/X","WhatsApp","Telegram","Snapchat","LinkedIn","Autre"])

    st.markdown('<span class="ct-section-title-red" style="margin-top:1rem;">🎭 Type d\'arnaque *</span>', unsafe_allow_html=True)
    types_options = ["💰 Arnaque financière","😡 Harcèlement","🔒 Extorsion","🎭 Usurpation d'identité","💔 Faux profil romantique","🛍️ Escroquerie vente","🔗 Phishing","❓ Autre"]
    cols = st.columns(4)
    for i, t in enumerate(types_options):
        with cols[i % 4]:
            if st.button(t, key=f"type_{i}", use_container_width=True):
                if t in st.session_state.selected_types:
                    st.session_state.selected_types.remove(t)
                else:
                    st.session_state.selected_types.append(t)
    if st.session_state.selected_types:
        st.success(f"✅ Sélectionnés : {', '.join(st.session_state.selected_types)}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="ct-card-red">', unsafe_allow_html=True)
    st.markdown('<span class="ct-section-title-red">📝 Description</span>', unsafe_allow_html=True)
    description = st.text_area("Décrivez ce qui s'est passé * (min. 50 caractères)", height=130)
    if description:
        nb = len(description)
        if nb < 50: st.error(f"❌ {nb}/50 minimum")
        elif nb < 100: st.warning(f"⚠️ {nb} caractères — plus de détails")
        else: st.success(f"✅ {nb} caractères")

    montant = 0
    if "💰 Arnaque financière" in st.session_state.selected_types:
        montant = st.number_input("Montant escroqué", min_value=0, step=1000)

    col1, col2 = st.columns(2)
    with col1: date_incident = st.date_input("Date de l'incident *")
    with col2: pays_victime = st.selectbox("Votre pays *", ["Sélectionnez"] + PAYS, key="denonce_pays")
    ville_victime = st.text_input("Votre ville *", key="denonce_ville")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="ct-card">', unsafe_allow_html=True)
    st.markdown('<span class="ct-section-title">✅ Vérification</span>', unsafe_allow_html=True)
    q1 = st.radio("Avez-vous effectué une transaction ?", ["Oui","Non","Je préfère ne pas répondre"])
    q2 = st.radio("Avez-vous des preuves ?", ["Oui, j'ai des preuves","Non, je n'ai pas de preuves","J'ai quelques éléments"])
    q5 = st.checkbox("Je certifie sur l'honneur que les informations sont véridiques")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🚨 Soumettre la dénonciation", use_container_width=True, type="primary"):
        erreurs = []
        if not compte_denonce: erreurs.append("Nom du compte obligatoire")
        if plateforme == "Sélectionnez": erreurs.append("Sélectionnez la plateforme")
        if not st.session_state.selected_types: erreurs.append("Sélectionnez un type d'arnaque")
        if len(description) < 50: erreurs.append("Description trop courte")
        if pays_victime == "Sélectionnez": erreurs.append("Sélectionnez votre pays")
        if not ville_victime: erreurs.append("Entrez votre ville")
        if not q5: erreurs.append("Certifiez les informations")
        if q2 == "Non, je n'ai pas de preuves" and q1 == "Non": erreurs.append("Signalement insuffisant")
        if erreurs:
            for e in erreurs: st.error(f"❌ {e}")
        else:
            type_str = ", ".join([t.split(" ",1)[1] for t in st.session_state.selected_types])
            data = {
                "compte_denonce": nettoyer(compte_denonce), "plateforme": plateforme,
                "type_arnaque": type_str, "description": nettoyer(description),
                "montant_escroqué": montant, "date_incident": str(date_incident),
                "pays_victime": pays_victime, "ville_victime": nettoyer(ville_victime),
                "user_email": st.session_state.email
            }
            with st.spinner("Envoi..."):
                result = api_post("/denoncer", data)
            if "erreur" in result:
                st.error(f"❌ {result['erreur']}")
            else:
                st.session_state.selected_types = []
                st.success(f"✅ {result['message']}")
                st.info(f"📊 Score de fiabilité : **{result['score_fiabilite']}/100**")
                st.markdown("**Si validée**, publiée sur les **pages officielles de Cyber Africa Culture** 🌍")
                if result.get("statut") == "valide": st.balloons()

# ==============================
# Page Carte
# ==============================
def page_carte():
    st.title("🗺️ Carte des signalements")
    st.markdown("---")
    with st.spinner("Chargement..."):
        result = api_get("/carte/stats")
    if "erreur" in result:
        st.error(f"❌ {result['erreur']}")
        return
    stats = result.get("stats", [])
    if not stats:
        st.warning("Aucune donnée disponible")
        return

    col1, col2 = st.columns(2)
    with col1: st.metric("🚨 Comptes suspects", sum(s.get("comptes_suspects",0) for s in stats))
    with col2: st.metric("📢 Dénonciations", sum(s.get("denonciations",0) for s in stats))

    col1, col2, col3 = st.columns(3)
    with col1: st.markdown('<span style="color:#10b981;font-size:12px;">● Faible</span>', unsafe_allow_html=True)
    with col2: st.markdown('<span style="color:#f59e0b;font-size:12px;">● Modéré</span>', unsafe_allow_html=True)
    with col3: st.markdown('<span style="color:#ef4444;font-size:12px;">● Élevé</span>', unsafe_allow_html=True)

    m = creer_carte(stats)
    st_folium(m, width=700, height=450)

    st.markdown("---")
    st.markdown('<div class="ct-card">', unsafe_allow_html=True)
    st.markdown('<span class="ct-section-title">🏆 Top pays</span>', unsafe_allow_html=True)
    df = pd.DataFrame(stats)
    df["total"] = df["comptes_suspects"] + df["denonciations"]
    df = df[df["total"]>0].sort_values("total", ascending=False).head(10)
    if not df.empty:
        max_val = df["total"].max()
        for i, row in df.iterrows():
            pct = int(row["total"]/max_val*100) if max_val else 0
            c = "#ef4444" if row["total"]>=6 else "#f59e0b" if row["total"]>=3 else "#10b981"
            rank = list(df.index).index(i)+1
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:0.5px solid rgba(255,255,255,0.04);">
                <span style="font-size:12px;color:#4b5563;width:20px;">{rank}</span>
                <span style="font-size:13px;color:#f9fafb;flex:1;">🌍 {row['pays']}</span>
                <div style="flex:2;background:#1f2937;height:4px;border-radius:2px;overflow:hidden;">
                    <div style="width:{pct}%;height:100%;background:{c};border-radius:2px;"></div>
                </div>
                <span style="font-size:12px;font-weight:500;color:{c};min-width:30px;text-align:right;">{int(row['total'])}</span>
            </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# Page Admin
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
            st.error(f"❌ Mot de passe incorrect — {r} tentative(s)" if r > 0 else "🚨 Accès bloqué")

def page_admin_dashboard():
    st.title("🔐 Dashboard Administrateur")
    col1, col2 = st.columns([4,1])
    with col2:
        if st.button("🚪 Déco. Admin", key="admin_logout_btn", use_container_width=True):
            st.session_state.admin_connecte = False
            st.rerun()

    headers = {"X-Admin-Key": ADMIN_KEY}
    tabs = st.tabs(["📊 Analyses","👥 Utilisateurs","📍 Régional","🚨 Dénonciations","🗺️ Carte","⬇️ Télécharger"])

    with tabs[0]:
        st.markdown("### 📊 Toutes les analyses")
        result = api_get("/admin/collecte", headers=headers)
        if "erreur" in result: st.error(f"❌ {result['erreur']}")
        else:
            total = result.get("total",0)
            donnees = result.get("donnees",[])
            suspects = sum(1 for d in donnees if "suspect" in d.get("resultat","").lower())
            col1,col2,col3 = st.columns(3)
            with col1: st.metric("Total",total)
            with col2: st.metric("✅ Authentiques",total-suspects)
            with col3: st.metric("🚨 Suspects",suspects)
            if donnees:
                st.markdown("---")
                search = st.text_input("🔍 Rechercher", key="admin_search")
                df = pd.DataFrame(donnees)
                if search:
                    df = df[df["compte_analyse"].str.contains(search, case=False, na=False)]
                df = df.rename(columns={"date":"Date","user_email":"Email","user_pays":"Pays","user_ville":"Ville","compte_analyse":"Compte","resultat":"Résultat","score_authenticite":"Auth%","score_suspicion":"Susp%"})
                st.dataframe(df[["Date","Email","Pays","Ville","Compte","Résultat","Auth%","Susp%"]], use_container_width=True)
            else:
                st.info("Aucune analyse enregistrée")

    with tabs[1]:
        st.markdown("### 👥 Utilisateurs inscrits")
        result = api_get("/admin/utilisateurs", headers=headers)
        if "erreur" in result: st.error(f"❌ {result['erreur']}")
        else:
            st.info(f"Total : **{result.get('total',0)}**")
            if result.get("utilisateurs"):
                df = pd.DataFrame(result["utilisateurs"])
                df = df.rename(columns={"email":"Email","date_inscription":"Inscription","pays":"Pays","ville":"Ville","email_verifie":"Vérifié"})
                st.dataframe(df, use_container_width=True)

    with tabs[2]:
        st.markdown("### 📍 Signalements régionaux")
        result = api_get("/admin/regional", headers=headers)
        if "erreur" in result: st.error(f"❌ {result['erreur']}")
        else:
            st.info(f"Suspects uniques : **{result.get('total_signalements',0)}**")
            col1,col2 = st.columns(2)
            with col1:
                if result.get("top_pays"):
                    df = pd.DataFrame(result["top_pays"])
                    df.columns = ["Pays","Signalements"]
                    st.dataframe(df, use_container_width=True)
            with col2:
                if result.get("top_villes"):
                    df = pd.DataFrame(result["top_villes"])
                    df.columns = ["Ville","Signalements"]
                    st.dataframe(df, use_container_width=True)

    with tabs[3]:
        st.markdown("### 🚨 Dénonciations")
        result = api_get("/admin/denonciations", headers=headers)
        if "erreur" in result: st.error(f"❌ {result['erreur']}")
        else:
            col1,col2,col3 = st.columns(3)
            with col1: st.metric("Total",result.get("total",0))
            with col2: st.metric("✅ Validées",result.get("valides",0))
            with col3: st.metric("⏳ En vérif.",result.get("en_verification",0))
            if result.get("denonciations"):
                st.dataframe(pd.DataFrame(result["denonciations"]), use_container_width=True)

    with tabs[4]:
        st.markdown("### 🗺️ Carte Admin")
        result = api_get("/carte/stats")
        if result.get("stats"):
            m = creer_carte(result["stats"])
            st_folium(m, width=700, height=400)
            df = pd.DataFrame(result["stats"])
            st.download_button("⬇️ Télécharger données carte", df.to_csv(index=False), "carte.csv", "text/csv", use_container_width=True)

    with tabs[5]:
        st.markdown("### ⬇️ Télécharger")
        r1 = api_get("/admin/collecte", headers=headers)
        if r1.get("donnees"): st.download_button("⬇️ Analyses", pd.DataFrame(r1["donnees"]).to_csv(index=False), "analyses.csv", "text/csv", use_container_width=True)
        r2 = api_get("/admin/utilisateurs", headers=headers)
        if r2.get("utilisateurs"): st.download_button("⬇️ Utilisateurs", pd.DataFrame(r2["utilisateurs"]).to_csv(index=False), "utilisateurs.csv", "text/csv", use_container_width=True)
        r3 = api_get("/admin/regional", headers=headers)
        if r3.get("donnees"): st.download_button("⬇️ Régional", pd.DataFrame(r3["donnees"]).to_csv(index=False), "regional.csv", "text/csv", use_container_width=True)
        r4 = api_get("/admin/denonciations", headers=headers)
        if r4.get("denonciations"): st.download_button("⬇️ Dénonciations", pd.DataFrame(r4["denonciations"]).to_csv(index=False), "denonciations.csv", "text/csv", use_container_width=True)

# ==============================
# Page Principale — Navigation fixe en haut
# ==============================
def page_principale():
    # ✅ Barre de navigation toujours visible en haut
    st.markdown(f"""
    <div style="background:#111827;border:0.5px solid rgba(245,158,11,0.2);border-radius:12px;
                padding:10px 16px;margin-bottom:1rem;display:flex;align-items:center;justify-content:space-between;">
        <div>
            <div style="font-size:13px;color:#f59e0b;font-weight:500;">👤 {st.session_state.email}</div>
            <div style="font-size:11px;color:#6b7280;">📍 {st.session_state.ville}, {st.session_state.pays}</div>
        </div>
        <div style="font-size:20px;">🌍</div>
    </div>
    """, unsafe_allow_html=True)

    # ✅ 5 boutons de navigation toujours visibles
    nav_cols = st.columns(5)
    nav_items = [
        ("analyser", "🔍 Analyser"),
        ("denoncer", "🚨 Dénoncer"),
        ("carte", "🗺️ Carte"),
        ("historique", "📊 Historique"),
        ("admin", "🔐 Admin"),
    ]
    for i, (page_id, label) in enumerate(nav_items):
        with nav_cols[i]:
            is_active = st.session_state.page_active == page_id
            if is_active:
                st.markdown(f"""
                <div style="background:rgba(245,158,11,0.15);border:0.5px solid rgba(245,158,11,0.4);
                            border-radius:8px;padding:8px 4px;text-align:center;font-size:12px;
                            color:#f59e0b;font-weight:500;cursor:pointer;">
                    {label}
                </div>
                """, unsafe_allow_html=True)
            if st.button(label, key=f"nav_btn_{page_id}", use_container_width=True):
                st.session_state.page_active = page_id
                st.rerun()

    # ✅ Bouton déconnexion
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🚪 Déco.", key="main_logout_btn", use_container_width=True):
            effacer_session()
            st.rerun()

    st.markdown("---")

    # ✅ Afficher la page active
    page = st.session_state.page_active
    if page == "analyser": page_analyser()
    elif page == "denoncer": page_denoncer()
    elif page == "carte": page_carte()
    elif page == "historique": page_historique()
    elif page == "admin":
        if st.session_state.admin_connecte: page_admin_dashboard()
        else: page_admin_login()

# ==============================
# Main
# ==============================
if st.session_state.connecte:
    page_principale()
else:
    page_auth()