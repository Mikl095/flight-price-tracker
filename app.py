import streamlit as st
from datetime import date, datetime, timedelta
import random
import uuid
import os
import pandas as pd

from utils.storage import ensure_data_file, load_routes, save_routes, load_email_config, save_email_config, append_log, count_updates_last_24h, ensure_route_fields
from utils.plotting import plot_price_history
from exporters import export_csv, export_pdf, export_xlsx
from email_utils import send_email

# init
ensure_data_file()
routes = load_routes()
email_cfg = load_email_config()

st.set_page_config(page_title="Flight Price Tracker", layout="wide")
st.title("✈️ Flight Price Tracker — Dashboard & Tools (Simu)")

# ---------------- Top bar: quick actions ----------------
col1, col2, col3 = st.columns([1,2,1])
with col1:
    if st.button("Mettre à jour tous (simu)"):
        for r in routes:
            price = random.randint(150, 900)
            r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
            r["last_tracked"] = datetime.now().isoformat()
        save_routes(routes)
        st.success("Tous mis à jour (simu).")
        st.experimental_rerun()

with col2:
    st.markdown("**Recherche & comparateur (simulation)** — comparer plusieurs origines/destinations et trouver les dates moins chères.")

with col3:
    st.download_button("Exporter XLSX", data=open(export_xlsx(routes, path="export.xlsx"), "rb"), file_name="export.xlsx")

# ---------------- Sidebar : Search config ----------------
st.sidebar.header("🔎 Search / Compare (simu)")

# multi-origin support (comma separated)
origins_input = st.sidebar.text_input("Origines (IATA, séparées par ,)", value="PAR,CDG,ORY")
destinations_input = st.sidebar.text_input("Destinations (IATA, séparées par ,)", value="NRT,HND,KIX")
start_date = st.sidebar.date_input("Date départ approximative", date.today()+timedelta(days=90))
search_window_days = st.sidebar.number_input("Plage recherche (jours) ±", min_value=0, max_value=30, value=7)
stay_days = st.sidebar.number_input("Durée séjour (jours)", min_value=1, max_value=60, value=7)
samples_per_option = st.sidebar.number_input("Échantillons par combo (pour simu)", min_value=3, max_value=30, value=10)

if st.sidebar.button("Lancer la recherche (simu)"):
    origins = [o.strip().upper() for o in origins_input.split(",") if o.strip()]
    dests = [d.strip().upper() for d in destinations_input.split(",") if d.strip()]

    results = []
    # brute-force simulate: for each origin x dest, sample departure dates in window and random prices
    for origin in origins:
        for dest in dests:
            for delta in range(-search_window_days, search_window_days+1):
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

# show last search / analysis
if "last_search" in st.session_state:
    df_res = st.session_state["last_search"]
    st.subheader("🔎 Résultats recherche (simu)")
    # show best per origin/dest: minimal price and corresponding date
    bests = df_res.loc[df_res.groupby(["origin","destination"])["price"].idxmin()]
    st.dataframe(bests.sort_values("price").reset_index(drop=True), use_container_width=True)

    # date suggestion: top 3 cheapest overall
    cheapest = df_res.sort_values("price").head(10).reset_index(drop=True)
    st.markdown("**Suggestions dates les moins chères (top 10)**")
    st.table(cheapest[["origin","destination","departure","stay_days","price"]].head(10))

    # allow user to add a chosen result to tracking
    with st.form("add_from_search"):
        sel_idx = st.number_input("Sélectionner la ligne (index) à ajouter comme suivi", min_value=0, max_value=max(0, len(df_res)-1), value=0)
        add_note = st.text_input("Note (optionnel)")
        add_submit = st.form_submit_button("Ajouter ce résultat comme suivi")
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
                "target_price": float(row["price"]) * 0.9,  # heuristic default target
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
            }
            routes.append(new)
            save_routes(routes)
            append_log(f"{datetime.now().isoformat()} - Added from search {new['id']}")
            st.success("Suivi créé depuis la recherche.")

# ---------------- Main Dashboard (optimized UI) ----------------
st.header("📊 Dashboard")
if not routes:
    st.info("Aucun suivi — ajoute un vol dans la barre latérale ou via Search.")
