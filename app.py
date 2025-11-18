# app.py - Flight Price Tracker - Partie 1/3
import streamlit as st
from datetime import date, datetime, timedelta
import random
import uuid
import pandas as pd

from utils.storage import (
    ensure_data_file, load_routes, save_routes, load_email_config,
    save_email_config, append_log, count_updates_last_24h, ensure_route_fields
)
from utils.plotting import plot_price_history
from exporters import export_csv, export_pdf, export_xlsx
from email_utils import send_email

# ---------- Helpers ----------
def safe_iso_to_datetime(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, date) and not isinstance(val, datetime):
        return datetime.combine(val, datetime.min.time())
    if isinstance(val, str):
        if not val.strip():
            return None
        try:
            return datetime.fromisoformat(val)
        except Exception:
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y"):
                try:
                    return datetime.strptime(val, fmt)
                except Exception:
                    continue
            return None
    return None

def file_bytes_for_path(path):
    with open(path, "rb") as f:
        return f.read()

# ---------- Init ----------
ensure_data_file()
routes = load_routes()
email_cfg = load_email_config()

st.set_page_config(page_title="Flight Price Tracker", layout="wide")
st.title("✈️ Flight Price Tracker — Multi-onglets")

# ---------- Top: quick actions ----------
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
        st.download_button("Télécharger CSV", data=file_bytes_for_path(path), file_name="export.csv")
    if st.button("Exporter PDF"):
        path = export_pdf(routes, path="export.pdf")
        st.download_button("Télécharger PDF", data=file_bytes_for_path(path), file_name="export.pdf")
    if st.button("Exporter XLSX"):
        path = export_xlsx(routes, path="export.xlsx")
        st.download_button("Télécharger XLSX", data=file_bytes_for_path(path), file_name="export.xlsx")

# ---------- Tabs ----------
tab_dashboard, tab_add, tab_config, tab_search = st.tabs(
    ["Dashboard", "Ajouter un suivi", "Configuration", "Recherche & Suggestions (simu)"]
)

# ---------------- DASHBOARD ----------------
with tab_dashboard:
    st.header("📊 Dashboard — Récapitulatif des suivis")
    if not routes:
        st.info("Aucun suivi pour l'instant. Ajoute un suivi dans l'onglet « Ajouter un suivi ».")
    else:
        total = len(routes)
        notif_on = sum(1 for r in routes if r.get("notifications"))
        updates_24h = sum(count_updates_last_24h(r) for r in routes)
        c1, c2, c3 = st.columns(3)
        c1.metric("Suivis", total)
        c2.metric("Notifications ON", notif_on)
        c3.metric("Mises à jour (24h)", updates_24h)

        st.markdown("---")
        df_rows = []
        for r in routes:
            last_price = r.get("history")[-1]["price"] if r.get("history") else None
            min_price = min((h["price"] for h in r.get("history", [])), default=None)
            df_rows.append({
                "id": r.get("id")[:8],
                "origin": r.get("origin"),
                "destination": r.get("destination"),
                "departure": r.get("departure"),
                "return": r.get("return"),
                "last_price": last_price,
                "min_price": min_price,
                "target": r.get("target_price"),
                "notif": "ON" if r.get("notifications") else "OFF",
                "email": r.get("email") or email_cfg.get("email", "")
            })
        df = pd.DataFrame(df_rows)
        st.dataframe(df, use_container_width=True)
# ---------------- AJOUTER UN SUIVI ----------------
with tab_add:
    st.header("➕ Ajouter / Éditer un suivi")
    with st.form("add_route_form"):
        col1, col2 = st.columns(2)
        with col1:
            origin = st.text_input("Aéroport de départ (code IATA)", max_chars=3)
            departure = st.date_input("Date de départ", value=date.today())
            notifications = st.checkbox("Activer notifications", value=True)
        with col2:
            destination = st.text_input("Aéroport d'arrivée (code IATA)", max_chars=3)
            return_date = st.date_input("Date de retour (optionnelle)", value=None)
            target_price = st.number_input("Prix cible (€)", min_value=0, value=300)

        submit = st.form_submit_button("Ajouter suivi")
        if submit:
            if not origin or not destination:
                st.warning("Merci de renseigner les deux aéroports.")
            else:
                route = {
                    "id": str(uuid.uuid4()),
                    "origin": origin.upper(),
                    "destination": destination.upper(),
                    "departure": departure.isoformat(),
                    "return": return_date.isoformat() if return_date else None,
                    "target_price": target_price,
                    "notifications": notifications,
                    "history": [],
                    "email": email_cfg.get("email")
                }
                ensure_route_fields(route)
                routes.append(route)
                save_routes(routes)
                append_log(f"{datetime.now().isoformat()} - Ajout suivi {origin}-{destination}")
                st.success(f"Suivi ajouté pour {origin} → {destination}")
                st.rerun()

