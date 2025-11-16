import streamlit as st
from datetime import date, datetime
from utils.storage import ensure_data_file, load_routes, save_routes
from utils.plotting import plot_price_history
from utils.tracking import simulate_price_tracking  # pour tracking manuel uniquement

# --- Init ---
st.set_page_config(page_title="Flight Price Tracker", layout="wide")
ensure_data_file()
routes = load_routes()

st.title("✈️ Flight Price Tracker – Suivi automatique des vols")
st.write(
    "Suivez vos vols et recevez des alertes par email. "
    "Les mises à jour automatiques sont exécutées via GitHub Actions."
)

# -------------------------------------------------------------------
# Sidebar : ajouter un vol
# -------------------------------------------------------------------
st.sidebar.header("➕ Ajouter un vol")

origin = st.sidebar.text_input("Origine", "PAR")

dest_options = ["TYO", "OSA", "SPK", "PTP", "Autre…"]
destination = st.sidebar.selectbox("Destination", dest_options)
if destination == "Autre…":
    destination = st.sidebar.text_input("Code IATA", "")

departure_date = st.sidebar.date_input("Départ", date.today())
return_date = st.sidebar.date_input("Retour", date.today())
target_price = st.sidebar.number_input("Seuil d’alerte (€)", min_value=50, value=350)
tracking_per_day = st.sidebar.number_input("Tracking/jour", min_value=1, max_value=24, value=2)
email_alert = st.sidebar.checkbox("Alerte email", value=True)

if st.sidebar.button("Ajouter"):
    if destination:
        new_route = {
            "origin": origin.upper(),
            "destination": destination.upper(),
            "departure": str(departure_date),
            "return": str(return_date),
            "target_price": target_price,
            "tracking_per_day": tracking_per_day,
            "notify": email_alert,
            "last_tracked": None,
            "history": []
        }
        routes.append(new_route)
        save_routes(routes)
        st.sidebar.success("Vol ajouté ✔️")
    else:
        st.sidebar.error("Veuillez saisir une destination valide.")

# -------------------------------------------------------------------
# Section principale
# -------------------------------------------------------------------
st.header("📊 Vos vols suivis")

if not routes:
    st.info("Aucun vol suivi. Ajoutez-en dans la barre latérale.")
else:
    for i, route in enumerate(routes):
        st.subheader(f"✈️ {route['origin']} → {route['destination']}")

        cols = st.columns([2, 1])
        with cols[0]:
            st.write(
                f"**Dates :** {route['departure']} → {route['return']} • "
                f"**Seuil :** {route['target_price']}€ • "
                f"**Tracking/jour :** {route['tracking_per_day']} • "
                f"**Alerte mail :** {'Oui' if route['notify'] else 'Non'}"
            )
        with cols[1]:
            if st.button("Mettre à jour maintenant", key=f"update-{i}"):
                simulate_price_tracking(route)
                save_routes(routes)
                st.success("Prix mis à jour ✔️")

        # Graphique historique
        if route["history"]:
            fig = plot_price_history(route["history"])
            st.pyplot(fig)

        # Supprimer
        if st.button("Supprimer", key=f"delete-{i}"):
            routes.pop(i)
            save_routes(routes)
            st.warning("Vol supprimé ❌")
            st.experimental_rerun()
            
