import streamlit as st
import random
import os
from datetime import date, datetime

from utils.storage import ensure_data_file, load_routes, save_routes
from utils.plotting import plot_price_history
from email_utils import send_email


# ----------------------------------------------------------
# INITIALISATION
# ----------------------------------------------------------
ensure_data_file()
routes = load_routes()

st.set_page_config(page_title="Flight Price Tracker", layout="wide")
st.title("✈️ Flight Price Tracker — Simulation")


# ----------------------------------------------------------
# TEST EMAIL (dans la sidebar)
# ----------------------------------------------------------
st.sidebar.header("📧 Notifications Email")

test_email = st.sidebar.text_input("Adresse email test", "")
if st.sidebar.button("Envoyer un test"):
    if not test_email:
        st.sidebar.error("Entrez une adresse email.")
    else:
        ok, status = send_email(
            to=test_email,
            subject="Test SendGrid — Flight Tracker",
            html="<h3>Test OK 🎉</h3><p>Votre configuration fonctionne.</p>"
        )
        if ok:
            st.sidebar.success(f"Email envoyé avec succès ! (status {status})")
        else:
            st.sidebar.error(f"Erreur d'envoi (status {status})")


# ----------------------------------------------------------
# AJOUT D’UN SUIVI
# ----------------------------------------------------------
st.sidebar.header("➕ Ajouter un vol")

origin = st.sidebar.text_input("Origine", "PAR")

dest_options = ["TYO", "OSA", "SPK", "PTP", "LON", "Autre…"]
destination = st.sidebar.selectbox("Destination", dest_options)

if destination == "Autre…":
    destination = st.sidebar.text_input("Code IATA", "")

departure_date = st.sidebar.date_input("Départ", date.today())
departure_flex = st.sidebar.number_input("Flexibilité départ (± jours)", 0, 7, 0)

stay_min = st.sidebar.number_input("Séjour minimum (jours)", 0, 60, 0)
stay_max = st.sidebar.number_input("Séjour maximum (jours)", 0, 60, 0)

email_for_route = st.sidebar.text_input("Email pour ce suivi", "")

target_price = st.sidebar.number_input("Seuil (€)", 50, 3000, 350)
tracking_per_day = st.sidebar.number_input("Trackings/jour", 1, 24, 1)

notifications = st.sidebar.checkbox("Activer notifications", False)


if st.sidebar.button("Ajouter ce suivi"):
    if not destination:
        st.sidebar.error("Code IATA invalide.")
    else:
        new_entry = {
            "origin": origin,
            "destination": destination.upper(),
            "departure": str(departure_date),
            "departure_flex": departure_flex,
            "stay_min": stay_min,
            "stay_max": stay_max,
            "email": email_for_route,
            "target_price": target_price,
            "tracking_per_day": tracking_per_day,
            "notifications": notifications,
            "last_tracked": None,
            "history": []
        }

        routes.append(new_entry)
        save_routes(routes)
        st.sidebar.success("Suivi ajouté ✔")
        st.rerun()


# ----------------------------------------------------------
# SIMULATION
# (remplacé plus tard par Amadeus)
# ----------------------------------------------------------
def simulate_price(route):
    now = datetime.now()
    price = random.randint(200, 900)

    route["history"].append({
        "date": now.isoformat(),
        "price": price
    })
    route["last_tracked"] = now.isoformat()


# ----------------------------------------------------------
# AFFICHAGE DES SUIVIS
# ----------------------------------------------------------
st.header("📊 Vos vols surveillés")

if not routes:
    st.info("Aucun suivi.")
else:

    for idx, r in enumerate(routes):
        st.subheader(f"✈️ {r['origin']} → {r['destination']}")

        st.write(
            f"**Départ :** {r['departure']} (±{r['departure_flex']} j) • "
            f"**Séjour :** {r['stay_min']}–{r['stay_max']} j • "
            f"**Seuil :** {r['target_price']}€ • "
            f"**Email :** {r.get('email','Aucun')} • "
            f"**Notif :** {'ON 🔔' if r.get('notifications') else 'OFF'}"
        )

        # ❗ Mise à jour (simulation)
        if st.button("Mettre à jour maintenant", key=f"update-{idx}"):
            simulate_price(r)
            save_routes(routes)

            last = r["history"][-1]["price"]
            st.info(f"Prix actuel : {last} €")

            if last <= r["target_price"]:
                st.success("🔥 Sous votre seuil !")

            st.rerun()

        # --- Graphique
        if r["history"]:
            fig = plot_price_history(r["history"])
            st.pyplot(fig)

        # --- Toggle notifications
        if st.button("Activer/Désactiver notifications", key=f"notif-{idx}"):
            r["notifications"] = not r["notifications"]
            save_routes(routes)
            st.rerun()

        # ----------------------------------------------------------
        # 🔧 FORMULAIRE D’ÉDITION DU SUIVI
        # ----------------------------------------------------------
        with st.expander("✏️ Modifier ce suivi"):
            with st.form(key=f"form-edit-{idx}"):
                new_target = st.number_input(
                    "Seuil (€)",
                    50, 3000,
                    r["target_price"]
                )
                new_email = st.text_input(
                    "Email",
                    value=r.get("email", "")
                )
                new_flex = st.number_input(
                    "Flex départ (± jours)",
                    0, 7,
                    r.get("departure_flex", 0)
                )
                new_stay_min = st.number_input(
                    "Séjour min (jours)",
                    0, 60,
                    r.get("stay_min", 0)
                )
                new_stay_max = st.number_input(
                    "Séjour max (jours)",
                    0, 60,
                    r.get("stay_max", 0)
                )

                submitted = st.form_submit_button("💾 Enregistrer les modifications")

            if submitted:
                r["target_price"] = new_target
                r["email"] = new_email
                r["departure_flex"] = new_flex
                r["stay_min"] = new_stay_min
                r["stay_max"] = new_stay_max
                save_routes(routes)
                st.success("Modifications enregistrées ✔")
                st.rerun()

        # --- Supprimer
        if st.button("🗑️ Supprimer", key=f"delete-{idx}"):
            routes.pop(idx)
            save_routes(routes)
            st.rerun()
