# app.py
import streamlit as st
from utils.storage import load_routes, load_email_config
from ui_components import (
    render_top_bar, render_dashboard, render_add_tab,
    render_search_tab, render_config_tab
)

# Charger les données
routes = load_routes()
email_cfg = load_email_config()

# Top bar
render_top_bar(routes, email_cfg)

# Onglets
tabs = ["Dashboard", "Ajouter un suivi", "Recherche / Simulation", "Configuration"]
selected_tab = st.sidebar.radio("Onglets", tabs)

if selected_tab == "Dashboard":
    render_dashboard(routes, email_cfg, global_notif_enabled=bool(email_cfg.get("enabled", False)))
elif selected_tab == "Ajouter un suivi":
    render_add_tab(routes)
elif selected_tab == "Recherche / Simulation":
    render_search_tab(routes)
elif selected_tab == "Configuration":
    render_config_tab()
