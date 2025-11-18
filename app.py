# app.py
import streamlit as st
from utils.storage import ensure_data_file, load_routes, save_routes, load_email_config
from ui_components import (
    render_top_bar,
    render_dashboard,
    render_add_tab,
    render_config_tab,
    render_search_tab
)

# -----------------------------
# INITIALISATION
# -----------------------------
ensure_data_file()
routes = load_routes()
email_cfg = load_email_config()

# -----------------------------
# Onglets principaux
# -----------------------------
tabs = ["Dashboard", "Ajouter un suivi", "Recherche / Simulation", "Configuration"]
tab_selected = st.sidebar.radio("Navigation", tabs)

# -----------------------------
# RENDER SELECTED TAB
# -----------------------------
if tab_selected == "Dashboard":
    render_top_bar(routes, email_cfg)
    global_notif_enabled = bool(email_cfg.get("enabled", False))
    render_dashboard(routes, email_cfg, global_notif_enabled)

elif tab_selected == "Ajouter un suivi":
    render_add_tab(routes)

elif tab_selected == "Recherche / Simulation":
    render_search_tab(routes)

elif tab_selected == "Configuration":
    render_config_tab()

# -----------------------------
# AUTO SAVE (si modif manuelle)
# -----------------------------
save_routes(routes)
