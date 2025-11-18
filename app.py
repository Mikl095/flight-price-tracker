# app.py
import streamlit as st
from utils.storage import ensure_data_file, load_routes, load_email_config
from ui_components import render_top_bar, render_dashboard, render_add_tab, render_config_tab, render_search_tab

# Initialisation
ensure_data_file()
routes = load_routes()
email_cfg = load_email_config()

st.set_page_config(page_title="Flight Price Tracker", layout="wide")
st.title("✈️ Flight Price Tracker")

# Notifications globales
global_notif = bool(email_cfg.get("enabled", False))
notif_color = "🟢" if global_notif else "🔴"
st.markdown(f"<div style='font-size:18px;'>{notif_color} Notifications globales : {'ACTIVÉES' if global_notif else 'DÉSACTIVÉES'}</div>", unsafe_allow_html=True)

# Top bar
render_top_bar(routes, email_cfg)

# Tabs
tab_dashboard, tab_add, tab_config, tab_search = st.tabs([
    "Dashboard",
    "Ajouter un suivi",
    "Configuration",
    "Recherche & Suggestions"
])

render_dashboard(tab_dashboard, routes, email_cfg)
render_add_tab(tab_add, routes)
render_config_tab(tab_config, email_cfg)
render_search_tab(tab_search, routes)
