# ui_components.py
import streamlit as st
import random
from datetime import datetime, date, timedelta
from utils.storage import (
    ensure_route_fields, save_routes, append_log, count_updates_last_24h, sanitize_dict
)
from utils.plotting import plot_price_history
from utils.email_utils import send_email
from exporters import export_csv, export_pdf, export_xlsx

def render_top_bar(routes, email_cfg):
    top_col1, top_col2, top_col3 = st.columns([1,2,1])
    with top_col1:
        if st.button("Mettre à jour tous (simu)"):
            for r in routes:
                price = random.randint(120, 1000)
                r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
                r["last_tracked"] = datetime.now().isoformat()
            save_routes(routes)
            append_log(f"{datetime.now().isoformat()} - Bulk update (simu)")
            st.success("Mise à jour globale simulée.")
            st.rerun()
    with top_col3:
        if st.button("Exporter CSV"):
            path = export_csv(routes, path="export.csv")
            st.download_button("Télécharger CSV", data=open(path,"rb").read(), file_name="export.csv")
        if st.button("Exporter PDF"):
            path = export_pdf(routes, path="export.pdf")
            st.download_button("Télécharger PDF", data=open(path,"rb").read(), file_name="export.pdf")
        if st.button("Exporter XLSX"):
            path = export_xlsx(routes, path="export.xlsx")
            st.download_button("Télécharger XLSX", data=open(path,"rb").read(), file_name="export.xlsx")
