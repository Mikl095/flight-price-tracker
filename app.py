# app.py
import streamlit as st
from datetime import date
from utils.storage import load_routes, save_routes
from ui_components import (
    render_top_bar,
    render_dashboard,
    render_add_tab,
    render_edit_tab,
    render_search_tab,
    render_export_individual,
    render_config_tab
)

# -----------------------------
# INITIALISATION
# -----------------------------
st.set_page_config(page_title="Flight Price Tracker", layout="wide")
routes = load_routes()

# -----------------------------
# SIDEBAR NAVIGATION
# -----------------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Aller à", [
    "Dashboard",
    "Ajouter un suivi",
    "Recherche / Simulation",
    "Export individuel",
    "Configuration"
])

# -----------------------------
# TOP BAR
# -----------------------------
render_top_bar()

# -----------------------------
# PAGES
# -----------------------------
if page == "Dashboard":
    render_dashboard(routes)
elif page == "Ajouter un suivi":
    render_add_tab(routes)
elif page == "Recherche / Simulation":
    render_search_tab(routes)
elif page == "Export individuel":
    render_export_individual(routes)
elif page == "Configuration":
    render_config_tab()

# -----------------------------
# SAUVEGARDE AUTOMATIQUE
# -----------------------------
if st.button("Sauvegarder toutes les modifications"):
    save_routes(routes)
    st.success("Tous les suivis sauvegardés ✔")
