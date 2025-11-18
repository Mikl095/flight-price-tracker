# app.py - Flight Price Tracker (Dashboard C)
import streamlit as st
from datetime import date, datetime, timedelta
import random
import uuid
import os
import pandas as pd

from utils.storage import (
    ensure_data_file, load_routes, save_routes, load_email_config,
    save_email_config, append_log, count_updates_last_24h, ensure_route_fields
)
from utils.plotting import plot_price_history
from exporters import export_csv, export_pdf, export_xlsx
from email_utils import send_email

# ----------------- INIT -----------------
ensure_data_file()
routes = load_routes()
email_cfg = load_email_config()

st.set_page_config(page_title="Flight Price Tracker", layout="wide")
st.title("✈️ Flight Price Tracker — Dashboard & Notifications (Simu)")

# ---------------- Sidebar: globals & add -----------------
st.sidebar.header("⚙️ Paramètres globaux")

global_email = st.sidebar.text_input(
    "Email global (pour notifications)", value=email_cfg.get("email", "")
)
global_enabled = st.sidebar.checkbox(
    "Activer notifications globales", value=email_cfg.get("enabled", False)
)

if st.sidebar.button("Enregistrer paramètres"):
    save_email_config({"email": global_email, "enabled": bool(global_enabled)})
    st.sidebar.success("Paramètres enregistrés")
    append_log(f"{datetime.now().isoformat()} - Global email saved: {global_email}")

st.sidebar.markdown("---")
st.sidebar.write("SendGrid: ajoute ta clé `SENDGRID_KEY` dans les Secrets (GitHub + Streamlit).")

# Add route
st.sidebar.header("➕ Ajouter un suivi")
origin = st.sidebar.text_input("Origine (IATA)", "PAR")
destination = st.sidebar.text_input("Destination (IATA)", "TYO")
departure_date = st.sidebar.date_input("Date départ (approx.)", date.today() + timedelta(days=90))

departure_flex_days = st.sidebar.number_input(
    "Plage départ ± jours", min_value=0, max_value=30, value=1
)
return_airport = st.sidebar.text_input("Aéroport retour (IATA) - vide = même", "")
stay_min = st.sidebar.number_input("Séjour min (jours)", min_value=1, max_value=365, value=6)
stay_max = st.sidebar.number_input("Séjour max (jours)", min_value=1, max_value=365, value=10)
return_flex_days = st.sidebar.number_input("Plage retour ± jours", min_value=0, max_value=30, value=1)

# float-safe for number_input
target_price = st.sidebar.number_input("Seuil alerte (€)", min_value=1.0, value=450.0, step=1.0)

tracking_per_day = st.sidebar.number_input("Trackings par jour", min_value=1, max_value=24, value=2)
notifications_on = st.sidebar.checkbox("Activer notifications pour ce vol", value=True)
min_bags = st.sidebar.number_input("Min bagages (préférence)", min_value=0, max_value=5, value=0)
direct_only = st.sidebar.checkbox("Vol direct uniquement (préférence)", value=False)
max_stops = st.sidebar.selectbox("Max escales (préférence)", ["any", 0, 1, 2])
avoid_airlines = st.sidebar.text_input("Compagnies à éviter (IATA, séparées par ,)", value="")
preferred_airlines = st.sidebar.text_input("Compagnies préférées (IATA, séparées par ,)", value="")
route_email = st.sidebar.text_input("Email pour ce suivi (laisser vide = email global)", "")

