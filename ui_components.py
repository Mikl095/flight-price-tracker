# ui_components.py
import streamlit as st
from utils.storage import load_routes, save_routes, ensure_route_fields, sanitize_dict
from utils.plotting import plot_price_history
from datetime import datetime, timedelta
import uuid

def render_top_bar():
    st.title("Flight Price Tracker")
    st.markdown("---")

def render_dashboard(routes):
    st.header("Tableau de bord")
    for r in routes:
        st.subheader(f"{r['origin']} → {r['destination']}")
        if r.get("history"):
            st.pyplot(plot_price_history(r["history"]))
        else:
            st.info("Pas d'historique de prix")

def render_add_tab(routes):
    st.header("Ajouter un suivi")
    with st.form("add_route_form"):
        origin = st.text_input("Aéroport de départ")
        destination = st.text_input("Aéroport de destination")
        departure = st.date_input("Date de départ")
        stay_min = st.number_input("Séjour min (jours)", value=1, min_value=1)
        stay_max = st.number_input("Séjour max (jours)", value=1, min_value=1)
        target_price = st.number_input("Prix cible (€)", value=100)
        direct_only = st.checkbox("Vol direct uniquement")
        notifications = st.checkbox("Notifications")
        email = st.text_input("Email pour notifications")
        submit = st.form_submit_button("Ajouter")

        if submit:
            new_route = {
                "id": str(uuid.uuid4()),
                "origin": origin,
                "destination": destination,
                "departure": departure.isoformat(),
                "stay_min": stay_min,
                "stay_max": stay_max,
                "target_price": target_price,
                "direct_only": direct_only,
                "notifications": notifications,
                "email": email,
                "history": []
            }
            ensure_route_fields(new_route)
            routes.append(new_route)
            save_routes(routes)
            st.success("Suivi ajouté !")

def render_edit_tab(route, routes):
    st.header("Modifier un suivi")
    with st.form(f"edit_route_{route['id']}"):
        origin = st.text_input("Aéroport de départ", value=route.get("origin", ""))
        destination = st.text_input("Aéroport de destination", value=route.get("destination", ""))
        departure_val = route.get("departure")
        departure = st.date_input(
            "Date de départ",
            value=datetime.fromisoformat(departure_val) if departure_val else datetime.today()
        )
        stay_min = st.number_input("Séjour min (jours)", value=route.get("stay_min",1), min_value=1)
        stay_max = st.number_input("Séjour max (jours)", value=route.get("stay_max",1), min_value=1)
        target_price = st.number_input("Prix cible (€)", value=route.get("target_price",100))
        direct_only = st.checkbox("Vol direct uniquement", value=route.get("direct_only", False))
        notifications = st.checkbox("Notifications", value=route.get("notifications", False))
        email = st.text_input("Email pour notifications", value=route.get("email",""))
        submit = st.form_submit_button("Mettre à jour")

        if submit:
            route.update({
                "origin": origin,
                "destination": destination,
                "departure": departure.isoformat(),
                "stay_min": stay_min,
                "stay_max": stay_max,
                "target_price": target_price,
                "direct_only": direct_only,
                "notifications": notifications,
                "email": email
            })
            ensure_route_fields(route)
            save_routes(routes)
            st.success("Suivi mis à jour !")

def render_search_tab(routes):
    st.header("Suggestions de suivi")
    # Simuler une recherche
    df_res = [{"id": str(i), "origin": "PAR", "destination": f"City{i}", "departure": "2025-12-01"} for i in range(5)]
    with st.form("add_from_search"):
        selected_ids = st.multiselect(
            "Sélectionner les résultats à ajouter",
            options=[r["id"] for r in df_res],
            format_func=lambda i: f"{df_res[int(i)]['origin']} → {df_res[int(i)]['destination']} ({df_res[int(i)]['departure']})"
        )
        add_submit = st.form_submit_button("Ajouter")
        if add_submit and selected_ids:
            added = 0
            for r in df_res:
                if r["id"] in selected_ids:
                    new_route = dict(r)
                    ensure_route_fields(new_route)
                    routes.append(new_route)
                    added += 1
            save_routes(routes)
            st.success(f"{added} suivis ajoutés !")
