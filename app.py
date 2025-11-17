import streamlit as st
from datetime import date, datetime
from utils import load_routes, save_routes, plot_price_history
import random

st.set_page_config(page_title="Flight Price Tracker", layout="wide")
st.title("✈️ Flight Price Tracker – Notifications Email & Tracking Auto")

routes = load_routes()

# ---------------------------------------------------------
# Sidebar — Configuration globale
# ---------------------------------------------------------
st.sidebar.header("⚙️ Configuration Notifications")

email_address = st.sidebar.text_input("Adresse email pour les alertes", "")

service = st.sidebar.selectbox(
    "Service d’envoi email",
    ["SendGrid (Recommandé)"]
)

if st.sidebar.button("Sauvegarder paramètres"):
    st.session_state["email_address"] = email_address
    st.session_state["email_service"] = service
    st.sidebar.success("Paramètres enregistrés.")

# ---------------------------------------------------------
# Sidebar — Ajouter un suivi de vol
# ---------------------------------------------------------
st.sidebar.header("➕ Ajouter un vol à surveiller")

origin = st.sidebar.text_input("Origine IATA", "PAR")
destination = st.sidebar.text_input("Destination IATA", "TYO")
departure_date = st.sidebar.date_input("Date de départ", date.today())
return_date = st.sidebar.date_input("Date de retour", date.today())
target_price = st.sidebar.number_input("Prix cible (€)", min_value=50, value=450)
track_every = st.sidebar.number_input("Trackings par jour", min_value=1, max_value=24, value=2)
notifications_enabled = st.sidebar.checkbox("Activer notifications pour ce vol", True)

if st.sidebar.button("Ajouter"):
    new_route = {
        "origin": origin.upper(),
        "destination": destination.upper(),
        "departure": str(departure_date),
        "return": str(return_date),
        "target_price": target_price,
        "tracking_per_day": track_every,
        "notifications": notifications_enabled,
        "history": [],
        "last_tracked": None
    }
    routes.append(new_route)
    save_routes(routes)
    st.sidebar.success("Vol ajouté.")

# ---------------------------------------------------------
# Section principale — Liste des vols
# ---------------------------------------------------------
st.header("📊 Vols suivis")

if not routes:
    st.info("Aucun vol pour l’instant.")
else:
    for idx, r in enumerate(routes):
        st.subheader(f"{r['origin']} → {r['destination']}")

        st.write(
            f"**Dates :** {r['departure']} → {r['return']}  •  "
            f"**Prix cible :** {r['target_price']}€  •  "
            f"**Notifications :** {'ON' if r['notifications'] else 'OFF'}  •  "
            f"**Tracking/jour :** {r['tracking_per_day']}"
        )

        # Tracking manuel
        if st.button(f"Mettre à jour maintenant", key=f"track-{idx}"):
            price = random.randint(250, 900)
            r["history"].append({"date": str(datetime.now()), "price": price})
            r["last_tracked"] = str(datetime.now())
            save_routes(routes)
            st.success(f"Prix actuel : {price}€")

        # Graphique
        if r["history"]:
            fig = plot_price_history(r["history"])
            st.pyplot(fig)

        # Activer/désactiver notif
        if st.button(f"Toggle Notifications", key=f"notif-{idx}"):
            r["notifications"] = not r["notifications"]
            save_routes(routes)
            st.experimental_rerun()

        # Supprimer
        if st.button("Supprimer", key=f"del-{idx}"):
            routes.pop(idx)
            save_routes(routes)
            st.experimental_rerun()