if st.sidebar.button("Ajouter ce vol"):
    new = {
        "id": str(uuid.uuid4()),
        "origin": origin.upper(),
        "destination": destination.upper(),
        "departure": str(departure_date),
        "departure_flex_days": int(departure_flex_days),
        "return": str((departure_date + timedelta(days=stay_min))),
        "return_airport": (return_airport.upper() if return_airport else None),
        "stay_min": int(stay_min),
        "stay_max": int(stay_max),
        "return_flex_days": int(return_flex_days),
        "target_price": float(target_price),
        "tracking_per_day": int(tracking_per_day),
        "notifications": bool(notifications_on),
        "min_bags": int(min_bags),
        "direct_only": bool(direct_only),
        "max_stops": max_stops,
        "avoid_airlines": [a.strip().upper() for a in avoid_airlines.split(",") if a.strip()],
        "preferred_airlines": [a.strip().upper() for a in preferred_airlines.split(",") if a.strip()],
        "email": route_email.strip(),
        "history": [],
        "last_tracked": None,
        "stats": {}
    }
    routes.append(new)
    save_routes(routes)
    append_log(f"{datetime.now().isoformat()} - Added route {new['id']}")
    st.success("Vol ajouté ✔")
    st.rerun()

# ---------------- Main layout: keep previous dashboard style + extras ----------------
st.header("📊 Dashboard")

if not routes:
    st.info("Aucun suivi — ajoute un vol dans la barre latérale.")
