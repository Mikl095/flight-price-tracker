# app.py
import streamlit as st
from utils.storage import load_routes
from ui_components import (
    render_top_bar, render_dashboard, render_add_tab, render_edit_tab,
    render_search_tab, render_config_tab
)

st.set_page_config(page_title="Flight Price Tracker", layout="wide")
render_top_bar()

routes = load_routes()

tabs = ["Dashboard","Ajouter","Recherche/Simulation","Configuration"]
tab = st.sidebar.radio("Onglets", tabs)

if tab=="Dashboard":
    render_dashboard(routes)
elif tab=="Ajouter":
    render_add_tab(routes)
elif tab=="Recherche/Simulation":
    render_search_tab(routes)
elif tab=="Configuration":
    render_config_tab()
