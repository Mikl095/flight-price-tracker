# app.py
import streamlit as st
from utils.storage import load_routes, load_email_config
from ui_components import (
    render_top_bar,
    render_dashboard,
    render_add_tab,
    render_search_tab,
    render_config_tab
)

# -----------------------------
# CHARGEMENT DES DONNÉES
# -----------------------------
routes = load_routes()
email_cfg = load_email_config()
global_notif_enabled = bool(email_cfg.get("enabled", False))

# -----------------------------
# SIDEBAR — Navigation
# -----------------------------
st.sidebar.title("🛫 Navigation")
tabs = ["Dashboard", "Ajouter un suivi", "Recherche/Simulation", "Configuration"]
active_tab = st.sidebar.radio("Choisir un onglet", tabs)

# -----------------------------
# TOP BAR (Actions globales / Export)
# -----------------------------
render_top_bar(routes, email_cfg)

# -----------------------------
# Onglets principaux
# -----------------------------
if active_tab == "Dashboard":
    render_dashboard(routes, email_cfg, global_notif_enabled)
elif active_tab == "Ajouter un suivi":
    render_add_tab(routes)
elif active_tab == "Recherche/Simulation":
    render_search_tab(routes)
elif active_tab == "Configuration":
    render_config_tab()
