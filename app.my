import streamlit as st
from datetime import date, datetime
from utils import ensure_data_file, load_routes, save_routes, plot_price_history
import random

# Initialisation
ensure_data_file()
routes = load_routes()

st.set_page_config(page_title="Flight Price Tracker", layout="wide")
st.title("✈️ Flight Price Tracker – Paris → Destinations personnalisables")

st.write("Ajoutez des vols, activez ou non les notifications, et laissez GitHub Actions tracker automatiquement vos prix.")


# -------------------------------------------------------
# Sidebar : Ajouter un vol
# -------------------------------------------------------
st.sidebar.header("➕ Ajouter un vol")

origin = st.sidebar.text_input("Origine", "PAR")

dest_default = ["TYO", "OSA", "SPK", "PTP", "Autre…"]
destination = st.sidebar.selectbox("Destination", dest_default)

if destination == "Autre…":
    destination = st.sidebar.text_input("Code IATA", "")

departure_date = st.sidebar.date_input("Départ", date.today())
return_date = st.sidebar.date_input("Retour", date.today())

target_price = st.sidebar.number_input("Seuil d’alerte (€)", value=350)
tracking_per_day = st.sidebar.number_input("Trackings par jour", value=2, min_value=1, max_value=24)

notifications_enabled = st.sidebar.checkbox("Notifications activées", value=True)

if st.sidebar.button("Ajouter"):
    if not destination:
        st.sidebar.error("Veuillez entrer un code IATA.")
    else:
        new_route = {
            "origin": origin,
            "destination": destination.upper(),
            "departure": str(departure_date),
            "return": str(return_date),
            "target_price": target_price,
            "tracking_per_day": tracking_per_day,
            "notifications_enabled": notifications_enabled,
            "last_tracked": None,
            "history": []
        }
        routes.append(new_route)
        save_routes(routes)
        st.sidebar.success(f"Vol ajouté : {origin} → {destination.upper()}")


# -------------------------------------------------------
# Simulation de tracking
# -------------------------------------------------------
def simulate_auto_tracking(route):
    now = datetime.now()
    route.setdefault("history", [])

    last = datetime.fromisoformat(route["last_tracked"]) if route.get("last_tracked") else None
    interval = 24 / max(route.get("tracking_per_day", 1), 1)

    updates_needed = 1
    if last:
        hours_passed = (now - last).total_seconds() / 3600
        updates_needed = int(hours_passed // interval)

    for _ in range(updates_needed):
        price = random.randint(200, 900)

        route["history"].append({
            "date": str(now),
            "price": price
        })

        route["last_tracked"] = str(now)


# Auto tracking
for route in routes:
    simulate_auto_tracking(route)
save_routes(routes)


# -------------------------------------------------------
# Liste des vols
# -------------------------------------------------------
st.header("📊 Vos vols suivis")

if not routes:
    st.info("Ajoutez un vol dans la barre latérale.")
else:
    for idx, route in enumerate(routes):
        st.subheader(f"{route['origin']} → {route['destination']}")

        st.write(
            f"📅 {route['departure']} → {route['return']} • "
            f"🎯 Seuil {route['target_price']}€ • "
            f"⏱ Track/jour : {route['tracking_per_day']} • "
            f"🔔 Notifs : {route['notifications_enabled']}"
        )

        if route["history"]:
            latest = route["history"][-1]["price"]
            st.write(f"💶 Dernier prix : **{latest} €**")

            if latest <= route["target_price"] and route["notifications_enabled"]:
                st.success("🔥 Prix sous le seuil !")

        fig = plot_price_history(route["history"])
        st.pyplot(fig)

        if st.button(f"Supprimer", key=f"del{idx}"):
            routes.pop(idx)
            save_routes(routes)
            st.experimental_rerun()
