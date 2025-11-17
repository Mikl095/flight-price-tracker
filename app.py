import os
print("Dossiers :", os.listdir("."))      # affiche la racine
print("utils existe ?", os.path.isdir("utils"))
print("Contenu utils :", os.listdir("utils") if os.path.isdir("utils") else "absent")

import streamlit as st
from datetime import date, datetime
from utils.storage import ensure_data_file, load_routes, save_routes
from utils.plotting import plot_price_history

# --- Initialisation ---  
ensure_data_file()
routes = load_routes()

st.set_page_config(page_title="Flight Price Tracker", layout="wide")
st.title("✈️ Flight Price Tracker – Paris → Destinations personnalisables")

# -------------------------------------------------------------------
# Sidebar : ajouter un vol
# -------------------------------------------------------------------
st.sidebar.header("➕ Ajouter un vol")

origin = st.sidebar.text_input("Origine", "PAR")

dest_options = ["TYO", "OSA", "SPK", "PTP", "LON", "Autre…"]
destination = st.sidebar.selectbox("Destination", dest_options)

if destination == "Autre…":
    destination = st.sidebar.text_input("Code IATA", value="")

departure_date = st.sidebar.date_input("Départ", date.today())
return_date = st.sidebar.date_input("Retour", date.today())

target_price = st.sidebar.number_input("Seuil d’alerte (€)", min_value=50, value=350)
tracking_per_day = st.sidebar.number_input("Trackings par jour", min_value=1, max_value=24, value=1)
notifications = st.sidebar.checkbox("Activer les notifications email", value=False)

# Ajouter un vol
if st.sidebar.button("Ajouter ce suivi"):
    if not destination:
        st.sidebar.error("Veuillez entrer un code IATA.")
    else:
        new_entry = {
            "origin": origin,
            "destination": destination.upper(),
            "departure": str(departure_date),
            "return": str(return_date),
            "target_price": target_price,
            "tracking_per_day": tracking_per_day,
            "notifications": notifications,
            "last_tracked": None,
            "history": []
        }
        routes.append(new_entry)
        save_routes(routes)
        st.sidebar.success(f"Ajouté : {origin} → {destination.upper()}")
        st.rerun()

# -------------------------------------------------------------------
# Simulation tracking auto (en attendant Amadeus)
# -------------------------------------------------------------------
import random

def simulate_price(route):
    """Simule des prix aléatoires pour les tests."""
    now = datetime.now()
    price = random.randint(200, 900)

    route["history"].append({
        "date": now.isoformat(),
        "price": price
    })
    route["last_tracked"] = now.isoformat()

# -------------------------------------------------------------------
# Section principale
# -------------------------------------------------------------------
st.header("📊 Vos vols surveillés")

if not routes:
    st.info("Aucun vol surveillé.")
else:
    for idx, r in enumerate(routes):
        st.subheader(f"✈️ {r['origin']} → {r['destination']}")

        st.write(
            f"**Dates :** {r['departure']} → {r['return']} • "
            f"**Seuil :** {r['target_price']}€ • "
            f"**Tracking/jour :** {r['tracking_per_day']} • "
            f"**Notifications :** {'ON 🔔' if r.get('notifications') else 'OFF'}"
        )

        # --- Mettre à jour manuellement ---
        if st.button("Mettre à jour maintenant", key=f"update-{idx}"):
            simulate_price(r)
            save_routes(routes)

            last = r["history"][-1]["price"]
            st.info(f"Prix actuel : {last} €")

            if last <= r["target_price"]:
                st.success("🔥 Sous votre seuil !")

            st.rerun()

        # --- Affichage du graphique ---
        if r["history"]:
            fig = plot_price_history(r["history"])
            st.pyplot(fig)

        # --- Toggle notifications ---
        if st.button("Activer/Désactiver notifications", key=f"notif-{idx}"):
            r["notifications"] = not r["notifications"]
            save_routes(routes)
            st.rerun()

        # --- Supprimer ---
        if st.button("Supprimer ce suivi", key=f"del-{idx}"):
            routes.pop(idx)
            save_routes(routes)
            st.rerun()
