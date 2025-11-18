# app.py
import streamlit as st
from datetime import datetime, date, timedelta
import uuid
import random
import pandas as pd

from ui_components import (
    render_top_bar,
    render_dashboard,
    render_add_tab,
    render_search_tab,
    render_config_tab
)
from utils.storage import (
    ensure_data_file,
    load_routes,
    save_routes,
    load_email_config,
    save_email_config,
    append_log,
    count_updates_last_24h,
    ensure_route_fields,
    sanitize_dict
)

# Chargement des données
routes = load_routes()
email_cfg = load_email_config()

# -----------------------------
# Sidebar - Navigation
# -----------------------------
st.sidebar.title("Navigation")
tab = st.sidebar.radio("Aller à :", [
    "Dashboard",
    "Ajouter un suivi",
    "Recherche / Simulation",
    "Configuration"
])

# -----------------------------
# Top bar
# -----------------------------
render_top_bar(routes, email_cfg)

# -----------------------------
# Onglets principaux
# -----------------------------
if tab == "Dashboard":
    render_dashboard(routes, email_cfg)
    # Optionnel : éditer un suivi depuis le dashboard
    for r in routes:
        render_edit_route(r, routes, email_cfg)

elif tab == "Ajouter un suivi":
    render_add_tab(routes)

elif tab == "Recherche / Simulation":
    render_search_tab(routes)

elif tab == "Configuration":
    render_config_tab()
