# ui_components.py
import streamlit as st
from datetime import datetime, date, timedelta
import random
import uuid
import pandas as pd

from helpers import safe_iso_to_datetime
from utils.plotting import plot_price_history
from email_utils import send_email
from utils.storage import ensure_route_fields, count_updates_last_24h

def render_top_bar(routes, save_routes, append_log):
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
        if st.button("Exporter CSV"):
            from exporters import export_csv
            path = export_csv(routes, path="export.csv")
            st.download_button("Télécharger CSV", data=open(path,"rb").read(), file_name="export.csv")
        if st.button("Exporter PDF"):
            from exporters import export_pdf
            path = export_pdf(routes, path="export.pdf")
            st.download_button("Télécharger PDF", data=open(path,"rb").read(), file_name="export.pdf")
        if st.button("Exporter XLSX"):
            from exporters import export_xlsx
            path = export_xlsx(routes, path="export.xlsx")
            st.download_button("Télécharger XLSX", data=open(path,"rb").read(), file_name="export.xlsx")

def render_route_panel(r, idx, routes, save_routes, append_log, email_cfg, global_notif_enabled):
    ensure_route_fields(r)

    st.subheader(f"{r['origin']} → {r['destination']}  (id: {r['id'][:8]})")
    cols = st.columns([2,1,1,1])

    # left (info)
    with cols[0]:
        st.write(
            f"**Dates :** {r.get('departure')} (±{r.get('departure_flex_days',0)} j) → "
            f"{r.get('return')} (±{r.get('return_flex_days',0)} j)\n\n"
            f"**Aéroport retour :** {r.get('return_airport') or '—'}\n\n"
            f"**Séjour :** {r.get('stay_min')}–{r.get('stay_max')} j\n\n"
            f"**Seuil :** {r.get('target_price')}€\n\n"
            f"**Email :** {r.get('email') or email_cfg.get('email','—')}"
        )

    # update btn
    with cols[1]:
        if st.button("Update", key=f"dash_update_{idx}"):
            price = random.randint(120, 1000)
            r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
            r["last_tracked"] = datetime.now().isoformat()
            save_routes(routes)
            append_log(f"{datetime.now().isoformat()} - Manual update {r['id']} price={price}")
            st.rerun()

    # notif toggle
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

    # delete
    with cols[3]:
        if st.button("Supprimer", key=f"dash_del_{idx}"):
            append_log(f"{datetime.now().isoformat()} - Delete route {r['id']}")
            routes.pop(idx)
            save_routes(routes)
            st.rerun()

    a1, a2, a3 = st.columns([1,1,1])
    with a1:
        if st.button("Test mail", key=f"dash_testmail_{idx}"):
            if not global_notif_enabled:
                st.warning("Notifications globales désactivées.")
            else:
                rcpt = r.get("email") or email_cfg.get("email", "")
                if not rcpt:
                    st.warning("Aucune adresse email configurée.")
                else:
                    ok, status = send_email(rcpt, f"Test alerte {r['origin']}→{r['destination']}", "<p>Test</p>")
                    st.info("Email envoyé" if ok else f"Erreur (status {status})")
    with a2:
        st.write(f"Last tracked: {r.get('last_tracked') or 'Never'}")
    with a3:
        st.write(f"Updates(24h): {count_updates_last_24h(r)}")

    if r.get("history"):
        fig = plot_price_history(r["history"])
        st.pyplot(fig)
    else:
        st.info("Aucun historique encore pour ce vol.")

    # expand edit form — to keep example short, we still call existing editing logic from app
    with st.expander("✏️ Éditer ce suivi"):
        st.write("Utiliser le formulaire d'édition complet dans l'app (ou extraire en component si tu veux).")
