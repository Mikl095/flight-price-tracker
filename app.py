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

# -----------------------------
# INITIALISATION
# -----------------------------
ensure_data_file()
routes = load_routes()
email_cfg = load_email_config()

# -----------------------------
# UI PRINCIPAL
# -----------------------------
render_top_bar(routes, email_cfg)

tab = st.sidebar.radio(
    "Onglets",
    ["Dashboard", "Ajouter un suivi", "Recherche / Simulation", "Configuration"]
)

if tab == "Dashboard":
    render_dashboard(routes, email_cfg, global_notif_enabled=email_cfg.get("enabled", False))
elif tab == "Ajouter un suivi":
    render_add_tab(routes)
elif tab == "Recherche / Simulation":
    render_search_tab(routes)
elif tab == "Configuration":
    render_config_tab()