else:
    # summary cards
    total = len(routes)
    total_with_notif = sum(1 for r in routes if r.get("notifications"))
    updates_24h = sum(count_updates_last_24h(r) for r in routes)
    colA, colB, colC = st.columns(3)
    colA.metric("Suivis total", total)
    colB.metric("Suivis avec notifications", total_with_notif)
    colC.metric("Mises à jour (24h)", updates_24h)

    # per-route panels
    for idx, r in enumerate(routes):
        ensure_route_fields(r)
        with st.container():
            st.subheader(f"{r['origin']} → {r['destination']}  (id: {r['id'][:8]})")
            row1, row2, row3 = st.columns([1,2,1])
            with row1:
                st.write(f"Dates: {r.get('departure')} → {r.get('return')}")
                st.write(f"Seuil: {r.get('target_price')}€")
                st.write(f"Notif: {'ON' if r.get('notifications') else 'OFF'}")
            with row2:
                if st.button("Update now", key=f"u_{idx}"):
                    price = random.randint(100, 1000)
                    r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
                    r["last_tracked"] = datetime.now().isoformat()
                    save_routes(routes)
                    append_log(f"{datetime.now().isoformat()} - Manual update {r['id']} price={price}")
                    st.experimental_rerun()
                if st.button("Test mail", key=f"tm_{idx}"):
                    rcpt = r.get("email") or email_cfg.get("email", "")
                    if not rcpt:
                        st.warning("Aucune adresse email configurée.")
                    else:
                        ok, status = send_email(rcpt, f"Test {r['origin']}->{r['destination']}", "<p>Test</p>")
                        st.info("Email envoyé" if ok else f"Erreur (status {status})")

            with row3:
                # stats small
                st.write(f"Updates (24h): {count_updates_last_24h(r)}")
                st.write(f"Total updates: {r.get('stats', {}).get('updates_total',0)}")
                st.write(f"Notifications sent: {r.get('stats', {}).get('notifications_sent',0)}")

            # show graph and edit expander
            if r.get("history"):
                fig = plot_price_history(r["history"])
                st.pyplot(fig)

            with st.expander("✏️ Edit / Advanced"):
                with st.form(key=f"form_{r['id']}"):
                    origin_e = st.text_input("Origine", value=r.get("origin"))
                    dest_e = st.text_input("Destination", value=r.get("destination"))
                    departure_e = st.date_input("Date départ", value=datetime.fromisoformat(r.get("departure")).date() if r.get("departure") else date.today())
                    depflex_e = st.number_input("Flex départ ± jours", min_value=0, max_value=30, value=int(r.get("departure_flex_days",0)))
                    stay_min_e = st.number_input("Séjour min", min_value=1, max_value=365, value=int(r.get("stay_min",1)))
                    stay_max_e = st.number_input("Séjour max", min_value=1, max_value=365, value=int(r.get("stay_max",1)))
                    target_e = st.number_input("Seuil (€)", min_value=1.0, value=float(r.get("target_price",100.0)))
                    trackpd_e = st.number_input("Trackings/jour", min_value=1, max_value=24, value=int(r.get("tracking_per_day",1)))
                    notif_e = st.checkbox("Activer notifications", value=bool(r.get("notifications", False)))
                    email_e = st.text_input("Email pour ce suivi", value=r.get("email",""))
                    submit = st.form_submit_button("Enregistrer")

                if submit:
                    r["origin"] = origin_e.upper()
                    r["destination"] = dest_e.upper()
                    r["departure"] = str(departure_e)
                    r["departure_flex_days"] = int(depflex_e)
                    r["stay_min"] = int(stay_min_e)
                    r["stay_max"] = int(stay_max_e)
                    r["target_price"] = float(target_e)
                    r["tracking_per_day"] = int(trackpd_e)
                    r["notifications"] = bool(notif_e)
                    r["email"] = email_e.strip()
                    save_routes(routes)
                    append_log(f"{datetime.now().isoformat()} - Edited {r['id']}")
                    st.success("Modifications enregistrées.")
                    st.experimental_rerun()
