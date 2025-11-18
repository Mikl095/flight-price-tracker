# app.py
import streamlit as st
from datetime import date, datetime, timedelta
import uuid

from utils.data import (
    ensure_data_file, load_routes, save_routes,
    load_email_config, save_email_config, append_log, count_updates_last_24h, ensure_route_fields
)
from utils.layout import render_header, render_top_actions, render_dashboard_table, render_route_card
from utils.forms import route_form_from_row, route_form_empty
from utils.actions import add_route_from_dict, bulk_update_sim, send_test_email_for_route
from utils.json_utils import sanitize_dict

# ---------- Init ----------
ensure_data_file()
routes = load_routes()
email_cfg = load_email_config()

st.set_page_config(page_title="Flight Price Tracker", layout="wide")
render_header(len(routes), theme="light")  # Theme A = light

# Top actions (add, bulk update, export)
render_top_actions()

# ---------- Tabs ----------
tab_dashboard, tab_add, tab_config, tab_search = st.tabs(
    ["Dashboard", "Ajouter un suivi", "Configuration", "Recherche (simu)"]
)

# ---------------- Dashboard ----------------
with tab_dashboard:
    st.header("📊 Dashboard")
    if not routes:
        st.info("Aucun suivi — ajoute ton premier suivi dans l'onglet « Ajouter un suivi ».")
    else:
        # metrics + table
        total = len(routes)
        notif_on = sum(1 for r in routes if r.get("notifications"))
        updates_24h = sum(count_updates_last_24h(r) for r in routes)
        st.metric("Suivis", total)
        st.metric("Notifications ON", notif_on)
        st.metric("Mises à jour (24h)", updates_24h)

        st.markdown("---")
        render_dashboard_table(routes, email_cfg)

        st.markdown("### Détails des suivis")
        for idx, r in enumerate(routes):
            ensure_route_fields(r)
            changed = render_route_card(r, idx, email_cfg)
            if changed:
                save_routes(routes)
                append_log(f"{datetime.now().isoformat()} - route updated {r.get('id')}")
                st.experimental_rerun()

# ---------------- Add ----------------
with tab_add:
    st.header("➕ Ajouter un suivi")
    with st.form("add_form"):
        form_values = route_form_empty()
        submitted = st.form_submit_button("Ajouter le suivi")
    if submitted:
        # sanitize and create
        new = add_route_from_dict(form_values)
        routes.append(new)
        save_routes(routes)
        append_log(f"{datetime.now().isoformat()} - Added route {new['id']}")
        st.success("Suivi ajouté ✔")
        st.experimental_rerun()

# ---------------- Config ----------------
with tab_config:
    st.header("⚙️ Configuration")
    st.subheader("Paramètres email")
    ge = st.text_input("Email global (pour notifications)", value=email_cfg.get("email",""))
    ge_on = st.checkbox("Activer notifications globales", value=email_cfg.get("enabled", False))
    if st.button("Enregistrer paramètres"):
        save_email_config({"email": ge, "enabled": bool(ge_on)})
        append_log(f"{datetime.now().isoformat()} - Saved email config")
        st.success("Paramètres enregistrés")
        st.experimental_rerun()

# ---------------- Search (simu) ----------------
with tab_search:
    st.header("🔎 Recherche & Suggestions (simulation)")
    origins = st.text_input("Origines (IATA séparés par ,)", value="PAR").upper()
    dests = st.text_input("Destinations (IATA séparés par ,)", value="NRT,HND,KIX").upper()
    start = st.date_input("Date départ approximative", date.today()+timedelta(days=90))
    window = st.number_input("Plage ± (jours)", min_value=0, max_value=30, value=7)
    samples = st.number_input("Échantillons/option", min_value=3, max_value=30, value=8)

    if st.button("Lancer recherche (simu)"):
        # simple simulation delegated to actions module for clarity
        new_entries = []
        for o in [x.strip() for x in origins.split(",") if x.strip()]:
            for d in [x.strip() for x in dests.split(",") if x.strip()]:
                for delta in range(-window, window+1):
                    dep = start + timedelta(days=delta)
                    for s in range(samples):
                        price = int(100 + (hash(f"{o}{d}{dep}{s}") % 1100))
                        new_entries.append({
                            "origin": o, "destination": d, "departure": dep.isoformat(),
                            "stay_days": 7, "price": price
                        })
        st.success(f"Simulation : {len(new_entries)} résultats")
        st.dataframe(new_entries[:200])
        # allow quick add
        idx = st.number_input("Index à ajouter comme suivi", min_value=0, max_value=max(0, len(new_entries)-1), value=0)
        if st.button("Ajouter sélection comme suivi"):
            row = new_entries[int(idx)]
            new = add_route_from_dict({
                "origin": row["origin"], "destination": row["destination"],
                "departure": row["departure"], "target_price": float(row["price"])*0.9
            })
            routes.append(new)
            save_routes(routes)
            append_log(f"{datetime.now().isoformat()} - Added from search {new['id']}")
            st.success("Suivi créé depuis la recherche.")
            st.experimental_rerun()
