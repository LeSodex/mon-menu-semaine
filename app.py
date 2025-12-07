import streamlit as st
import pandas as pd
import random

# --- CONFIGURATION ---
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRS_LmTrrujM8a8RnMG4O0__lGPpl459PWmAulQLCCgoS01IZdgOQqGQblLmTqgrzumNCSfCI4zIetw/pub?gid=2493091&single=true&output=csv"

st.set_page_config(page_title="Mon Menu Semainier", page_icon="🍳", layout="wide")

# --- CONSTANTES ---
DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MOMENTS = ["Midi", "Soir"]

# --- STYLE CSS ---
st.markdown('''
<style>
    .stButton>button { width: 100%; border-radius: 8px; }
    .day-header { font-size: 22px; font-weight: bold; color: #1E88E5; margin-top: 20px; border-bottom: 2px solid #eee; padding-bottom: 5px; }
    .badge { padding: 4px 8px; border-radius: 4px; font-size: 0.7em; font-weight: bold; color: white; vertical-align: middle; }
    .badge-Rapide { background-color: #28a745; }
    .badge-Moyen { background-color: #ffc107; color: black; }
    .badge-Long { background-color: #dc3545; }
    .ingredient-list { background-color: #f9f9f9; padding: 15px; border-radius: 10px; border-left: 5px solid #1E88E5; }
</style>
''', unsafe_allow_html=True)

# --- FONCTIONS ---
@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(CSV_URL, on_bad_lines='skip')
        if len(df.columns) < 5: return None
        new_cols = ['Nom', 'Ingredients', 'Instructions', 'Favori', 'Temps'] + list(df.columns[5:])
        df.columns = new_cols
        # Calcul des poids pour le tirage au sort (Favori = x3)
        df['Poids'] = df['Favori'].apply(lambda x: 3 if str(x).lower() in ['true', 'vrai', '1', 'oui'] else 1)
        return df
    except:
        return None

def get_weighted_recipe_index(df, exclude=[]):
    """Tire une recette au sort en tenant compte des favoris (x3)"""
    available_df = df[~df.index.isin(exclude)]
    if available_df.empty: return None
    return random.choices(
        available_df.index.tolist(), 
        weights=available_df['Poids'].tolist(), 
        k=1
    )[0]

# --- CHARGEMENT DES DONNÉES ---
df = load_data()

if df is None:
    st.error("⚠️ Impossible de lire le fichier Google Sheet.")
    st.stop()

# --- CALLBACKS (C'est ici que la magie opère pour éviter le bug) ---
def reroll_callback(day, moment, widget_key):
    """Fonction appelée AVANT le rechargement de la page quand on clique sur le bouton"""
    # 1. Identifier les recettes déjà utilisées ailleurs pour éviter les doublons
    used_indices = []
    for d in DAYS:
        for m in MOMENTS:
            # On n'exclut pas le créneau actuel qu'on est en train de changer
            if not (d == day and m == moment):
                rid = st.session_state['planning'][d][m]['recipe_id']
                if rid is not None:
                    used_indices.append(rid)
    
    # 2. Tirer une nouvelle recette
    new_idx = get_weighted_recipe_index(df, exclude=used_indices)
    
    # 3. Mettre à jour le planning ET le widget selectbox
    if new_idx is not None:
        st.session_state['planning'][day][moment]['recipe_id'] = new_idx
        st.session_state[widget_key] = new_idx

def reset_week_callback():
    """Réinitialise tout"""
    st.session_state['planning'] = {}
    for day in DAYS:
        st.session_state['planning'][day] = {}
        for moment in MOMENTS:
            is_weekend = day in ["Samedi", "Dimanche"]
            active = True if (is_weekend or moment == "Soir") else False
            st.session_state['planning'][day][moment] = {'active': active, 'recipe_id': None}
    
    # Nettoyage des clés de widgets pour forcer le rafraîchissement
    keys_to_remove = [k for k in st.session_state.keys() if k.startswith("select_")]
    for k in keys_to_remove:
        del st.session_state[k]

# --- INITIALISATION SESSION ---
if 'planning' not in st.session_state:
    # On utilise le callback de reset pour initialiser la première fois
    reset_week_callback()

# Fonction pour remplir les trous (Initialisation auto)
def fill_empty_slots():
    used_indices = []
    # 1. Lister les recettes déjà placées
    for d in DAYS:
        for m in MOMENTS:
            rid = st.session_state['planning'][d][m]['recipe_id']
            if rid is not None:
                used_indices.append(rid)

    # 2. Remplir les cases actives mais vides
    for d in DAYS:
        for m in MOMENTS:
            slot = st.session_state['planning'][d][m]
            if slot['active'] and slot['recipe_id'] is None:
                new_idx = get_weighted_recipe_index(df, exclude=used_indices)
                if new_idx is not None:
                    slot['recipe_id'] = new_idx
                    used_indices.append(new_idx)

# Premier remplissage au chargement
fill_empty_slots()

# --- INTERFACE ---
st.title("🍳 Planificateur Avancé")

col_top1, col_top2 = st.columns([3, 1])
with col_top1:
    st.caption("Favoris = 3x plus de chances • Gestion Midi/Soir • Liste
