import streamlit as st
import pandas as pd
import random

# --- CONFIGURATION ---
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRS_LmTrrujM8a8RnMG4O0__lGPpl459PWmAulQLCCgoS01IZdgOQqGQblLmTqgrzumNCSfCI4zIetw/pub?gid=2493091&single=true&output=csv"

st.set_page_config(page_title="Mon Menu Semainier", page_icon="🍳", layout="centered")

# --- STYLE CSS ---
st.markdown('''
<style>
    .stButton>button { width: 100%; border-radius: 20px; }
    .day-header { font-size: 20px; font-weight: bold; color: #1E88E5; margin-top: 10px; }
    .badge { padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; color: white; vertical-align: middle; }
    .badge-Rapide { background-color: #28a745; }
    .badge-Moyen { background-color: #ffc107; color: black; }
    .badge-Long { background-color: #dc3545; }
    .recipe-card { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 10px; }
</style>
''', unsafe_allow_html=True)

# --- FONCTIONS ---
@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(CSV_URL, on_bad_lines='skip')
        if len(df.columns) < 5: return None
        # Renommage des colonnes pour être sûr
        new_cols = ['Nom', 'Ingredients', 'Instructions', 'Favori', 'Temps'] + list(df.columns[5:])
        df.columns = new_cols
        return df
    except:
        return None

def get_random_index(df, exclude=[]):
    available = [i for i in df.index if i not in exclude]
    return random.choice(available) if available else None

# --- CHARGEMENT ---
df = load_data()

if df is None:
    st.error("⚠️ Impossible de lire le fichier Google Sheet.")
    st.info("Vérifiez que vous avez bien mis le lien 'Publier sur le web > CSV' dans le code.")
    st.stop()

# --- INITIALISATION SESSION (MÉMOIRE) ---
if 'menu' not in st.session_state:
    st.session_state['menu'] = {}
    days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    chosen = []
    for day in days:
        idx = get_random_index(df, exclude=chosen)
        if idx is not None:
            st.session_state['menu'][day] = idx
            chosen.append(idx)

# --- INTERFACE ---
st.title("🍳 Générateur de Menus")
st.caption("Votre planificateur de repas automatique")

if st.button("🎲 GÉNÉRER UNE SEMAINE COMPLÈTE", type="primary"):
    st.session_state['menu'] = {}
    chosen = []
    days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    for day in days:
        idx = get_random_index(df, exclude=chosen)
        if idx is not None:
            st.session_state['menu'][day] = idx
            chosen.append(idx)
    st.rerun()

st.markdown("---")

days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

for day in days:
    if day in st.session_state['menu']:
        idx = st.session_state['menu'][day]
        row = df.iloc[idx]
        
        temps = str(row['Temps']).strip()
        fav = "★ " if str(row['Favori']).lower() in ['true', 'vrai', '1', 'oui'] else ""
        color_class = f"badge-{temps}" if temps in ['Rapide', 'Moyen', 'Long'] else "badge-Moyen"
        
        # Structure de la carte
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"<div class='day-header'>{day}</div>", unsafe_allow_html=True)
                st.markdown(f"**{fav}{row['Nom']}** <span class='badge {color_class}'>{temps}</span>", unsafe_allow_html=True)
            with col2:
                st.write("")
                st.write("")
                if st.button("🔄", key=f"btn_{day}", help="Changer ce plat"):
                    current_indices = list(st.session_state['menu'].values())
                    new_idx = get_random_index(df, exclude=current_indices)
                    if new_idx is not None:
                        st.session_state['menu'][day] = new_idx
                        st.rerun()
            
            with st.expander("Voir la recette"):
                st.write(f"**🛒 Ingrédients :** {row['Ingredients']}")
                st.write(f"**👨‍🍳 Instructions :** {row['Instructions']}")
            st.divider()
