import streamlit as st
import pandas as pd
from datetime import datetime
from utils.storage import load_routes, save_routes, ensure_data_file, load_email_config
from ui_components import render_top_bar, render_dashboard, render_search_tab

# ------------------------------------------------------------
# INITIALISATION
# ------------------------------------------------------------
st.set_page_config(page_title="Flight Price Tracker", layout="wide")
ensure_data_file()
routes = load_routes()
email_cfg = load_email_config()

# ------------------------------------------------------------
# HEADER / TOP BAR
# ------------------------------------------------------------
st.title("✈️ Flight Price Tracker")
render_top_bar(routes)

# ------------------------------------------------------------
# TABS
# ------------------------------------------------------------
tab = st.sidebar.radio("Navigation", ["Dashboard", "Ajouter depuis recherche", "Configuration"])

if tab == "Dashboard":
    render_dashboard(routes, email_cfg)

elif tab == "Ajouter depuis recherche":
    st.subheader("🔍 Ajouter un suivi depuis des résultats de recherche")
    # Dummy DataFrame pour l’exemple
    if "search_results" not in st.session_state:
        # Générer quelques résultats factices
        df = pd.DataFrame([
            {"id": f"res{i}", "origin": "CDG", "destination": "NYC", "departure": "2025-12-01", "price": 350+i*10, "stay_days": 7}
            for i in range(5)
        ])
        st.session_state.search_results = df
    else:
        df = st.session_state.search_results

    render_search_tab(df, routes)

elif tab == "Configuration":
    st.subheader("⚙️ Configuration générale")
    st.write("Paramètres globaux, email, etc.")
    # Exemple : activation notifications globales
    notify_all = st.checkbox("Activer notifications par défaut pour les nouveaux suivis", value=False)
    st.write("Configuration avancée et email peuvent être ajoutés ici.")
