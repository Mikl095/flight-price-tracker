# ui_components.py
import streamlit as st
from datetime import datetime, timedelta
from utils.storage import load_routes, save_routes, ensure_route_fields, sanitize_dict
from utils.email_utils import send_email
from utils.plotting import plot_price_history
import uuid
import pandas as pd

def render_top_bar():
    st.title("Flight Price Tracker")
    st.markdown("---")

def render_dashboard(routes):
    st.subheader("Suivis existants")
    if not routes:
        st.info("Aucun suivi disponible.")
        return
    for r in routes:
        ensure_route_fields(r)
        col1, col2 = st.columns([3,1])
        with col1:
            st.markdown(f"**{r['origin']} → {r['destination']}**")
            st.markdown(f"Départ: {r['departure']} | Retour: {r.get('return', 'N/A')} | Prix cible: {r['target_price']}€")
        with col2:
            if st.button("Éditer", key=f"edit_{r['id']}"):
                st.session_state["edit_id"] = r["id"]

def render_add_tab(routes):
    st.subheader("Ajouter un suivi")
    with st.form("add_form"):
        origin = st.text_input("Origine")
        destination = st.text_input("Destination")
        departure = st.date_input("Départ")
        return_date = st.date_input("Retour (facultatif)", value=None)
        stay_min = st.number_input("Durée minimale du séjour (jours)", min_value=1, value=1)
        stay_max = st.number_input("Durée maximale du séjour (jours)", min_value=1, value=7)
        target_price = st.number_input("Prix cible (€)", min_value=1.0, value=100.0)
        notifications = st.checkbox("Activer notifications")
        email = st.text_input("Email pour notifications")
        add_submit = st.form_submit_button("Ajouter")

    if add_submit:
        new_id = str(uuid.uuid4())
        r = {
            "id": new_id,
            "origin": origin,
            "destination": destination,
            "departure": departure.isoformat(),
            "return": return_date.isoformat() if return_date else None,
            "stay_min": stay_min,
            "stay_max": stay_max,
            "target_price": target_price,
            "notifications": notifications,
            "email": email,
            "history": []
        }
        ensure_route_fields(r)
        routes.append(r)
        save_routes(routes)
        st.success(f"Suivi ajouté pour {origin} → {destination}")

def render_edit_tab(routes):
    edit_id = st.session_state.get("edit_id")
    if not edit_id:
        return

    route = next((r for r in routes if r["id"] == edit_id), None)
    if not route:
        st.error("Suivi introuvable")
        return

    ensure_route_fields(route)
    st.subheader(f"Éditer suivi {route['origin']} → {route['destination']}")
    with st.form(f"edit_form_{edit_id}"):
        origin = st.text_input("Origine", value=route['origin'])
        destination = st.text_input("Destination", value=route['destination'])
        departure = st.date_input("Départ", value=datetime.fromisoformat(route['departure']))
        # si pas de retour, prioriser stay
        if route.get('return'):
            return_date_val = datetime.fromisoformat(route['return'])
        else:
            return_date_val = departure + timedelta(days=route.get("stay_max", 1))
        return_date = st.date_input("Retour (facultatif)", value=return_date_val)
        stay_min = st.number_input("Durée minimale du séjour (jours)", min_value=1, value=route.get("stay_min",1))
        stay_max = st.number_input("Durée maximale du séjour (jours)", min_value=1, value=route.get("stay_max",7))
        target_price = st.number_input("Prix cible (€)", min_value=1.0, value=route.get("target_price",100.0))
        notifications = st.checkbox("Activer notifications", value=route.get("notifications", False))
        email = st.text_input("Email pour notifications", value=route.get("email",""))
        save_submit = st.form_submit_button("Sauvegarder")

    if save_submit:
        route.update({
            "origin": origin,
            "destination": destination,
            "departure": departure.isoformat(),
            "return": return_date.isoformat() if return_date else None,
            "stay_min": stay_min,
            "stay_max": stay_max,
            "target_price": target_price,
            "notifications": notifications,
            "email": email
        })
        save_routes(routes)
        st.success("Suivi mis à jour")
        st.session_state.pop("edit_id")

def render_search_tab(routes):
    st.subheader("Recherche suggestions")
    df_res = pd.DataFrame([{"id": r["id"], "origin": r["origin"], "destination": r["destination"], "departure": r["departure"]} for r in routes])
    if df_res.empty:
        st.info("Pas de suggestions disponibles")
        return

    with st.form("add_from_search"):
        selected_ids = st.multiselect(
            "Sélectionner les résultats à ajouter",
            options=df_res["id"].tolist(),
            format_func=lambda i: f"{df_res.loc[df_res['id']==i,'origin'].values[0]} → {df_res.loc[df_res['id']==i,'destination'].values[0]} ({df_res.loc[df_res['id']==i,'departure'].values[0]})"
        )
        add_submit = st.form_submit_button("Ajouter")

    if add_submit and selected_ids:
        created = 0
        for sid in selected_ids:
            if sid not in [r["id"] for r in routes]:
                r = next((r for r in routes if r["id"]==sid), None)
                if r:
                    routes.append(r)
                    created += 1
        save_routes(routes)
        st.success(f"{created} suivis ajoutés")
