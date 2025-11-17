import streamlit as st
from datetime import datetime, date
import random

from utils import (
    load_routes, save_routes,
    load_email_config, save_email_config,
    plot_price_history
)

routes = load_routes()
email_config = load_email_config()

st.set_page_config(page_title="Flight Price Tracker", layout="wide")
st.title("✈️ Flight Price Tracker – Notifications Email + Tracking Auto")


# ---------------------------------------------------------
# Configuration email
# ---------------------------------------------------------
st.sidebar.header("📧 Notifications Email")

email_input = st.sidebar.text_input(
    "Adresse email pour recevoir les alertes",
    email_config.get("email", "")
)

def is_valid_email(email):
    return "@" in email and "." in email and len(email) >= 6

if st.sidebar.button("Enregistrer l'email"):
    if is_valid_email(email_input):
        save_email_config(email_input)
        st.sidebar.success("Email enregistré ✔")
    else:
        st.sidebar.error("Adresse email invalide.")


# ---------------------------------------------------------
# Ajouter un vol
# ---------------------------------------------------------
st.sidebar.header("➕ Ajouter un vol")

origin = st.sidebar.text_input("Origine IATA", "PAR")
destination = st.sidebar.text_input("Destination IATA", "TYO")

departure_date = st.sidebar.date_input("Départ", date.today())
return_date = st.sidebar.date_input("Retour", date.today())
target_price = st.sidebar.number_input("Prix cible (€)", min_value=50, value=450)
tracking_per_day = st.sidebar.number_input("Trackings/jour", min_value=1, max_value=24, value=2)
notifications = st.sidebar.checkbox("Activer notifications", True)

if st.sidebar.button("Ajouter ce vol"):
    route = {
        "origin": origin.upper(),
        "destination": destination.upper(),
        "departure": str(departure_date),
        "return": str(return_date),
        "target_price": target_price,
        "tracking_per_day": tracking_per_day,
        "notifications": notifications,
        "history": [],
        "last_tracked": None
    }
    routes.append(route)
    save_routes(routes)
    st.sidebar.success("Vol ajouté ✔")


# ---------------------------------------------------------
# Liste des vols
# ---------------------------------------------------------
st.header("📊 Vols surveillés")

if not routes:
    st.info("Aucun vol.")
else:
    for idx, r in enumerate(routes):
        st.subheader(f"✈️ {r['origin']} → {r['destination']}")

        st.write(
            f"**Dates :** {r['departure']} → {r['return']}  •  "
            f"**Prix cible :** {r['target_price']}€  •  "
            f"**Notifications :** {'ON' if r['notifications'] else 'OFF'}  •  "
            f"**Trackings/jour :** {r['tracking_per_day']}"
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

        # ON/OFF notifications
        if st.button(f"Toggle notifications", key=f"notif-{idx}"):
            r["notifications"] = not r["notifications"]
            save_routes(routes)
            st.experimental_rerun()

        # Supprimer
        if st.button("Supprimer", key=f"del-{idx}"):
            routes.pop(idx)
            save_routes(routes)
            st.experimental_rerun()