# ---------------- CONFIGURATION ----------------
with tab_config:
    st.header("⚙️ Configuration globale")
    email = st.text_input("Email pour notifications", value=email_cfg.get("email", ""))
    global_notifications = st.checkbox("Notifications globales ON/OFF", value=email_cfg.get("global_notifications", True))
    
    if st.button("Sauvegarder configuration"):
        email_cfg["email"] = email
        email_cfg["global_notifications"] = global_notifications
        save_email_config(email_cfg)
        st.success("Configuration enregistrée.")
    
    st.markdown("---")
    st.subheader("Test envoi email")
    if st.button("Envoyer email test"):
        if send_email(email, "Test Notification", "Ceci est un test."):
            st.success(f"Email envoyé avec succès à {email}")
        else:
            st.error("Échec de l'envoi de l'email")

# ---------------- GESTION DES SUIVIS ----------------
st.sidebar.header("🔧 Gestion rapide des suivis")
if routes:
    for r in routes:
        with st.sidebar.expander(f"{r['origin']} → {r['destination']}"):
            st.text(f"Target: {r.get('target_price')}€ | Notifications: {'ON' if r.get('notifications') else 'OFF'}")
            if st.button(f"Supprimer {r['origin']}-{r['destination']}", key=f"del_{r['id']}"):
                routes.remove(r)
                save_routes(routes)
                append_log(f"{datetime.now().isoformat()} - Suppression {r['origin']}-{r['destination']}")
                st.experimental_rerun()
            if st.button(f"Activer/Désactiver notif", key=f"notif_{r['id']}"):
                r["notifications"] = not r.get("notifications", True)
                save_routes(routes)
                st.experimental_rerun()
            if st.button(f"Mettre à jour prix (simu)", key=f"update_{r['id']}"):
                price = random.randint(120, 1000)
                r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
                r["last_tracked"] = datetime.now().isoformat()
                save_routes(routes)
                append_log(f"{datetime.now().isoformat()} - Update simu {r['origin']}-{r['destination']}")
                st.experimental_rerun()
        # ---------------- SUGGESTIONS / RECHERCHE ----------------
with tab_suggest:
    st.header("💡 Suggestions & Recherche")
    
    search_origin = st.text_input("Aéroport de départ", max_chars=3, key="search_origin")
    search_destination = st.text_input("Aéroport d'arrivée (optionnel)", max_chars=3, key="search_dest")
    search_departure = st.date_input("Date de départ", value=None, key="search_departure")
    search_return = st.date_input("Date de retour (optionnelle)", value=None, key="search_return")
    max_duration = st.number_input("Durée max du séjour (jours, optionnel si pas de date de retour)", min_value=0, value=0)
    
    if st.button("Chercher"):
        st.subheader("Résultats")
        results = []
        for r in routes:
            # Filtrage de base
            if search_origin and r["origin"] != search_origin.upper():
                continue
            if search_destination and r["destination"] != search_destination.upper():
                continue
            # Date de départ
            if search_departure and r["departure"] != search_departure.isoformat():
                continue
            # Durée si pas de date de retour
            if search_return:
                if r.get("return") != search_return.isoformat():
                    continue
            elif max_duration > 0 and r.get("return"):
                dep_date = datetime.fromisoformat(r["departure"])
                ret_date = datetime.fromisoformat(r["return"])
                duration = (ret_date - dep_date).days
                if duration > max_duration:
                    continue
            results.append(r)
        
        if results:
            for r in results:
                st.markdown(f"**{r['origin']} → {r['destination']}**")
                last_price = r.get("history")[-1]["price"] if r.get("history") else "N/A"
                st.text(f"Dernier prix connu: {last_price}€ | Notifications: {'ON' if r.get('notifications') else 'OFF'}")
                
                # Graphique historique
                if r.get("history"):
                    df_hist = pd.DataFrame(r["history"])
                    df_hist["date"] = pd.to_datetime(df_hist["date"])
                    st.line_chart(df_hist.set_index("date")["price"])
        else:
            st.info("Aucun suivi ne correspond aux critères.")

# ---------------- LOG ----------------
with tab_logs:
    st.header("📝 Logs")
    if logs:
        for log in reversed(logs[-50:]):
            st.text(log)
    else:
        st.text("Aucun log pour le moment.")
                
