import streamlit as st
from datetime import date

from amadeus_client import search_flights
from utils import load_routes, save_routes, plot_price_history

st.title("✈️ Flight Price Tracker – Paris ➜ Japon & Guadeloupe")

routes = load_routes()

# --- Sidebar : Ajout d’un nouveau suivi ---
st.sidebar.header("Ajouter un vol à surveiller")

origin = st.sidebar.text_input("Origine", "PAR")

destination = st.sidebar.selectbox(
    "Destination",
    ["TYO", "OSA", "SPK", "PTP"],
    help="Tokyo / Osaka / Sapporo / Guadeloupe"
)

departure_date = st.sidebar.date_input("Départ", date.today())
return_date = st.sidebar.date_input("Retour", date.today())

target_price = st.sidebar.number_input("Seuil d’alerte (€)", 300)

if st.sidebar.button("Ajouter ce suivi"):
    new_entry = {
        "origin": origin,
        "destination": destination,
        "departure": str(departure_date),
        "return": str(return_date),
        "target_price": target_price,
        "history": []
    }
    routes.append(new_entry)
    save_routes(routes)
    st.sidebar.success("Ajouté ✔️")

# --- Affichage des trajets suivis ---
st.subheader("Vos vols surveillés")

if not routes:
    st.info("Aucun vol surveillé pour le moment.")
else:
    for route in routes:
        st.markdown(f"### ✈️ {route['origin']} → {route['destination']}")

        flights = search_flights(
            route["origin"],
            route["destination"],
            route["departure"],
            route["return"]
        )

        if "error" in flights:
            st.error(flights["error"])
            continue

        price = float(flights[0]["price"]["total"])
        st.write(f"Prix actuel : **{price}€**")

        # Sauvegarde historique
        route["history"].append({
            "date": str(date.today()),
            "price": price
        })
        save_routes(routes)

        # Graphique
        if len(route["history"]) > 1:
            fig = plot_price_history(route["history"])
            st.pyplot(fig)

        # Alerte
        if price <= route["target_price"]:
            st.success(f"🔥 Prix sous votre seuil ({route['target_price']}€) !")
