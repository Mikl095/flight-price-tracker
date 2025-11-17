import streamlit as st
import os
import random
from datetime import date, datetime

# ---- Utils ----
from utils.storage import ensure_data_file, load_routes, save_routes
from utils.plotting import plot_price_history

# ---- Email ----
from email_utils import send_email


# =========================================================
# Initialisation
# =========================================================
ensure_data_file()
routes = load_routes()

st.set_page_config(page_title="Flight Price Tracker", layout="wide")
st.title("✈️ Flight Price Tracker – Paris → Destinations personnalisables")


# =========================================================
# ----- SIDEBAR : SECTION EMAIL + TEST EMAIL -----
# =========================================================
st.sidebar.subheader("📧 Test email")
test_email = st.sidebar.text_input("Adresse email de test")

if st.sidebar.button("Envoyer un email de test"):
    from email_utils import send_email
    ok = send_email(
        to=test_email,
        subject="Test SendGrid — OK 🎉",
        html="<p>Votre configuration SendGrid fonctionne !</p>"
    )
    if ok:
        st.sidebar.success("Email envoyé ✔️")
    else:
        st.sidebar.error("Erreur lors de l’envoi ❌ — voir logs")

# =========================================================
# ----- SIDEBAR : AJOUTER UN NOUVEAU VOL -----
# =========================================================
st.sidebar.header("➕ Ajouter un vol à surveiller")

origin = st.sidebar.text_input("Origine", "PAR")

dest_options = ["TYO", "OSA", "SPK", "PTP", "LON", "Autre…"]
destination = st.sidebar.selectbox("Destination", dest_options)

if destination == "Autre…":
    destination = st.sidebar.text_input("Code IATA personnalisé", "")

departure_date = st.sidebar.date_input("Départ", date.today())
return_date = st.sidebar.date_input("Retour", date.today())

target_price = st.sidebar.number_input("Seuil d’alerte (€)", min_value=50, value=350)
tracking_per_day = st.sidebar.number_input("Trackings par jour", min_value=1, max_value=24, value=1)
notifications = st.sidebar.checkbox("Activer les notifications email", value=False)


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


# =========================================================
# ----- SIMULATION — TEMPORAIRE EN ATTENDANT AMADEUS -----
# =========================================================
def simulate_price(route):
    now = datetime.now()
    price = random.randint(200, 900)

    route["history"].append({
        "date": now.isoformat(),
        "price": price
    })
    route["last_tracked"] = now.isoformat()


# =========================================================
# ----- SECTION PRINCIPALE -----
# =========================================================
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

        # --- Mise à jour manuelle ---
        if st.button("Mettre à jour maintenant", key=f"update-{idx}"):
            simulate_price(r)
            save_routes(routes)

            last = r["history"][-1]["price"]
            st.info(f"Prix actuel : {last} €")

            if last <= r["target_price"]:
                st.success("🔥 Sous votre seuil !")

                if r.get("notifications"):
                    send_email(
                        to=test_email,
                        subject=f"Prix bas détecté pour {r['origin']} → {r['destination']}",
                        html=f"<p>Prix actuel : <b>{last} €</b></p>"
                    )

            st.rerun()

        # --- Graphique ---
        if r["history"]:
            fig = plot_price_history(r["history"])
            st.pyplot(fig)

        # --- Toggle notifictions ---
        if st.button("Notifications ON/OFF", key=f"notif-{idx}"):
            r["notifications"] = not r["notifications"]
            save_routes(routes)
            st.rerun()

        # --- Supprimer ---
        if st.button("Supprimer ce suivi", key=f"del-{idx}"):
            routes.pop(idx)
            save_routes(routes)
            st.rerun()
