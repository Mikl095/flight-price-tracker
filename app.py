import streamlit as st
from utils.storage import ensure_data_file, load_routes, save_routes, load_email_config, save_email_config
from ui_components import render_top_bar, render_dashboard, render_search_tab
import pandas as pd

# --- initialisation ---
ensure_data_file()
routes = load_routes()
email_cfg = load_email_config()

# --- sidebar ---
st.sidebar.title("Flight Price Tracker")
tab = st.sidebar.radio("Navigation", ["Dashboard", "Ajouter suivi", "Configuration"])

# --- Dashboard tab ---
if tab == "Dashboard":
    render_top_bar(routes)
    render_dashboard(routes, email_cfg)

# --- Ajouter suivi / Search tab ---
elif tab == "Ajouter suivi":
    st.header("🔎 Ajouter un suivi")
    
    # Exemple de DataFrame de résultats de recherche
    # Remplace par ta logique réelle de recherche / API
    df_res = pd.DataFrame([
        {"id":"res1","origin":"Paris","destination":"New York","departure":"2025-12-25","price":450,"stay_days":7},
        {"id":"res2","origin":"Paris","destination":"Tokyo","departure":"2025-12-28","price":800,"stay_days":10},
        {"id":"res3","origin":"Paris","destination":"Lisbonne","departure":"2025-12-30","price":150,"stay_days":5},
    ])
    render_search_tab(df_res, routes)

# --- Configuration tab ---
elif tab == "Configuration":
    st.header("⚙️ Configuration email")
    enabled = st.checkbox("Activer envoi d’email", value=email_cfg.get("enabled", False))
    email = st.text_input("Email destinataire", value=email_cfg.get("email",""))
    api_user = st.text_input("API user", value=email_cfg.get("api_user",""))
    api_pass = st.text_input("API pass / Key", value=email_cfg.get("api_pass",""), type="password")
    if st.button("Enregistrer configuration"):
        email_cfg.update({
            "enabled": enabled,
            "email": email,
            "api_user": api_user,
            "api_pass": api_pass
        })
        save_email_config(email_cfg)
        st.success("Configuration sauvegardée.")

# --- sauvegarde automatique des routes après toutes modifications ---
save_routes(routes)