else:
    # summary
    total = len(routes)
    total_with_notif = sum(1 for r in routes if r.get("notifications"))
    updates_24h = sum(count_updates_last_24h(r) for r in routes)
    colA, colB, colC = st.columns(3)
    colA.metric("Suivis total", total)
    colB.metric("Suivis avec notifications", total_with_notif)
    colC.metric("Mises à jour (24h)", updates_24h)

    st.markdown("---")

    # legacy-style list (vertical cards) while keeping extras
    for idx, r in enumerate(routes):
        ensure_route_fields(r)
        st.subheader(f"{r['origin']} → {r['destination']}  (id: {r['id'][:8]})")

        # first row info
        cols = st.columns([2, 1, 1, 1])
        with cols[0]:
            st.write(
                f"**Dates :** {r.get('departure')} (±{r.get('departure_flex_days',0)} j) → "
                f"{r.get('return')} (±{r.get('return_flex_days',0)} j)\n\n"
                f"**Séjour :** {r.get('stay_min')}–{r.get('stay_max')} j\n\n"
                f"**Seuil :** {r.get('target_price')}€\n\n"
                f"**Email :** {r.get('email') or global_email or '—'}\n\n"
                f"**Bagages min :** {r.get('min_bags',0)} • "
                f"**Direct only :** {r.get('direct_only')} • "
                f"**Max stops :** {r.get('max_stops')}"
            )
        with cols[1]:
            if st.button("Mettre à jour", key=f"update_{idx}"):
                price = random.randint(150, 900)
                r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
                r["last_tracked"] = datetime.now().isoformat()
                save_routes(routes)
                append_log(f"{datetime.now().isoformat()} - Manual update {r['id']} price={price}")
                st.rerun()
        with cols[2]:
            # notif on/off button (explicit)
            if r.get("notifications"):
                if st.button("Désactiver notif", key=f"notif_off_{idx}"):
                    r["notifications"] = False
                    save_routes(routes)
                    append_log(f"{datetime.now().isoformat()} - Notifications OFF {r['id']}")
                    st.rerun()
            else:
                if st.button("Activer notif", key=f"notif_on_{idx}"):
                    r["notifications"] = True
                    save_routes(routes)
                    append_log(f"{datetime.now().isoformat()} - Notifications ON {r['id']}")
                    st.rerun()
        with cols[3]:
            if st.button("Supprimer", key=f"del_{idx}"):
                append_log(f"{datetime.now().isoformat()} - Delete route {r['id']}")
                routes.pop(idx)
                save_routes(routes)
                st.rerun()

        # small actions row
        a1, a2, a3 = st.columns([1, 1, 1])
        with a1:
            if st.button("Envoyer test mail", key=f"testmail_{idx}"):
                recipient = r.get("email") or global_email
                if not recipient:
                    st.warning("Aucune adresse email configurée (route/global).")
                else:
                    ok, status = send_email(
                        recipient,
                        f"Test alerte {r['origin']}→{r['destination']}",
                        "<p>Test d'alerte</p>"
                    )
                    st.info("Email envoyé" if ok else f"Erreur d'envoi (status {status})")
                    append_log(f"{datetime.now().isoformat()} - Test mail {r['id']} -> {recipient} ok={ok} status={status}")
        with a2:
            st.write(f"Last tracked: {r.get('last_tracked') or 'Never'}")
        with a3:
            st.write(f"Updates(24h): {count_updates_last_24h(r)} | Total updates: {r.get('stats',{}).get('updates_total',0)}")

        # history graph
        if r.get("history"):
            fig = plot_price_history(r["history"])
            st.pyplot(fig)
        else:
            st.info("Aucun historique encore pour ce vol.")

        # edit expander
        with st.expander("✏️ Éditer ce suivi"):
            with st.form(key=f"form_edit_{r['id']}"):
                origin_e = st.text_input("Origine (IATA)", value=r.get("origin"))
                destination_e = st.text_input("Destination (IATA)", value=r.get("destination"))
                # safe parse departure: if not ISO, fallback to today
                try:
                    departure_default = datetime.fromisoformat(r.get("departure")).date()
                except Exception:
                    departure_default = date.today()
                departure_e = st.date_input("Date départ", value=departure_default)
                dep_flex_e = st.number_input(
                    "Plage départ ± jours", min_value=0, max_value=30, value=int(r.get("departure_flex_days", 0))
                )
                return_airport_e = st.text_input("Aéroport retour (laisir vide = même)", value=r.get("return_airport") or "")
                stay_min_e = st.number_input("Séjour min (jours)", min_value=1, max_value=365, value=int(r.get("stay_min", 1)))
                stay_max_e = st.number_input("Séjour max (jours)", min_value=1, max_value=365, value=int(r.get("stay_max", 1)))
                return_flex_e = st.number_input("Plage retour ± jours", min_value=0, max_value=30, value=int(r.get("return_flex_days", 0)))

                target_e = st.number_input(
                    "Seuil alerte (€)", min_value=1.0, value=float(r.get("target_price", 450.0)), step=1.0
                )
                trackpd_e = st.number_input("Trackings/jour", min_value=1, max_value=24, value=int(r.get("tracking_per_day", 1)))
                # notif checkbox in edit form (explicit on/off)
                notif_e = st.checkbox("Activer notifications", value=bool(r.get("notifications", False)))
                min_bags_e = st.number_input("Min bagages", min_value=0, max_value=5, value=int(r.get("min_bags", 0)))
                direct_only_e = st.checkbox("Vol direct uniquement", value=bool(r.get("direct_only", False)))
                max_stops_e = st.selectbox(
                    "Max escales", ["any", 0, 1, 2],
                    index=["any", 0, 1, 2].index(r.get("max_stops") if r.get("max_stops") in ["any", 0, 1, 2] else "any")
                )
                avoid_e = st.text_input("Compagnies à éviter (IATA, séparées par ,)", value=",".join(r.get("avoid_airlines", [])))
                preferred_e = st.text_input("Compagnies préférées (IATA, séparées par ,)", value=",".join(r.get("preferred_airlines", [])))
                email_e = st.text_input("Email pour ce suivi (vide = global)", value=r.get("email", ""))

                submit = st.form_submit_button("Enregistrer modifications")

            if submit:
                r["origin"] = origin_e.upper()
                r["destination"] = destination_e.upper()
                r["departure"] = str(departure_e)
                r["departure_flex_days"] = int(dep_flex_e)
                r["return_airport"] = return_airport_e.upper() if return_airport_e else None
                r["stay_min"] = int(stay_min_e)
                r["stay_max"] = int(stay_max_e)
                r["return"] = str((departure_e + timedelta(days=stay_min_e)))
                r["return_flex_days"] = int(return_flex_e)
                r["target_price"] = float(target_e)
                r["tracking_per_day"] = int(trackpd_e)
                r["notifications"] = bool(notif_e)
                r["min_bags"] = int(min_bags_e)
                r["direct_only"] = bool(direct_only_e)
                r["max_stops"] = max_stops_e
                r["avoid_airlines"] = [a.strip().upper() for a in avoid_e.split(",") if a.strip()]
                r["preferred_airlines"] = [a.strip().upper() for a in preferred_e.split(",") if a.strip()]
                r["email"] = email_e.strip()
                save_routes(routes)
                append_log(f"{datetime.now().isoformat()} - Edited route {r['id']}")
                st.success("Modifications enregistrées")
                st.rerun()

        st.markdown("---")

