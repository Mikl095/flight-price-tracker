import streamlit as st
from datetime import date, datetime
from utils import ensure_data_file, load_routes, save_routes, plot_price_history
import random

# --- Initialisation ---
ensure_data_file()
routes = load_routes()

st.set_page_config(page_title="Flight Price Tracker", layout="wide")
st.title("✈️ Flight Price Tracker – Paris → Destinations personnalisables")

st.write(
    "Suivez vos vols depuis Paris, saisissez n'importe quelle destination (code IATA) "
    "ou utilisez les suggestions : Tokyo (TYO), Osaka (OSA), Sapporo (SPK), Guadeloupe (PTP)."
)

# -------------------------------------------------------------------
# Sidebar : ajouter un vol
# -------------------------------------------------------------------
st.sidebar.header("➕ Ajouter un vol")

origin = st.sidebar.text_input("Origine", "PAR")

dest_options = ["TYO", "OSA", "SPK", "PTP", "Autre…"]
destination = st.sidebar.selectbox("Destination (sélection ou saisie libre)", dest_options)
if destination == "Autre…":
    destination = st.sidebar.text_input("Code IATA de votre destination", value="")

departure_date = st.sidebar.date_input("Départ", date.today())
return_date = st.sidebar.date_input("Retour", date.today())

target_price = st.sidebar.number_input("Seuil d’alerte (€)", min_value=50, value=350)
tracking_per_day = st.sidebar.number_input("Nombre de trackings par jour", min_value=1, max_value=24, value=1)

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
            "tracking_per_day": tracking_per_day,
            "last_tracked": None,
            "history": []
        }
        routes.append(new_entry)
        save_routes(routes)
        st.sidebar.success(f"Trajet ajouté : {origin} → {destination.upper()} ✔️")

# -------------------------------------------------------------------
# Fonction de tracking automatique “cloud friendly”
# -------------------------------------------------------------------
def simulate_auto_tracking(route):
    """Simule le tracking automatique selon tracking_per_day."""
    now = datetime.now()

    # Sécurité : créer les clés manquantes
    last_tracked_str = route.get('last_tracked')
    route.setdefault('history', [])

    last = datetime.fromisoformat(last_tracked_str) if last_tracked_str else None
    interval = 24 / max(route.get('tracking_per_day', 1), 1)  # heures

    # Combien de fois le tracking aurait dû se produire depuis last_tracked ?
    updates_needed = 0
    if last:
        hours_passed = (now - last).total_seconds() / 3600
        updates_needed = int(hours_passed // interval)
    else:
        updates_needed = 1  # première fois

    for _ in range(updates_needed):
        # Simulation : prix aléatoire pour test
        price = random.randint(200, 800)
        route['history'].append({
            "date": str(now),
            "price": price
        })
        route['last_tracked'] = str(now)

# --- Mettre à jour tous les vols automatiquement ---
for route in routes:
    simulate_auto_tracking(route)
save_routes(routes)

# -------------------------------------------------------------------
# Section principale : vols suivis
# -------------------------------------------------------------------
st.header("📊 Vos vols surveillés")

if not routes:
    st.info("Aucun vol surveillé. Ajoutez un vol dans la barre latérale.")
else:
    for idx, route in enumerate(routes):
        st.subheader(f"✈️ {route['origin']} → {route['destination']}")
        st.write(
            f"**Dates :** {route['departure']} → {route['return']} • "
            f"**Seuil :** {route['target_price']}€ • "
            f"**Tracking/jour :** {route.get('tracking_per_day', 1)}"
        )

        # Bouton pour update manuel
        if st.button(f"Mettre à jour le prix maintenant", key=f"update-{idx}"):
            simulate_auto_tracking(route)
            save_routes(routes)
            st.write(f"🎟️ Prix actuel : {route['history'][-1]['price']}€")
            if route['history'][-1]['price'] <= route['target_price']:
                st.success(f"🔥 Prix sous votre seuil ({route['target_price']}€) !")

        # Graphique historique
        if route["history"]:
            fig = plot_price_history(route["history"])
            st.pyplot(fig)

        # Supprimer le suivi
        if st.button(f"Supprimer ce suivi", key=f"delete-{idx}"):
            routes.pop(idx)
            save_routes(routes)
            st.warning("Vol supprimé ❌")
            st.experimental_rerun()
            
