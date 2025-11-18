# app.py
import streamlit as st
from helpers import sanitize_dict
from utils.storage import ensure_data_file, load_routes, save_routes, load_email_config, save_email_config
from ui_components import (
    render_top_bar, render_dashboard, render_add_tab, render_config_tab, render_search_tab
)

# INIT
ensure_data_file()
st.set_page_config(page_title="Flight Price Tracker", layout="wide")
st.title("✈️ Flight Price Tracker — Refactor complet")

# session-state centralisé
if "routes" not in st.session_state:
    st.session_state["routes"] = load_routes()
if "email_cfg" not in st.session_state:
    st.session_state["email_cfg"] = load_email_config()

routes = st.session_state["routes"]
email_cfg = st.session_state["email_cfg"]

global_notif_enabled = bool(email_cfg.get("enabled", False))

notif_color = "🟢" if global_notif_enabled else "🔴"
st.markdown(
    f"<div style='font-size:18px; margin-bottom:15px;'>{notif_color} <b>Notifications globales : {'ACTIVÉES' if global_notif_enabled else 'DÉSACTIVÉES'}</b></div>",
    unsafe_allow_html=True,
)

# top quick actions
render_top_bar(routes, save_routes)

# tabs
tab_dashboard, tab_add, tab_config, tab_search = st.tabs([
    "Dashboard", "Ajouter un suivi", "Configuration", "Recherche & Suggestions (simu)"
])

with tab_dashboard:
    render_dashboard(routes, save_routes, email_cfg, global_notif_enabled)

with tab_add:
    render_add_tab(routes, save_routes)

with tab_config:
    render_config_tab(email_cfg, save_email_config)

with tab_search:
    render_search_tab(routes, save_routes)

st.markdown("---")
st.markdown("<p style='text-align:center; color:#888;'>Flight Tracker — Refactor ©</p>", unsafe_allow_html=True)
