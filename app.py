import streamlit as st
from datetime import date, datetime
from utils.storage import ensure_data_file, load_routes, save_routes, load_email_config, save_email_config
from utils.plotting import plot_price_history
from utils.dashboard import create_flight_table
from exporters import export_csv, export_pdf
from sendgrid_client import sendgrid_send
import os
import random



st.sidebar.header("📧 Test Email")

test_email = st.sidebar.text_input("Email de test", "")
if st.sidebar.button("Envoyer un email de test"):
    from email_utils import send_email
    
    ok = send_email(
        to=test_email,
        subject="Test SendGrid depuis votre Flight Tracker",
        html="<h3>Test réussi 🎉</h3><p>Si vous recevez ce message, SendGrid est bien configuré.</p>"
    )

    if ok:
        st.sidebar.success("Email envoyé !")
    else:
        st.sidebar.error("Erreur : vérifiez votre clé SendGrid.")



# init
ensure_data_file()
routes = load_routes()
email_cfg = load_email_config()

st.set_page_config(page_title="Flight Price Tracker", layout="wide")
st.title("✈️ Flight Price Tracker — Dashboard & Notifications")

# ---------------- Sidebar: global settings ----------------
st.sidebar.header("⚙️ Configuration globale")
email = st.sidebar.text_input("Email de réception des alertes", value=email_cfg.get("email",""))
enable_notifications_global = st.sidebar.checkbox("Activer notifications globales", value=email_cfg.get("enabled", False))
sendgrid_key_field = st.sidebar.text_input("Clé SendGrid (optionnel local)", type="password", value=os.environ.get("SENDGRID_KEY",""))

if st.sidebar.button("Sauvegarder paramètres"):
    cfg = {"email": email.strip(), "enabled": bool(enable_notifications_global)}
    save_email_config(cfg)
    st.sidebar.success("Paramètres sauvegardés (email, notifications).")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.write("SendGrid: pour que GitHub Actions puisse envoyer des emails automatiquement, ajoute une secret `SENDGRID_KEY` dans ton repo.")

# ---------------- Sidebar: add route ----------------
st.sidebar.header("➕ Ajouter un suivi")
origin = st.sidebar.text_input("Origine (IATA)", "PAR")
destination = st.sidebar.text_input("Destination (IATA)", "TYO")
departure_date = st.sidebar.date_input("Date départ", date.today())
return_date = st.sidebar.date_input("Date retour", date.today())
target_price = st.sidebar.number_input("Seuil alerte (€)", min_value=10, value=450)
tracking_per_day = st.sidebar.number_input("Trackings par jour", min_value=1, max_value=24, value=2)
notifications_on = st.sidebar.checkbox("Activer notifications pour ce vol", value=True)
min_bags = st.sidebar.number_input("Min. bagages (préférence)", min_value=0, max_value=5, value=0)
max_stops = st.sidebar.selectbox("Max escales (préférence)", ["any", 0, 1, 2])

if st.sidebar.button("Ajouter ce vol"):
    new = {
        "origin": origin.upper(),
        "destination": destination.upper(),
        "departure": str(departure_date),
        "return": str(return_date),
        "target_price": float(target_price),
        "tracking_per_day": int(tracking_per_day),
        "notifications": bool(notifications_on),
        "min_bags": int(min_bags),
        "max_stops": max_stops,
        "history": [],
        "last_tracked": None
    }
    routes.append(new)
    save_routes(routes)
    st.sidebar.success("Vol ajouté ✔")
    st.rerun()

# ---------------- Main Dashboard ----------------
st.header("📊 Dashboard")

if not routes:
    st.info("Aucun suivi pour l'instant — ajoute un vol dans la barre latérale.")
else:
    import pandas as pd
    df = create_flight_table(routes)
    st.dataframe(df, use_container_width=True)

    # Controls
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("Exporter CSV"):
            path = export_csv(routes)
            st.success(f"CSV exporté: {path}")
            st.download_button("Télécharger CSV", path, file_name=path)
    with col2:
        if st.button("Exporter PDF"):
            path = export_pdf(routes)
            st.success(f"PDF exporté: {path}")
            st.download_button("Télécharger PDF", path, file_name=path)
    with col3:
        if st.button("Mettre à jour tous les prix (simu)"):
            # simple simulate update once per route
            for r in routes:
                price = random.randint(200,900)
                r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
                r["last_tracked"] = datetime.now().isoformat()
                # local quick notification
                if r.get("notifications") and email_cfg.get("enabled") and email_cfg.get("email"):
                    if r.get("target_price") and price <= r.get("target_price"):
                        # try send a quick email with local key if provided
                        local_key = sendgrid_key_field or os.environ.get("SENDGRID_KEY")
                        if local_key:
                            os.environ["SENDGRID_KEY"] = local_key
                            sendgrid_send(email_cfg.get("email"), f"[ALERTE] {r['origin']}→{r['destination']}: {price}€",
                                          f"Prix: {price}€\nSeuil: {r['target_price']}€")
            save_routes(routes)
            st.success("Mise à jour effectuée.")

    # Per-route UI
    for i, r in enumerate(routes):
        st.markdown("---")
        st.subheader(f"{r['origin']} → {r['destination']}")
        cols = st.columns([1,1,1,1])
        with cols[0]:
            if st.button("Mettre à jour", key=f"update_{i}"):
                price = random.randint(200,900)
                r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
                r["last_tracked"] = datetime.now().isoformat()
                save_routes(routes)
                st.rerun()
        with cols[1]:
            if st.button("Toggle notif", key=f"toggle_{i}"):
                r["notifications"] = not r.get("notifications", False)
                save_routes(routes)
                st.rerun()
        with cols[2]:
            if st.button("Supprimer", key=f"del_{i}"):
                routes.pop(i)
                save_routes(routes)
                st.rerun()
        with cols[3]:
            if st.button("Rafraîchir graphe", key=f"graph_{i}"):
                st.rerun()

        if r.get("history"):
            fig = plot_price_history(r["history"])
            st.pyplot(fig)