# ---------------- Bottom: Search & suggestions (kept simple) ----------------
st.header("🔎 Suggestions & Comparaison (simu)")
with st.expander("Ouvrir l'outil de comparaison"):
    origins_input = st.text_input("Origines (IATA, séparées par ,)", value="PAR,CDG,ORY")
    destinations_input = st.text_input("Destinations (IATA, séparées par ,)", value="NRT,HND,KIX")
    start_date = st.date_input("Date départ approximative", date.today() + timedelta(days=90))
    search_window_days = st.number_input("Plage recherche (jours) ±", min_value=0, max_value=30, value=7)
    stay_days = st.number_input("Durée séjour (jours)", min_value=1, max_value=60, value=7)
    samples_per_option = st.number_input("Échantillons par combo (pour simu)", min_value=3, max_value=30, value=8)

    if st.button("Lancer la recherche (simu)"):
        origins = [o.strip().upper() for o in origins_input.split(",") if o.strip()]
        dests = [d.strip().upper() for d in destinations_input.split(",") if d.strip()]
        results = []
        for origin in origins:
            for dest in dests:
                for delta in range(-search_window_days, search_window_days + 1):
                    dep = start_date + timedelta(days=delta)
                    for s in range(samples_per_option):
                        price = random.randint(120, 1200)
                        results.append({
                            "origin": origin,
                            "destination": dest,
                            "departure": dep.isoformat(),
                            "stay_days": int(stay_days),
                            "price": price
                        })
        df_res = pd.DataFrame(results)
        st.session_state["last_search"] = df_res
        st.success(f"Recherche simulée : {len(df_res)} résultats générés.")

    if "last_search" in st.session_state:
        df_res = st.session_state["last_search"]
        bests = df_res.loc[df_res.groupby(["origin", "destination"])["price"].idxmin()]
        st.subheader("Meilleurs résultats par origine-destination")
        st.dataframe(bests.sort_values("price").reset_index(drop=True), use_container_width=True)

        cheapest = df_res.sort_values("price").head(10).reset_index(drop=True)
        st.markdown("**Suggestions dates les moins chères (top 10)**")
        st.table(cheapest[["origin", "destination", "departure", "stay_days", "price"]].head(10))

        with st.form("add_from_search"):
            sel_idx = st.number_input(
                "Index à ajouter comme suivi", min_value=0, max_value=max(0, len(df_res) - 1), value=0
            )
            add_submit = st.form_submit_button("Ajouter le résultat comme suivi")
            if add_submit:
                row = df_res.iloc[int(sel_idx)]
                new = {
                    "id": str(uuid.uuid4()),
                    "origin": row["origin"],
                    "destination": row["destination"],
                    "departure": row["departure"],
                    "departure_flex_days": 0,
                    "return": (datetime.fromisoformat(row["departure"]) + timedelta(days=row["stay_days"])).date().isoformat(),
                    "return_airport": None,
                    "stay_min": int(row["stay_days"]),
                    "stay_max": int(row["stay_days"]),
                    "return_flex_days": 0,
                    "target_price": float(row["price"]) * 0.9,
                    "tracking_per_day": 2,
                    "notifications": False,
                    "min_bags": 0,
                    "direct_only": False,
                    "max_stops": "any",
                    "avoid_airlines": [],
                    "preferred_airlines": [],
                    "email": "",
                    "history": [{"date": datetime.now().isoformat(), "price": row["price"]}],
                    "last_tracked": datetime.now().isoformat(),
                    "stats": {}
                }
                routes.append(new)
                save_routes(routes)
                append_log(f"{datetime.now().isoformat()} - Added from search {new['id']}")
                st.success("Suivi créé depuis la recherche.")
