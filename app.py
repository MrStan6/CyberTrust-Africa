# ==============================
# CyberTrust Africa — v6.4
# Design Complet Africain Dark Mode
# ==============================

import streamlit as st
import requests
import re
import os
import pandas as pd
import folium
from streamlit_folium import st_folium
import pycountry
from datetime import datetime, timedelta

import json
import hashlib
import os

CACHE_DIR = ".ct_cache"

def _get_cache_file(email):
    """Retourne le chemin du fichier cache pour un email"""
    if not email:
        return None
    os.makedirs(CACHE_DIR, exist_ok=True)
    h = hashlib.md5(email.strip().lower().encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{h}.json")

def charger_cache_utilisateur(email):
    """Charge le cache JSON de l'utilisateur"""
    path = _get_cache_file(email)
    if not path or not os.path.exists(path):
        return {"historique": [], "dernier_resultat": None}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"historique": [], "dernier_resultat": None}

def sauvegarder_cache_utilisateur(email, data):
    """Sauvegarde le cache JSON de l'utilisateur"""
    path = _get_cache_file(email)
    if not path:
        return
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def ajouter_analyse_cache(email, analyse):
    """Ajoute une analyse au cache et limite à 100 entrées"""
    cache = charger_cache_utilisateur(email)
    historique = cache.get("historique", [])
    # Éviter doublons consécutifs
    if not historique or historique[0].get("compte_analyse") != analyse.get("compte_analyse"):
        historique.insert(0, analyse)
    cache["historique"] = historique[:100]  # Garder 100 max
    sauvegarder_cache_utilisateur(email, cache)

def sauvegarder_dernier_resultat_cache(email, resultat):
    """Sauvegarde le dernier résultat dans le cache"""
    cache = charger_cache_utilisateur(email)
    cache["dernier_resultat"] = resultat
    sauvegarder_cache_utilisateur(email, cache)

API_URL = os.getenv("API_URL", "http://127.0.0.1:5000")
ADMIN_KEY = os.getenv("ADMIN_KEY", "cybertrust_admin_2026_secure")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "CyberTrust@Admin2026!")
SESSION_TIMEOUT_HEURES = 24

