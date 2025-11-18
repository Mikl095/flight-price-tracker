# app.py
import streamlit as st
from utils.storage import load_routes, save_routes, ensure_data_file
from ui_components import (
    render_top_bar, render_dashboard, render_add_tab, render_edit_tab, render_search_tab
)

ensure_data_file()
if "edit_id" not in st.session_state:
    st.session_state["edit_id"] = None

routes = load_routes()
render_top_bar()

tabs = ["Dashboard", "Ajouter", "Éditer", "Suggestions"]
tab = st.sidebar.radio("Navigation", tabs)

if tab == "Dashboard":
    render_dashboard(routes)
elif tab == "Ajouter":
    render_add_tab(routes)
elif tab == "Éditer":
    render_edit_tab(routes)
elif tab == "Suggestions":
    render_search_tab(routes)
