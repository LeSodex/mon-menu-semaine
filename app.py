import streamlit as st
import pandas as pd
import random

# --- CONFIGURATION ---
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRS_LmTrrujM8a8RnMG4O0__lGPpl459PWmAulQLCCgoS01IZdgOQqGQblLmTqgrzumNCSfCI4zIetw/pub?gid=2493091&single=true&output=csv"

st.set_page_config(page_title="Mon Menu Semainier", page_icon="🍳", layout="wide")

# --- STYLE CSS ---
st.markdown('''
<style>
    .stButton>button { width: 100%; border-radius: 8px; }
    .day-header { font-size: 22px; font-weight: bold; color: #1E88E5; margin-top: 20px; border-bottom: 2px solid #eee; padding-bottom: 5px; }
    .meal-type { font-weight: bold; color: #555; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }
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
    
    # Tirage pondéré
    return random.choices(
        available_df.index.tolist(), 
        weights=available_df['Poids'].tolist(), 
        k=1
    )[0]

# --- CHARGEMENT ---
df = load_data()

if df is None:
    st.error("⚠️ Impossible de lire le fichier Google Sheet.")
    st.stop()

# --- INITIALISATION SESSION ---
# Structure : st.session_state['planning'][JOUR][MOMENT] = {'active': bool, 'recipe_id': int}
DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MOMENTS = ["Midi", "Soir"]

if 'planning' not in st.session_state:
    st.session_state['planning'] = {}
    
    # Initialisation par défaut
    for day in DAYS:
        st.session_state['planning'][day] = {}
        for moment in MOMENTS:
            # Règle : Semaine = Soir uniquement / Weekend = Midi + Soir
            is_weekend = day in ["Samedi", "Dimanche"]
            active = True if (is_weekend or moment == "Soir") else False
            
            st.session_state['planning'][day][moment] = {
                'active': active,
                'recipe_id': None
            }

# Fonction pour remplir les trous (générer aléatoirement là où c'est vide et actif)
def fill_empty_slots():
    used_indices = []
    # On liste d'abord ce qui est déjà fixé pour éviter les doublons
    for d in DAYS:
        for m in MOMENTS:
            rid = st.session_state['planning'][d][m]['recipe_id']
            if rid is not None:
                used_indices.append(rid)

    # On remplit les vides
    for d in DAYS:
        for m in MOMENTS:
            slot = st.session_state['planning'][d][m]
            if slot['active'] and slot['recipe_id'] is None:
                new_idx = get_weighted_recipe_index(df, exclude=used_indices)
                if new_idx is not None:
                    slot['recipe_id'] = new_idx
                    used_indices.append(new_idx)

# Premier remplissage si nécessaire
fill_empty_slots()

# --- INTERFACE ---
st.title("🍳 Planificateur Avancé")

col_top1, col_top2 = st.columns([3, 1])
with col_top1:
    st.caption("Favoris = 3x plus de chances • Gestion Midi/Soir • Liste de courses")
with col_top2:
    if st.button("🎲 Tout régénérer", type="primary"):
        # On reset les IDs mais on garde les cases cochées/décochées
        for d in DAYS:
            for m in MOMENTS:
                st.session_state['planning'][d][m]['recipe_id'] = None
        fill_empty_slots()
        st.rerun()

st.markdown("---")

# --- BOUCLE D'AFFICHAGE DES JOURS ---
for day in DAYS:
    st.markdown(f"<div class='day-header'>{day}</div>", unsafe_allow_html=True)
    
    cols = st.columns(2) # Colonne Midi et Colonne Soir
    
    for i, moment in enumerate(MOMENTS):
        with cols[i]:
            # Clé unique pour les widgets
            slot_key = f"{day}_{moment}"
            slot_data = st.session_state['planning'][day][moment]
            
            # Checkbox activation (Midi / Soir)
            is_active = st.checkbox(f"{moment}", value=slot_data['active'], key=f"check_{slot_key}")
            
            # Mise à jour de l'état si l'utilisateur change la checkbox
            if is_active != slot_data['active']:
                st.session_state['planning'][day][moment]['active'] = is_active
                if is_active and slot_data['recipe_id'] is None:
                    fill_empty_slots() # Si on active, on remplit direct
                st.rerun()

            # Si actif, on affiche la carte recette
            if is_active:
                current_id = slot_data['recipe_id']
                
                # Sélecteur de recette (Recherche manuelle)
                # On prépare la liste pour le selectbox : Index actuel ou None
                options = df.index.tolist()
                # Fonction pour afficher le nom dans le selectbox
                format_func = lambda x: df.iloc[x]['Nom']
                
                selected_id = st.selectbox(
                    "Choisir une recette :",
                    options,
                    index=options.index(current_id) if current_id in options else None,
                    format_func=format_func,
                    key=f"select_{slot_key}",
                    label_visibility="collapsed"
                )
                
                # Détection changement manuel via selectbox
                if selected_id != current_id:
                    st.session_state['planning'][day][moment]['recipe_id'] = selected_id
                    st.rerun()

                # Affichage Détails Recette
                if selected_id is not None:
                    row = df.iloc[selected_id]
                    temps = str(row['Temps']).strip()
                    fav = "★" if str(row['Favori']).lower() in ['true', 'vrai', '1', 'oui'] else ""
                    color_class = f"badge-{temps}" if temps in ['Rapide', 'Moyen', 'Long'] else "badge-Moyen"

                    st.markdown(
                        f"**{fav} {row['Nom']}** <span class='badge {color_class}'>{temps}</span>", 
                        unsafe_allow_html=True
                    )
                    
                    # Bouton Relancer individuel (juste ce créneau)
                    if st.button("🔄 Aléatoire", key=f"reroll_{slot_key}"):
                        # On récupère tous les IDs utilisés AILLEURS pour ne pas faire de doublon
                        all_ids = []
                        for d in DAYS:
                            for m in MOMENTS:
                                if not (d == day and m == moment) and st.session_state['planning'][d][m]['recipe_id'] is not None:
                                    all_ids.append(st.session_state['planning'][d][m]['recipe_id'])
                        
                        new_idx = get_weighted_recipe_index(df, exclude=all_ids)
                        if new_idx is not None:
                            st.session_state['planning'][day][moment]['recipe_id'] = new_idx
                            st.rerun()

                    with st.expander("Ingrédients & Recette"):
                        st.write(f"_{row['Ingredients']}_")
                        st.caption(row['Instructions'])
            else:
                st.caption(f"Pas de repas prévu le {day.lower()} {moment.lower()}.")

# --- LISTE DE COURSES ---
st.markdown("---")
st.header("🛒 Liste de Courses")

ingredients_list = []
for day in DAYS:
    for moment in MOMENTS:
        slot = st.session_state['planning'][day][moment]
        if slot['active'] and slot['recipe_id'] is not None:
            nom_recette = df.iloc[slot['recipe_id']]['Nom']
            ingr_text = df.iloc[slot['recipe_id']]['Ingredients']
            ingredients_list.append(f"**{nom_recette}** : {ingr_text}")

if ingredients_list:
    st.markdown('<div class="ingredient-list">', unsafe_allow_html=True)
    for line in ingredients_list:
        st.markdown(f"- {line}")
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Aucun repas planifié, la liste est vide.")
