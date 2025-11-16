import streamlit as st
from datetime import date

from utils import ensure_data_file, load_routes, save_routes, plot_price_history
from amadeus_client import search_flights

# --- Assurer que le fichier de données existe ---
ensure_data_file()

# --- Charger les routes suivies ---
routes = load_routes()

st.title("✈️ Flight Price Tracker – Paris → Destinations personnalisables")

st.write(
    "Suivi automatique des prix des vols depuis Paris. "
    "Vous pouvez ajouter n'importe quelle destination en code IATA, "
    "ou choisir parmi les suggestions : Tokyo (TYO), Osaka (OSA), "
    "Sapporo (SPK) et Guadeloupe (PTP)."
)

# -------------------------------------------------------------------
# Sidebar : ajout d'un nouveau suivi
# -------------------------------------------------------------------

st.sidebar.header("➕ Ajouter un vol à surveiller")

origin = st.sidebar.text_input("Origine", "PAR")

# Destination personnalisable avec suggestions
dest_options = ["TYO", "OSA", "SPK", "PTP", "Autre…"]
destination = st.sidebar.selectbox("Destination (sélection ou saisie libre)", dest_options)

if destination == "Autre…":
    destination = st.sidebar.text_input("Code IATA de votre destination", value="")

departure_date = st.sidebar.date_input("Départ", date.today())
return_date = st.sidebar.date_input("Retour", date.today())

target_price = st.sidebar.number_input("Seuil d’alerte (€)", min_value=50, value=350)

if st.sidebar.button("Ajouter ce suivi"):
    if not destination:
        st.sidebar.error("Veuillez entrer un code IATA pour la destination.")
    else:
        new_entry = {
            "origin": origin,
            "destination": destination.upper(),
            "departure": str(departure_date),
            "return": str(return_date),
            "target_price": target_price,
            "history": []
        }
        routes.append(new_entry)
        save_routes(routes)
        st.sidebar.success(f"Trajet ajouté : {origin} → {destination.upper()} ✔️")

# -------------------------------------------------------------------
# Affichage des routes existantes
# -------------------------------------------------------------------

st.header("📊 Vos vols surveillés")

if not routes:
    st.info("Aucun vol surveillé pour l'instant. Ajoutez un vol dans le menu à gauche.")
else:
    for idx, route in enumerate(routes):

        st.subheader(f"✈️ {route['origin']} → {route['destination']}")

        st.write(
            f"**Dates :** {route['departure']} → {route['return']} • "
            f"**Seuil d’alerte :** {route['target_price']}€"
        )

        # ---- Récupération du prix actuel ----
        flights = search_flights(
            origin=route["origin"],
            destination=route["destination"],
            departure_date=route["departure"],
            return_date=route["return"]
        )

        if "error" in flights:
            st.error("Erreur API Amadeus : " + flights["error"])
            continue

        try:
            price = float(flights[0]["price"]["total"])
        except:
            st.error("Impossible de lire le prix du vol.")
            continue

        st.write(f"🎟️ **Prix actuel : {price}€**")

        # ---- Historique ----
        route["history"].append({
            "date": str(date.today()),
            "price": price
        })
        save_routes(routes)

        # ---- Graphique ----
        if len(route["history"]) > 1:
            fig = plot_price_history(route["history"])
            st.pyplot(fig)

        # ---- Alerte ----
        if price <= route["target_price"]:
            st.success(f"🔥 Prix sous votre seuil ({route['target_price']}€) !")

        # ---- Bouton supprimer ----
        if st.button(f"Supprimer ce suivi", key=f"delete-{idx}"):
            routes.pop(idx)
            save_routes(routes)
            st.warning("Vol supprimé ❌")
            st.experimental_rerun()