st.set_page_config(
    page_title="CyberTrust Africa",
    page_icon="🌍",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ==============================
# CSS Design Complet
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
    [data-testid="stSidebar"] .stRadio label { font-size: 14px !important; }

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
        font-size: 14px !important;
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
        font-size: 14px !important;
        padding: 10px 20px !important;
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
        color: #ffffff !important;
    }
    .stButton > button[kind="secondary"] {
        background: #1f2937 !important;
        color: #ffffff !important;
        border: 0.5px solid rgba(255,255,255,0.1) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        background: #0a0a0f !important;
        border-radius: 10px !important;
        padding: 4px !important;
        gap: 4px !important;
        border-bottom: none !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border-radius: 8px !important;
        color: #6b7280 !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        border: none !important;
        padding: 8px 16px !important;
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
    [data-testid="stMetricLabel"] { color: #9ca3af !important; font-size: 12px !important; }
    [data-testid="stMetricValue"] { color: #f59e0b !important; font-size: 1.8rem !important; font-weight: 600 !important; }

    .stSuccess { background: rgba(16,185,129,0.1) !important; border: 0.5px solid rgba(16,185,129,0.3) !important; border-radius: 8px !important; color: #10b981 !important; }
    .stError { background: rgba(239,68,68,0.1) !important; border: 0.5px solid rgba(239,68,68,0.3) !important; border-radius: 8px !important; color: #ef4444 !important; }
    .stWarning { background: rgba(245,158,11,0.1) !important; border: 0.5px solid rgba(245,158,11,0.3) !important; border-radius: 8px !important; color: #f59e0b !important; }
    .stInfo { background: rgba(59,130,246,0.1) !important; border: 0.5px solid rgba(59,130,246,0.3) !important; border-radius: 8px !important; color: #60a5fa !important; }

    .stDataFrame { border: 0.5px solid rgba(245,158,11,0.15) !important; border-radius: 8px !important; overflow: hidden !important; }
    .stCheckbox > label { color: #9ca3af !important; font-size: 13px !important; }
    .stRadio > div > label { color: #9ca3af !important; font-size: 14px !important; }
    .stCaption { color: #6b7280 !important; font-size: 12px !important; }
    .stDownloadButton > button { background: rgba(16,185,129,0.1) !important; border: 0.5px solid rgba(16,185,129,0.3) !important; color: #10b981 !important; }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    hr { border-color: rgba(245,158,11,0.15) !important; }

    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: #0a0a0f; }
    ::-webkit-scrollbar-thumb { background: rgba(245,158,11,0.3); border-radius: 2px; }

    /* ✅ Cacher complètement la sidebar Streamlit */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }

    /* ✅ Navigation fixe en bas */
    .ct-bottom-nav {
        position: fixed;
        bottom: 0; left: 0; right: 0;
        background: #111827;
        border-top: 0.5px solid rgba(245,158,11,0.2);
        display: flex;
        z-index: 9999;
        padding: 6px 0 8px;
    }
    .ct-nav-item {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
        padding: 6px 4px;
        cursor: pointer;
        border-radius: 8px;
        margin: 0 3px;
        transition: all 0.15s;
        text-decoration: none;
        border: none;
        background: transparent;
    }
    .ct-nav-item:hover { background: rgba(245,158,11,0.08); }
    .ct-nav-item.active { background: rgba(245,158,11,0.12); }
    .ct-nav-icon { font-size: 18px; line-height: 1; }
    .ct-nav-label {
        font-size: 10px;
        font-family: var(--font-sans);
        color: #6b7280;
        font-weight: 500;
    }
    .ct-nav-item.active .ct-nav-label { color: #f59e0b; }

    /* ✅ Espace en bas pour ne pas cacher le contenu */
    .main .block-container { padding-bottom: 90px !important; }

    /* ✅ User info bar en haut */
    .ct-top-bar {
        background: #111827;
        border-bottom: 0.5px solid rgba(245,158,11,0.15);
        padding: 10px 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
        border-radius: 12px;
    }
    .ct-top-bar-email {
        font-size: 13px;
        font-weight: 500;
        color: #f59e0b;
    }
    .ct-top-bar-location {
        font-size: 11px;
        color: #6b7280;
        margin-top: 2px;
    }
    .ct-logout-btn {
        background: rgba(239,68,68,0.1);
        border: 0.5px solid rgba(239,68,68,0.3);
        border-radius: 8px;
        padding: 5px 12px;
        font-size: 12px;
        color: #ef4444 !important;
        cursor: pointer;
        font-family: var(--font-sans);
        font-weight: 500;
    }

    /* Composants custom */
    .ct-badge-secure {
        display: inline-flex; align-items: center; gap: 6px;
        background: rgba(16,185,129,0.1); border: 0.5px solid rgba(16,185,129,0.3);
        border-radius: 20px; padding: 4px 12px; font-size: 12px; color: #10b981;
    }
    .ct-card {
        background: #111827; border: 0.5px solid rgba(245,158,11,0.15);
        border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem;
    }
    .ct-card-red {
        background: #111827; border: 0.5px solid rgba(239,68,68,0.15);
        border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem;
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
        border-left: 3px solid transparent;
    }
    .ct-hist-item.suspect { border-left-color: #ef4444; border: 0.5px solid rgba(239,68,68,0.15); border-left: 3px solid #ef4444; }
    .ct-hist-item.authentique { border-left-color: #10b981; border: 0.5px solid rgba(16,185,129,0.15); border-left: 3px solid #10b981; }
    .ct-progress-wrap { margin: 0.75rem 0; }
    .ct-progress-bar-bg { height: 6px; background: #1f2937; border-radius: 3px; overflow: hidden; }
    .ct-country-row {
        display: flex; align-items: center; gap: 10px;
        padding: 8px 0; border-bottom: 0.5px solid rgba(255,255,255,0.04);
    }
    </style>
    """, unsafe_allow_html=True)

inject_css()


# ==============================
# Persistance session via st.query_params
# ==============================
def get_session_param(key, default=""):
    try:
        params = st.query_params
        val = params.get(key, default)
        return val if val else default
    except Exception:
        return default

def sauvegarder_params_session(email, pays, ville, token):
    """Sauvegarde session dans query_params ET session_state"""
    try:
        st.query_params["ct_email"] = email
        st.query_params["ct_pays"] = pays
        st.query_params["ct_ville"] = ville
        st.query_params["ct_token"] = token
        st.query_params["ct_connecte"] = "true"
    except Exception:
        pass

def effacer_params_session():
    """Efface les query_params de session"""
    try:
        for k in ["ct_email", "ct_pays", "ct_ville", "ct_token", "ct_connecte"]:
            if k in st.query_params:
                del st.query_params[k]
    except Exception:
        pass

# Fonctions alias pour compatibilité
def get_cookie(key, default=""):
    mapping = {
        "connecte": "ct_connecte",
        "email": "ct_email",
        "pays": "ct_pays",
        "ville": "ct_ville",
        "jwt_token": "ct_token",
        "heure_connexion": "ct_heure"
    }
    mapped_key = mapping.get(key, key)
    return get_session_param(mapped_key, default)

def set_cookie(key, value, expires_at=None):
    mapping = {
        "connecte": "ct_connecte",
        "email": "ct_email",
        "pays": "ct_pays",
        "ville": "ct_ville",
        "jwt_token": "ct_token",
        "heure_connexion": "ct_heure"
    }
    mapped_key = mapping.get(key, key)
    try:
        st.query_params[mapped_key] = value
    except Exception:
        pass

def delete_cookie(key):
    mapping = {
        "connecte": "ct_connecte",
        "email": "ct_email",
        "pays": "ct_pays",
        "ville": "ct_ville",
        "jwt_token": "ct_token",
        "heure_connexion": "ct_heure"
    }
    mapped_key = mapping.get(key, key)
    try:
        if mapped_key in st.query_params:
            del st.query_params[mapped_key]
    except Exception:
        pass

def verifier_jwt(token):
    try:
        if not token:
            return None
        r = requests.post(f"{API_URL}/verifier-token", json={"token": token}, timeout=5)
        if r.status_code == 200 and r.text.strip():
            return r.json()
        return None
    except Exception:
        return None

# ==============================
# Session — Restauration depuis query_params
# ✅ query_params persistent dans l'URL → survivent aux actualisations
# ==============================
if "connecte" not in st.session_state:
    params = st.query_params
    qp_connecte = params.get("ct_connecte", "")
    qp_email = params.get("ct_email", "")
    qp_token = params.get("ct_token", "")
    qp_pays = params.get("ct_pays", "")
    qp_ville = params.get("ct_ville", "")

    if qp_connecte == "true" and qp_email and qp_token:
        # ✅ Restauration depuis URL — persiste à l'actualisation
        st.session_state.connecte = True
        st.session_state.email = qp_email
        st.session_state.pays = qp_pays
        st.session_state.ville = qp_ville
        st.session_state.jwt_token = qp_token
    else:
        st.session_state.connecte = False
        st.session_state.email = ""
        st.session_state.pays = ""
        st.session_state.ville = ""
        st.session_state.jwt_token = ""

if "historique_session" not in st.session_state:
    # ✅ Charger depuis cache JSON local si email dispo
    _email_cache = st.query_params.get("ct_email", "")
    if _email_cache:
        _cache = charger_cache_utilisateur(_email_cache)
        st.session_state.historique_session = _cache.get("historique", [])
    else:
        st.session_state.historique_session = []

if "dernier_resultat" not in st.session_state:
    # ✅ Restaurer depuis cache JSON local
    try:
        _email_cache = st.query_params.get("ct_email", "")
        if _email_cache:
            _cache = charger_cache_utilisateur(_email_cache)
            st.session_state.dernier_resultat = _cache.get("dernier_resultat", None)
        else:
            st.session_state.dernier_resultat = None
    except Exception:
        st.session_state.dernier_resultat = None
if "admin_connecte" not in st.session_state:
    st.session_state.admin_connecte = False
if "tentatives_admin" not in st.session_state:
    st.session_state.tentatives_admin = 0

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
    for c in ["'", '"', ";", "--", "/*", "*/", "xp_", "DROP", "SELECT", "INSERT", "DELETE", "UPDATE", "UNION", "EXEC"]:
        texte = texte.replace(c, "")
    return texte[:500].strip()

def valider_mot_de_passe(mdp):
    if len(mdp) < 12: return False, "Le mot de passe doit contenir au moins 12 caractères"
    if not any(c.isupper() for c in mdp): return False, "Le mot de passe doit contenir au moins une majuscule"
    if not any(c.islower() for c in mdp): return False, "Le mot de passe doit contenir au moins une minuscule"
    if not any(c.isdigit() for c in mdp): return False, "Le mot de passe doit contenir au moins un chiffre"
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in mdp): return False, "Le mot de passe doit contenir au moins un symbole"
    return True, "OK"

def inscrire(email, mdp, pays, ville):
    return _safe_api_call(
        lambda: requests.post(f"{API_URL}/inscription",
                              json={"email": email, "mot_de_passe": mdp, "pays": pays, "ville": ville}, timeout=10)
    )

def connecter(email, mdp):
    return _safe_api_call(
        lambda: requests.post(f"{API_URL}/connexion", json={"email": email, "mot_de_passe": mdp}, timeout=10)
    )

def renvoyer_verification(email):
    return _safe_api_call(
        lambda: requests.post(f"{API_URL}/renvoyer-verification", json={"email": email}, timeout=10)
    )

def get_historique():
    email = st.session_state.get("email", "").strip()
    if not email:
        return {"total_analyses": 0, "historique": []}
    return _safe_api_call(
        lambda: requests.get(f"{API_URL}/historique", params={"email": email}, timeout=10)
    )

def get_historique_denonciations():
    email = st.session_state.get("email", "").strip()
    if not email:
        return {"total": 0, "denonciations": []}
    return _safe_api_call(
        lambda: requests.get(f"{API_URL}/historique/denonciations", params={"email": email}, timeout=10)
    )

def get_carte_stats():
    return _safe_api_call(
        lambda: requests.get(f"{API_URL}/carte/stats", timeout=10)
    )

def _safe_api_call(func):
    """Wrapper pour gérer les erreurs API proprement"""
    try:
        result = func()
        if result.status_code == 200:
            return result.json()
        else:
            return {"erreur": f"Erreur API {result.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"erreur": "❌ API Flask non démarrée — lancez python api.py"}
    except Exception as e:
        return {"erreur": f"Erreur : {str(e)}"}

def get_admin_collecte():
    return _safe_api_call(
        lambda: requests.get(f"{API_URL}/admin/collecte", headers={"X-Admin-Key": ADMIN_KEY}, timeout=10)
    )

def get_admin_utilisateurs():
    return _safe_api_call(
        lambda: requests.get(f"{API_URL}/admin/utilisateurs", headers={"X-Admin-Key": ADMIN_KEY}, timeout=10)
    )

def get_admin_regional():
    return _safe_api_call(
        lambda: requests.get(f"{API_URL}/admin/regional", headers={"X-Admin-Key": ADMIN_KEY}, timeout=10)
    )

def get_admin_denonciations():
    return _safe_api_call(
        lambda: requests.get(f"{API_URL}/admin/denonciations", headers={"X-Admin-Key": ADMIN_KEY}, timeout=10)
    )

def soumettre_denonciation(data):
    return _safe_api_call(
        lambda: requests.post(f"{API_URL}/denoncer", json=data, timeout=10)
    )

def creer_carte(stats):
    m = folium.Map(location=[20, 10], zoom_start=2, tiles="CartoDB dark_matter")
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
            couleur = "#ef4444" if total >= 5 else "#f59e0b" if total >= 2 else "#10b981"
            folium.CircleMarker(
                location=coords, radius=max(8, total * 3),
                color=couleur, fill=True, fill_color=couleur, fill_opacity=0.8,
                popup=folium.Popup(f"<b style='color:#f59e0b'>🌍 {pays}</b><br>🚨 {suspects} suspect(s)<br>📢 {denonciations} dénonciation(s)", max_width=200),
                tooltip=f"{pays}: {suspects} suspects | {denonciations} dénonciations"
            ).add_to(m)
    return m

def sauvegarder_session(email, pays, ville, token):
    st.session_state.connecte = True
    st.session_state.email = email
    st.session_state.pays = pays
    st.session_state.ville = ville
    st.session_state.jwt_token = token
    # ✅ Sauvegarde dans query_params pour persistance à l'actualisation
    try:
        st.query_params["ct_connecte"] = "true"
        st.query_params["ct_email"] = email
        st.query_params["ct_pays"] = pays
        st.query_params["ct_ville"] = ville
        st.query_params["ct_token"] = token
        st.query_params["ct_heure"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    except Exception:
        pass

def effacer_session():
    st.session_state.connecte = False
    st.session_state.email = ""
    st.session_state.pays = ""
    st.session_state.ville = ""
    st.session_state.jwt_token = ""
    st.session_state.dernier_resultat = None
    st.session_state.admin_connecte = False
    # ✅ Efface tous les query_params
    try:
        all_keys = ["ct_connecte","ct_email","ct_pays","ct_ville","ct_token","ct_heure",
                    "ct_last_compte","ct_last_auth","ct_last_susp","ct_last_resultat","ct_last_nb"]
        for k in all_keys:
            if k in st.query_params:
                del st.query_params[k]
    except Exception:
        pass

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
            Système sécurisé — v6.4
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    onglet1, onglet2 = st.tabs(["🔑 Connexion", "📝 Inscription"])

    with onglet1:
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
                    if result.get("email_non_verifie"):
                        st.warning("📧 Vérifiez votre boîte mail")
                        if st.button("📨 Renvoyer l'email", use_container_width=True):
                            r = renvoyer_verification(email)
                            st.success("✅ Email renvoyé") if "erreur" not in r else st.error(f"❌ {r['erreur']}")
                else:
                    sauvegarder_session(email, result.get("pays", ""), result.get("ville", ""), result.get("token", ""))
                    st.success("✅ Connexion réussie !")
                    st.rerun()
            else:
                st.warning("⚠️ Remplissez tous les champs")

    with onglet2:
        email_i = st.text_input("Email", placeholder="votre@email.com", key="register_email")
        mdp_i = st.text_input("Mot de passe", type="password", key="register_password")
        if mdp_i:
            ind = st.columns(5)
            checks = [(len(mdp_i)>=12,"12+"), (any(c.isupper() for c in mdp_i),"Maj."), (any(c.islower() for c in mdp_i),"Min."), (any(c.isdigit() for c in mdp_i),"Chiff."), (any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in mdp_i),"Symb.")]
            for i,(ok,label) in enumerate(checks):
                with ind[i]:
                    if ok: st.success(label)
                    else: st.error(label)
        confirmer = st.text_input("Confirmer le mot de passe", type="password", key="confirm_password")
        pays_i = st.selectbox("🌍 Votre pays", ["Sélectionnez votre pays"] + PAYS, key="register_pays")
        ville_i = st.text_input("🏙️ Votre ville", placeholder="ex: Dakar", key="register_ville")
        if st.button("📝 Créer mon compte", use_container_width=True):
            if email_i and mdp_i:
                if mdp_i != confirmer: st.error("❌ Les mots de passe ne correspondent pas")
                elif pays_i == "Sélectionnez votre pays": st.error("❌ Sélectionnez votre pays")
                elif not ville_i: st.error("❌ Entrez votre ville")
                else:
                    valide, msg = valider_mot_de_passe(mdp_i)
                    if not valide: st.error(f"❌ {msg}")
                    else:
                        with st.spinner("Création du compte..."):
                            result = inscrire(email_i, mdp_i, pays_i, ville_i)
                        if "erreur" in result: st.error(f"❌ {result['erreur']}")
                        else:
                            if result.get("connexion_auto"):
                                sauvegarder_session(email_i, pays_i, ville_i, result.get("token", ""))
                                st.success("✅ Compte créé — Connexion automatique !")
                                st.rerun()
                            else:
                                st.success("✅ Compte créé !")
                                st.info(f"📧 Email de confirmation envoyé à **{email_i}**\n\n> Vérifiez aussi vos **spams**")
            else:
                st.warning("⚠️ Remplissez tous les champs")

# ==============================
# Page Analyse
# ==============================
def page_analyser():
    st.title("🔍 Analyser un compte")
    st.markdown("<p style='color:#6b7280;font-size:13px;margin-bottom:1.5rem;'>Renseignez les informations du compte à analyser</p>", unsafe_allow_html=True)

    # Section Identité
    st.markdown('<div class="ct-card">', unsafe_allow_html=True)
    st.markdown('<span class="ct-section-title">👤 Identité du compte</span>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        username_raw = st.text_input("Nom d'utilisateur *", placeholder="ex: staned_junior6", key="username_input")
    with col2:
        fullname_raw = st.text_input("Nom complet", placeholder="ex: Mr.Stan6", key="fullname_input")
    username = nettoyer_entree(username_raw)
    fullname = nettoyer_entree(fullname_raw)
    name_equals = 1 if (username.lower().strip() == fullname.lower().strip() and username != "") else 0
    if username and fullname:
        if name_equals == 1:
            st.warning("⚠️ Nom complet identique au nom d'utilisateur — indicateur suspect")
        else:
            st.info("✅ Nom complet différent du nom d'utilisateur")

    # ✅ Photo de profil — selectbox persistant
    profile_pic = st.selectbox(
        "Photo de profil",
        options=[1, 0],
        format_func=lambda x: "✅ Oui" if x == 1 else "Non",
        key="profile_pic"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Section Stats
    st.markdown('<div class="ct-card">', unsafe_allow_html=True)
    st.markdown('<span class="ct-section-title">📊 Statistiques</span>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        posts = st.number_input("Publications", min_value=0, max_value=100000, step=1, key="posts_input")
    with col2:
        followers = st.number_input("Followers", min_value=0, max_value=10000000, step=1, key="followers_input")
    with col3:
        follows = st.number_input("Abonnements", min_value=0, max_value=10000000, step=1, key="follows_input")
    description_length = st.number_input("Longueur de la bio (caractères)", min_value=0, max_value=500, step=1, key="bio_input")
    st.markdown('</div>', unsafe_allow_html=True)

    # Section Paramètres
    st.markdown('<div class="ct-card">', unsafe_allow_html=True)
    st.markdown('<span class="ct-section-title">⚙️ Paramètres</span>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        # ✅ Lien externe — selectbox persistant
        external_url = st.selectbox(
            "Lien externe dans la bio",
            options=[0, 1],
            format_func=lambda x: "✅ Oui" if x == 1 else "Non",
            key="external_url"
        )
    with col2:
        # ✅ Compte privé — selectbox persistant
        private = st.selectbox(
            "Compte privé",
            options=[0, 1],
            format_func=lambda x: "🔒 Oui" if x == 1 else "🌐 Non",
            key="private"
        )
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🔍 Lancer l'analyse IA", use_container_width=True):
        if not username:
            st.warning("⚠️ Entrez un nom d'utilisateur")
        else:
            data = {
                "profile_pic": profile_pic,
                "username": username, "fullname": fullname,
                "name_equals_username": name_equals,
                "description_length": int(description_length),
                "external_url": external_url,
                "private": private,
                "posts": int(posts), "followers": int(followers), "follows": int(follows),
                "user_email": st.session_state.email,
                "user_pays": st.session_state.pays, "user_ville": st.session_state.ville
            }
            try:
                with st.spinner("⏳ Analyse IA en cours..."):
                    response = requests.post(f"{API_URL}/analyser", json=data)
                    result = response.json()
                if "erreur" in result:
                    st.error(f"❌ {result['erreur']}")
                else:
                    st.session_state.dernier_resultat = result
                    # ✅ Créer l'entrée historique
                    entree = {
                        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "compte_analyse": result.get("compte_analyse",""),
                        "resultat": result.get("resultat",""),
                        "score_authenticite": result.get("score_authenticite",0),
                        "score_suspicion": result.get("score_suspicion",0),
                    }
                    if "historique_session" not in st.session_state:
                        st.session_state.historique_session = []
                    if not st.session_state.historique_session or \
                       st.session_state.historique_session[0].get("compte_analyse") != entree["compte_analyse"]:
                        st.session_state.historique_session.insert(0, entree)
                    # ✅ SAUVEGARDER dans cache JSON local (persiste déco/actualisation)
                    _email = st.session_state.get("email","").strip()
                    if _email:
                        ajouter_analyse_cache(_email, entree)
                        sauvegarder_dernier_resultat_cache(_email, result)
                    st.markdown("---")
                    st.markdown("### 📊 Résultat de l'analyse")

                    if result.get("deja_analyse_par_user") and result.get("derniere_analyse"):
                        da = result["derniere_analyse"]
                        st.info(f"📌 **Déjà analysé !** {da['date']} | {da['resultat']} | Auth: {da['score_authenticite']}% | Susp: {da['score_suspicion']}%")

                    nb_analyses = result.get("nb_analyses_total", 0)
                    if nb_analyses > 0:
                        st.markdown(f"""<div style="display:inline-flex;align-items:center;gap:4px;background:rgba(59,130,246,0.1);border:0.5px solid rgba(59,130,246,0.25);border-radius:20px;padding:3px 10px;font-size:11px;color:#60a5fa;margin-bottom:1rem;">📊 Analysé <strong>{nb_analyses} fois</strong> sur CyberTrust Africa</div>""", unsafe_allow_html=True)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("✅ Score Authenticité", f"{result['score_authenticite']} %")
                    with col2:
                        st.metric("⚠️ Score Suspicion", f"{result['score_suspicion']} %")

                    # Barre de progression
                    score_susp = result['score_suspicion']
                    st.markdown(f"""
                    <div class="ct-progress-wrap">
                        <div style="display:flex;justify-content:space-between;font-size:11px;color:#6b7280;margin-bottom:6px;">
                            <span style="color:#10b981">Authentique</span>
                            <span style="color:#ef4444">Suspect</span>
                        </div>
                        <div class="ct-progress-bar-bg">
                            <div style="width:{score_susp}%;height:100%;border-radius:3px;background:linear-gradient(90deg,#10b981,#f59e0b,#ef4444);"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    nb_denon = result.get("nb_denonciations", 0)
                    types_arnaque = result.get("types_arnaque", [])
                    if nb_denon > 0:
                        st.error(f"🚨 **ALERTE — Ce compte a été dénoncé {nb_denon} fois !**\n\nTypes : **{', '.join(types_arnaque)}**")

                    if result["score_authenticite"] >= 70:
                        st.success(f"✅ {result['resultat']}")
                        if nb_denon == 0: st.balloons()
                    else:
                        st.error(f"🚨 {result['resultat']}")
                        sig = result.get("signalements_region", 0)
                        region = result.get("region_utilisateur", "")
                        if sig > 0 and region:
                            st.warning(f"📍 **{sig} compte(s) suspect(s) unique(s)** dans votre région ({region})")
                        if result["score_suspicion"] >= 70:
                            st.markdown("---")
                            st.markdown('<div class="ct-card-red">', unsafe_allow_html=True)
                            st.markdown('<span class="ct-section-title-red">⚠️ Recommandations de sécurité</span>', unsafe_allow_html=True)
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.markdown("**🚫 Arrêter**\n- Cessez tout contact\n- Ne partagez rien\n- N'envoyez pas d'argent")
                            with col2:
                                st.markdown("**🔒 Bloquer**\n- Bloquez ce compte\n- Signalez à la plateforme\n- Protégez votre profil")
                            with col3:
                                st.markdown("**📢 Signaler**\n- Dénoncez sur CyberTrust\n- Portez plainte\n- Conservez les preuves")
                            st.markdown('</div>', unsafe_allow_html=True)
                            st.warning("📞 **En cas d'urgence :** Portez plainte immédiatement")
                        else:
                            st.warning("⚠️ Soyez prudent avec ce compte !")
            except Exception as e:
                st.error("❌ Impossible de contacter l'API")

    # ✅ Afficher le dernier résultat — charger depuis cache si session vide
    if not st.session_state.get("dernier_resultat"):
        _email = st.session_state.get("email","")
        if _email:
            _cache = charger_cache_utilisateur(_email)
            if _cache.get("dernier_resultat"):
                st.session_state.dernier_resultat = _cache["dernier_resultat"]

    if st.session_state.get("dernier_resultat"):
        result = st.session_state.dernier_resultat
        st.markdown("---")
        st.markdown("""
        <div style="font-size:11px;color:#6b7280;font-family:sans-serif;margin-bottom:8px;">
            🕘 Dernier résultat enregistré
        </div>
        """, unsafe_allow_html=True)
        score_auth = result.get("score_authenticite", 0)
        score_susp = result.get("score_suspicion", 0)
        compte = result.get("compte_analyse", "")
        resultat = result.get("resultat", "")
        is_suspect = "suspect" in resultat.lower()
        couleur_bord = "rgba(239,68,68,0.3)" if is_suspect else "rgba(16,185,129,0.3)"
        icon = "🚨" if is_suspect else "✅"

        st.markdown(f"""
        <div style="background:#111827;border:0.5px solid {couleur_bord};border-radius:14px;padding:1.25rem 1.5rem;">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;">
                <div style="font-size:15px;font-weight:500;color:#f9fafb;">{icon} @{compte}</div>
                <div style="font-size:11px;color:#6b7280;">{result.get("nb_analyses_total", 0)} analyse(s) au total</div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:1rem;">
                <div style="background:rgba(16,185,129,0.1);border:0.5px solid rgba(16,185,129,0.3);border-radius:10px;padding:12px;text-align:center;">
                    <div style="font-size:11px;color:#10b981;margin-bottom:4px;">✅ Authenticité</div>
                    <div style="font-size:26px;font-weight:600;color:#10b981;">{score_auth}%</div>
                </div>
                <div style="background:rgba(245,158,11,0.1);border:0.5px solid rgba(245,158,11,0.3);border-radius:10px;padding:12px;text-align:center;">
                    <div style="font-size:11px;color:#f59e0b;margin-bottom:4px;">⚠️ Suspicion</div>
                    <div style="font-size:26px;font-weight:600;color:#f59e0b;">{score_susp}%</div>
                </div>
            </div>
            <div style="height:6px;background:#1f2937;border-radius:3px;overflow:hidden;">
                <div style="width:{score_susp}%;height:100%;background:linear-gradient(90deg,#10b981,#f59e0b,#ef4444);border-radius:3px;"></div>
            </div>
            <div style="text-align:center;margin-top:1rem;font-size:14px;font-weight:500;color:{'#ef4444' if is_suspect else '#10b981'};">
                {resultat}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==============================
# Page Dénoncer
# ==============================
def page_denoncer():
    st.title("🚨 Dénoncer un cybercriminel")

    try:
        hist = get_historique_denonciations()
        if hist.get("total", 0) > 0:
            st.markdown('<div class="ct-card-red">', unsafe_allow_html=True)
            st.markdown('<span class="ct-section-title-red">📋 Vos dénonciations du mois</span>', unsafe_allow_html=True)
            st.caption("⚠️ Cet historique se supprime automatiquement après 30 jours")
            for d in reversed(hist["denonciations"]):
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
    plateforme = st.selectbox("Plateforme *", ["Sélectionnez", "Instagram", "Facebook", "TikTok", "Twitter/X", "WhatsApp", "Telegram", "Snapchat", "LinkedIn", "Autre"])

    st.markdown('<span class="ct-section-title-red" style="margin-top:1rem;">🎭 Type d\'arnaque *</span>', unsafe_allow_html=True)
    types_options = ["💰 Arnaque financière", "😡 Harcèlement", "🔒 Extorsion / Chantage", "🎭 Usurpation d'identité", "💔 Faux profil romantique", "🛍️ Escroquerie à la vente", "🔗 Phishing / Liens malveillants", "❓ Autre"]
    if "selected_types" not in st.session_state:
        st.session_state.selected_types = []

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
    description = st.text_area("Décrivez ce qui s'est passé * (min. 50 caractères)", placeholder="Exemple : Le compte m'a contacté en prétendant vendre des articles...", height=130)
    if description:
        nb = len(description)
        if nb < 50: st.error(f"❌ {nb}/50 caractères minimum")
        elif nb < 100: st.warning(f"⚠️ {nb} caractères — Ajoutez plus de détails")
        else: st.success(f"✅ {nb} caractères")

    montant = 0
    if st.session_state.selected_types and "💰 Arnaque financière" in st.session_state.selected_types:
        montant = st.number_input("Montant escroqué", min_value=0, step=1000)

    col1, col2 = st.columns(2)
    with col1:
        date_incident = st.date_input("Date de l'incident *")
    with col2:
        pays_victime = st.selectbox("Votre pays *", ["Sélectionnez"] + PAYS, key="denonce_pays")
    ville_victime = st.text_input("Votre ville *", placeholder="ex: Dakar", key="denonce_ville")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="ct-card">', unsafe_allow_html=True)
    st.markdown('<span class="ct-section-title">✅ Questionnaire de vérification</span>', unsafe_allow_html=True)
    q1 = st.radio("Avez-vous effectué une transaction avec ce compte ?", ["Oui", "Non", "Je préfère ne pas répondre"])
    q2 = st.radio("Avez-vous des preuves ?", ["Oui, j'ai des preuves", "Non, je n'ai pas de preuves", "J'ai quelques éléments"])
    q3 = st.radio("Connaissez-vous personnellement ce compte ?", ["Non, c'est un inconnu", "Oui, je le connais", "Je ne suis pas sûr"])
    q5 = st.checkbox("Je certifie sur l'honneur que les informations sont véridiques", value=False)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🚨 Soumettre la dénonciation", use_container_width=True, type="primary"):
        erreurs = []
        if not compte_denonce: erreurs.append("Nom du compte obligatoire")
        if plateforme == "Sélectionnez": erreurs.append("Sélectionnez la plateforme")
        if not st.session_state.selected_types: erreurs.append("Sélectionnez au moins un type d'arnaque")
        if len(description) < 50: erreurs.append("Description trop courte (min 50 caractères)")
        if pays_victime == "Sélectionnez": erreurs.append("Sélectionnez votre pays")
        if not ville_victime: erreurs.append("Entrez votre ville")
        if not q5: erreurs.append("Vous devez certifier les informations")
        if q2 == "Non, je n'ai pas de preuves" and q1 == "Non": erreurs.append("Signalement insuffisant — pas de preuves ni de transaction")

        if erreurs:
            for e in erreurs: st.error(f"❌ {e}")
        else:
            type_arnaque_str = ", ".join([t.split(" ", 1)[1] for t in st.session_state.selected_types])
            data = {
                "compte_denonce": nettoyer_entree(compte_denonce), "plateforme": plateforme,
                "type_arnaque": type_arnaque_str, "description": nettoyer_entree(description),
                "montant_escroqué": montant, "date_incident": str(date_incident),
                "pays_victime": pays_victime, "ville_victime": nettoyer_entree(ville_victime),
                "user_email": st.session_state.email
            }
            with st.spinner("Envoi..."):
                result = soumettre_denonciation(data)
            if "erreur" in result:
                st.error(f"❌ {result['erreur']}")
            else:
                st.session_state.selected_types = []
                st.success(f"✅ {result['message']}")
                st.info(f"📊 Score de fiabilité : **{result['score_fiabilite']}/100**")
                st.markdown("""
---
### 📢 Dénonciation enregistrée !
Notre équipe va l'étudier. Si validée, elle sera publiée sur les **pages officielles de Cyber Africa Culture** 🌍

> Historique disponible pendant **30 jours**
                """)
                if result.get("statut") == "valide":
                    st.balloons()

# ==============================
# Page Historique
# ==============================
def page_historique():
    st.title("📊 Historique des analyses")
    st.markdown("---")

    # ✅ Charger depuis cache JSON local (persiste déco/actualisation)
    email = st.session_state.get("email", "").strip()
    cache = charger_cache_utilisateur(email) if email else {"historique":[], "dernier_resultat":None}
    historique_cache = cache.get("historique", [])

    # ✅ Fusionner avec session_state (plus récent)
    historique_session = st.session_state.get("historique_session", [])
    comptes_session = {a.get("compte_analyse","") + a.get("date","") for a in historique_session}
    for a in historique_cache:
        cle = a.get("compte_analyse","") + a.get("date","")
        if cle not in comptes_session:
            historique_session.append(a)

    # Mettre à jour session_state
    st.session_state.historique_session = historique_session
    historique = historique_session
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
            <div style="font-size:14px;color:#4b5563;">Aucune analyse effectuée.<br>
            Allez sur <b>🔍 Analyser</b> pour commencer !</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("---")
        filtre = st.radio("Filtrer", ["Tous", "🚨 Suspects", "✅ Authentiques"], horizontal=True)

        nb_affiches = 0
        for analyse in historique:
            resultat = analyse.get("resultat", "")
            is_suspect = "suspect" in resultat.lower()
            if filtre == "🚨 Suspects" and not is_suspect: continue
            if filtre == "✅ Authentiques" and is_suspect: continue

            nb_affiches += 1
            type_class = "suspect" if is_suspect else "authentique"
            icon = "🚨" if is_suspect else "✅"
            score_auth = analyse.get("score_authenticite", 0)
            score_susp = analyse.get("score_suspicion", 0)
            bar_color = "#ef4444" if is_suspect else "#10b981"

            st.markdown(f"""
            <div class="ct-hist-item {type_class}">
                <div style="flex:1;">
                    <div style="font-size:14px;font-weight:500;color:#f9fafb;">{icon} @{analyse.get('compte_analyse','')}</div>
                    <div style="font-size:11px;color:#6b7280;margin-top:2px;">{analyse.get('date','')}</div>
                    <div style="height:3px;background:#1f2937;border-radius:2px;margin-top:6px;overflow:hidden;">
                        <div style="width:{score_susp}%;height:100%;background:{bar_color};border-radius:2px;"></div>
                    </div>
                </div>
                <div style="text-align:right;margin-left:12px;">
                    <div style="font-size:12px;color:#10b981;font-weight:500;">Auth: {score_auth}%</div>
                    <div style="font-size:12px;color:#f59e0b;font-weight:500;">Susp: {score_susp}%</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        if nb_affiches == 0:
            st.info("Aucune analyse dans cette catégorie")

# ==============================
# Page Carte
# ==============================
def page_carte():
    st.title("🗺️ Carte des signalements")
    st.markdown("<p style='color:#6b7280;font-size:13px;'>Distribution géographique des comptes suspects et dénonciations</p>", unsafe_allow_html=True)
    st.markdown("---")

    try:
        with st.spinner("Chargement..."):
            result = get_carte_stats()
        stats = result.get("stats", [])

        if not stats:
            st.warning("Aucune donnée disponible pour le moment")
        else:
            total_suspects = sum(s.get("comptes_suspects", 0) for s in stats)
            total_denon = sum(s.get("denonciations", 0) for s in stats)

            col1, col2 = st.columns(2)
            with col1: st.metric("🚨 Comptes suspects (score > 60%)", total_suspects)
            with col2: st.metric("📢 Dénonciations validées", total_denon)

            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1: st.markdown('<span style="color:#10b981;font-size:12px;">● Faible (1-2)</span>', unsafe_allow_html=True)
            with col2: st.markdown('<span style="color:#f59e0b;font-size:12px;">● Modéré (3-5)</span>', unsafe_allow_html=True)
            with col3: st.markdown('<span style="color:#ef4444;font-size:12px;">● Élevé (6+)</span>', unsafe_allow_html=True)

            # Carte Folium CartoDB Dark Matter
            m = creer_carte(stats)
            st_folium(m, width=700, height=450)

            st.markdown("---")
            st.markdown('<div class="ct-card">', unsafe_allow_html=True)
            st.markdown('<span class="ct-section-title">🏆 Top pays — Activité signalée</span>', unsafe_allow_html=True)

            df = pd.DataFrame(stats)
            df["total"] = df["comptes_suspects"] + df["denonciations"]
            df = df[df["total"] > 0].sort_values("total", ascending=False).head(10)

            if not df.empty:
                max_val = df["total"].max()
                for i, row in df.iterrows():
                    pct = int(row["total"] / max_val * 100) if max_val > 0 else 0
                    couleur = "#ef4444" if row["total"] >= 6 else "#f59e0b" if row["total"] >= 3 else "#10b981"
                    st.markdown(f"""
                    <div class="ct-country-row">
                        <span style="font-size:12px;color:#4b5563;width:20px;">{list(df.index).index(i)+1}</span>
                        <span style="font-size:13px;color:#f9fafb;flex:1;">🌍 {row['pays']}</span>
                        <div style="flex:2;background:#1f2937;height:4px;border-radius:2px;overflow:hidden;">
                            <div style="width:{pct}%;height:100%;background:{couleur};border-radius:2px;"></div>
                        </div>
                        <span style="font-size:12px;font-weight:500;color:{couleur};min-width:30px;text-align:right;">{int(row['total'])}</span>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ {str(e)}")

# ==============================
# Page Admin Login
# ==============================
def page_admin_login():
    st.title("🔐 Espace Administrateur")
    st.markdown("---")
    if st.session_state.tentatives_admin >= 3:
        st.error("🚨 Accès bloqué — Trop de tentatives échouées")
        return
    st.warning("⚠️ Accès réservé aux administrateurs")
    mdp = st.text_input("Mot de passe admin", type="password", key="admin_pwd")
    st.caption(f"⚠️ {3 - st.session_state.tentatives_admin} tentative(s) restante(s)")
    if st.button("🔐 Accéder au dashboard", use_container_width=True):
        if mdp == ADMIN_PASSWORD:
            st.session_state.admin_connecte = True
            st.session_state.tentatives_admin = 0
            st.rerun()
        else:
            st.session_state.tentatives_admin += 1
            r = 3 - st.session_state.tentatives_admin
            if r > 0: st.error(f"❌ Mot de passe incorrect — {r} tentative(s) restante(s)")
            else: st.error("🚨 Accès bloqué définitivement")

# ==============================
# Page Admin Dashboard
# ==============================
def page_admin_dashboard():
    st.title("🔐 Dashboard Administrateur")

    col1, col2 = st.columns([4,1])
    with col2:
        if st.button("🚪 Déco. Admin", use_container_width=True):
            st.session_state.admin_connecte = False
            st.rerun()

    admin_tabs = st.tabs(["📊 Analyses", "👥 Utilisateurs", "📍 Régional", "🚨 Dénonciations", "🗺️ Carte", "⬇️ Télécharger"])
    tab_analyses, tab_users, tab_regional, tab_denon, tab_carte, tab_dl = admin_tabs
    onglet_admin = None  # handled by tabs below

    with tab_analyses:
        st.markdown("### 📊 Toutes les analyses")
        try:
            result = get_admin_collecte()
            if "erreur" in result:
                st.error(f"❌ {result['erreur']}")
            else:
                donnees = result.get("donnees", [])
                total = result.get("total", 0)
                suspects = sum(1 for d in donnees if "suspect" in d.get("resultat","").lower())

                col1, col2, col3 = st.columns(3)
                with col1: st.metric("📊 Total analyses", total)
                with col2: st.metric("✅ Authentiques", total - suspects)
                with col3: st.metric("🚨 Suspects", suspects)

                if total > 0:
                    st.markdown("---")
                    recherche = st.text_input("🔍 Rechercher un compte", placeholder="ex: fake_account", key="admin_search")
                    df = pd.DataFrame(donnees)
                    if recherche:
                        df = df[df["compte_analyse"].str.contains(recherche, case=False, na=False)]
                    df = df.rename(columns={
                        "date":"Date","user_email":"Email","user_pays":"Pays",
                        "user_ville":"Ville","ip_address":"IP","pays_ip":"Pays IP",
                        "ville_ip":"Ville IP","compte_analyse":"Compte analysé",
                        "nom_complet":"Nom complet","resultat":"Résultat",
                        "score_authenticite":"Auth %","score_suspicion":"Susp %"
                    })
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("Aucune analyse enregistrée pour le moment")
        except Exception as e:
            st.error(f"❌ Erreur : {str(e)}")

    with tab_users:
        st.markdown("### 👥 Utilisateurs inscrits")
        try:
            result = get_admin_utilisateurs()
            if "erreur" in result: st.error(f"❌ {result['erreur']}")
            else:
                st.info(f"👥 Total : **{result['total']}**")
                if result["total"] > 0:
                    df = pd.DataFrame(result["utilisateurs"])
                    df = df.rename(columns={"email":"Email","date_inscription":"Date","pays":"Pays","ville":"Ville","email_verifie":"Email vérifié"})
                    st.dataframe(df, use_container_width=True)
        except Exception as e: st.error(f"❌ {str(e)}")

    with tab_regional:
        st.markdown("### 📍 Signalements régionaux IA")
        try:
            result = get_admin_regional()
            if "erreur" in result: st.error(f"❌ {result['erreur']}")
            else:
                st.info(f"🚨 Total suspects uniques : **{result['total_signalements']}**")
                col1,col2 = st.columns(2)
                with col1:
                    if result["top_pays"]:
                        df_p = pd.DataFrame(result["top_pays"])
                        df_p.columns = ["Pays","Signalements"]
                        st.dataframe(df_p, use_container_width=True)
                with col2:
                    if result["top_villes"]:
                        df_v = pd.DataFrame(result["top_villes"])
                        df_v.columns = ["Ville","Signalements"]
                        st.dataframe(df_v, use_container_width=True)
        except Exception as e: st.error(f"❌ {str(e)}")

    with tab_denon:
        st.markdown("### 🚨 Base de données des dénonciations")
        try:
            result = get_admin_denonciations()
            if "erreur" in result: st.error(f"❌ {result['erreur']}")
            else:
                col1,col2,col3 = st.columns(3)
                with col1: st.metric("Total",result["total"])
                with col2: st.metric("✅ Validées",result["valides"])
                with col3: st.metric("⏳ En vérification",result["en_verification"])
                st.markdown("---")
                col1,col2 = st.columns(2)
                with col1:
                    if result["top_pays"]:
                        df_p = pd.DataFrame(result["top_pays"])
                        df_p.columns = ["Pays","Dénonciations"]
                        st.dataframe(df_p, use_container_width=True)
                with col2:
                    if result["top_villes"]:
                        df_v = pd.DataFrame(result["top_villes"])
                        df_v.columns = ["Ville","Dénonciations"]
                        st.dataframe(df_v, use_container_width=True)
                col1,col2 = st.columns(2)
                with col1:
                    if result["top_types"]:
                        df_t = pd.DataFrame(result["top_types"])
                        df_t.columns = ["Type","Dénonciations"]
                        st.dataframe(df_t, use_container_width=True)
                with col2:
                    if result["top_plateformes"]:
                        df_pl = pd.DataFrame(result["top_plateformes"])
                        df_pl.columns = ["Plateforme","Dénonciations"]
                        st.dataframe(df_pl, use_container_width=True)
                if result["denonciations"]:
                    st.markdown("---")
                    st.dataframe(pd.DataFrame(result["denonciations"]), use_container_width=True)
        except Exception as e: st.error(f"❌ {str(e)}")

    with tab_carte:
        st.markdown("### 🗺️ Carte complète Admin")
        try:
            result = get_carte_stats()
            stats = result.get("stats", [])
            if stats:
                m = creer_carte(stats)
                st_folium(m, width=700, height=450)
                df_carte = pd.DataFrame(stats)
                df_carte = df_carte.rename(columns={"pays":"Pays","comptes_suspects":"Suspects","denonciations":"Dénonciations"})
                st.download_button("⬇️ Télécharger données carte", df_carte.to_csv(index=False), "cybertrust_carte.csv", "text/csv", use_container_width=True)
        except Exception as e: st.error(f"❌ {str(e)}")

    with tab_dl:
        st.markdown("### ⬇️ Télécharger les données")
        try:
            result = get_admin_collecte()
            if result.get("total",0) > 0:
                st.download_button("⬇️ Analyses complètes", pd.DataFrame(result["donnees"]).to_csv(index=False), "cybertrust_analyses.csv", "text/csv", use_container_width=True)
            result_u = get_admin_utilisateurs()
            if result_u.get("total",0) > 0:
                st.download_button("⬇️ Utilisateurs", pd.DataFrame(result_u["utilisateurs"]).to_csv(index=False), "cybertrust_utilisateurs.csv", "text/csv", use_container_width=True)
            result_r = get_admin_regional()
            if result_r.get("total_signalements",0) > 0:
                st.download_button("⬇️ Données régionales", pd.DataFrame(result_r["donnees"]).to_csv(index=False), "cybertrust_regional.csv", "text/csv", use_container_width=True)
            result_d = get_admin_denonciations()
            if result_d.get("total",0) > 0:
                st.download_button("⬇️ Dénonciations complètes", pd.DataFrame(result_d["denonciations"]).to_csv(index=False), "cybertrust_denonciations.csv", "text/csv", use_container_width=True)
        except Exception as e: st.error(f"❌ {str(e)}")

# ==============================
# Page principale — Navigation bas d'écran
# ==============================
def page_principale():
    # ✅ Initialiser la page active
    if "page_active" not in st.session_state:
        st.session_state.page_active = "analyser"

    # ✅ Barre utilisateur en haut
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        <div class="ct-top-bar">
            <div>
                <div class="ct-top-bar-email">👤 {st.session_state.email}</div>
                <div class="ct-top-bar-location">📍 {st.session_state.ville}, {st.session_state.pays}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("🚪 Déconnexion", use_container_width=True):
            effacer_session()
            st.rerun()

    # ✅ Navigation bas d'écran — 5 boutons
    nav_items = [
        ("analyser", "🔍", "Analyser"),
        ("denoncer", "🚨", "Dénoncer"),
        ("carte", "🗺️", "Carte"),
        ("historique", "📊", "Historique"),
        ("admin", "🔐", "Admin"),
    ]

    cols = st.columns(5)
    for i, (page_id, icon, label) in enumerate(nav_items):
        with cols[i]:
            is_active = st.session_state.page_active == page_id
            btn_style = "primary" if is_active else "secondary"
            if st.button(f"{icon}\n{label}", key=f"nav_{page_id}", use_container_width=True):
                st.session_state.page_active = page_id
                st.rerun()

    st.markdown("---")

    # ✅ Afficher la page active
    page = st.session_state.page_active
    if page == "analyser":
        page_analyser()
    elif page == "denoncer":
        page_denoncer()
    elif page == "carte":
        page_carte()
    elif page == "historique":
        page_historique()
    elif page == "admin":
        if st.session_state.admin_connecte:
            page_admin_dashboard()
        else:
            page_admin_login()

# ==============================
# Main
# ==============================
if st.session_state.connecte:
    page_principale()
else:
    page_auth()