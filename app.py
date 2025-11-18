# app.py
import streamlit as st
from datetime import datetime, date, timedelta
import random
import uuid
import pandas as pd
from utils.storage import (
    ensure_data_file, load_routes, save_routes,
    load_email_config, save_email_config,
    append_log, count_updates_last_24h, ensure_route_fields, sanitize_dict
)
from utils.plotting import plot_price_history
from email_utils import send_email
from exporters_detailed import export_detailed_xlsx, export_detailed_pdf

ensure_data_file()
routes = load_routes()
email_cfg = load_email_config()

# -----------------------------
# TOP BAR
# -----------------------------
st.set_page_config(page_title="Flight Price Tracker", layout="wide")
st.title("✈️ Flight Price Tracker — Multi-onglets")

global_notif_enabled = bool(email_cfg.get("enabled", False))
notif_color = "🟢" if global_notif_enabled else "🔴"
st.markdown(
    f"<div style='font-size:18px; margin-bottom:15px;'>{notif_color} "
    f"<b>Notifications globales : {'ACTIVÉES' if global_notif_enabled else 'DÉSACTIVÉES'}</b></div>",
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns([1,2,1])

with col1:
    if st.button("Mettre à jour tous (simu)"):
        for r in routes:
            price = random.randint(120, 1000)
            r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
            r["last_tracked"] = datetime.now().isoformat()
        save_routes(routes)
        append_log(f"{datetime.now().isoformat()} - Bulk update (simu)")
        st.success("Mise à jour globale simulée.")
        st.rerun()

with col3:
    if st.button("Exporter tous XLSX"):
        path = export_detailed_xlsx(routes)
        st.download_button("Télécharger XLSX", data=open(path,"rb").read(), file_name="export_detailed.xlsx")

    if st.button("Exporter tous PDF"):
        path = export_detailed_pdf(routes)
        st.download_button("Télécharger PDF", data=open(path,"rb").read(), file_name="export_detailed.pdf")

st.markdown("---")

# -----------------------------
# DASHBOARD
# -----------------------------
st.header("📊 Dashboard — Récapitulatif des suivis")
if not routes:
    st.info("Aucun suivi pour l'instant. Ajoute un suivi dans l'onglet « Ajouter un suivi ».")
else:
    for idx, r in enumerate(routes):
        ensure_route_fields(r)
        st.subheader(f"{r['origin']} → {r['destination']}  (id: {r['id'][:8]})")
        cols = st.columns([2,1,1,1])

        # LEFT COL
        with cols[0]:
            st.write(
                f"**Dates :** {r.get('departure')} (±{r.get('departure_flex_days',0)} j) → "
                f"{r.get('return')} (±{r.get('return_flex_days',0)} j)\n\n"
                f"**Classe :** {r.get('travel_class','Eco')}\n\n"
                f"**Séjour :** {r.get('stay_min')}–{r.get('stay_max')} j\n\n"
                f"**Seuil :** {r.get('target_price')}€\n\n"
                f"**Email :** {r.get('email') or email_cfg.get('email','—')}"
            )

        # UPDATE BUTTON
        with cols[1]:
            if st.button("Update", key=f"dash_update_{idx}"):
                price = random.randint(120, 1000)
                r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
                r["last_tracked"] = datetime.now().isoformat()
                save_routes(routes)
                append_log(f"{datetime.now().isoformat()} - Manual update {r['id']} price={price}")
                st.rerun()

        # NOTIF BUTTON
        with cols[2]:
            if r.get("notifications"):
                if st.button("Désactiver notif", key=f"dash_notif_off_{idx}"):
                    r["notifications"] = False
                    save_routes(routes)
                    append_log(f"{datetime.now().isoformat()} - Notifications OFF {r['id']}")
                    st.rerun()
            else:
                if st.button("Activer notif", key=f"dash_notif_on_{idx}"):
                    r["notifications"] = True
                    save_routes(routes)
                    append_log(f"{datetime.now().isoformat()} - Notifications ON {r['id']}")
                    st.rerun()

        # DELETE BUTTON
        with cols[3]:
            if st.button("Supprimer", key=f"dash_del_{idx}"):
                append_log(f"{datetime.now().isoformat()} - Delete route {r['id']}")
                routes.pop(idx)
                save_routes(routes)
                st.rerun()

        # EXPORT SINGLE
        ex1, ex2 = st.columns(2)
        with ex1:
            if st.button("Exporter XLSX ce suivi", key=f"export_xlsx_{idx}"):
                path = export_detailed_xlsx(routes, single_route_id=r["id"])
                st.download_button("Télécharger XLSX", data=open(path,"rb").read(), file_name=f"{r['origin']}_{r['destination']}.xlsx")
        with ex2:
            if st.button("Exporter PDF ce suivi", key=f"export_pdf_{idx}"):
                path = export_detailed_pdf(routes, single_route_id=r["id"])
                st.download_button("Télécharger PDF", data=open(path,"rb").read(), file_name=f"{r['origin']}_{r['destination']}.pdf")

        # PRICE HISTORY PLOT
        if r.get("history"):
            fig = plot_price_history(r["history"])
            st.pyplot(fig)
        else:
            st.info("Aucun historique encore pour ce vol.")

        # EDIT ROUTE
        with st.expander("✏️ Éditer ce suivi"):
            from ui_components import render_edit_route
            render_edit_route(r, routes, email_cfg)

st.markdown("---")

# -----------------------------
# AJOUTER UN SUIVI
# -----------------------------
from ui_components import render_add_tab
render_add_tab(routes)

# -----------------------------
# RECHERCHE & SIMULATION
# -----------------------------
from ui_components import render_search_tab
render_search_tab(routes)

# -----------------------------
# CONFIGURATION
# -----------------------------
from ui_components import render_config_tab
render_config_tab()
