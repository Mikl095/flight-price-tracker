# app.py
import streamlit as st
from utils.storage import load_routes, save_routes
from ui_components import (
    render_top_bar,
    render_dashboard,
    render_add_tab,
    render_edit_tab,
    render_search_tab
)

st.set_page_config(page_title="Flight Price Tracker", layout="wide")
routes = load_routes()
render_top_bar()

tab = st.sidebar.radio("Onglets", ["Dashboard", "Ajouter", "Modifier", "Suggestions"])
if tab == "Dashboard":
    render_dashboard(routes)
elif tab == "Ajouter":
    render_add_tab(routes)
elif tab == "Modifier":
    if routes:
        sel = st.selectbox("Choisir un suivi à modifier", options=routes, format_func=lambda x: f"{x['origin']} → {x['destination']}")
        render_edit_tab(sel, routes)
    else:
        st.info("Aucun suivi existant à modifier")
elif tab == "Suggestions":
    render_search_tab(routes)
