import streamlit as st
from datetime import date, datetime, timedelta
import random
import uuid
import os

from utils.storage import ensure_data_file, load_routes, save_routes, load_email_config, save_email_config, append_log, count_updates_last_24h
from utils.plotting import plot_price_history
from exporters import export_csv, export_pdf
from email_utils import send_email

# init
ensure_data_file()
routes = load_routes()
email_cfg = load_email_config()

st.set_page_config(page_title="Flight Price Tracker", layout="wide")
st.title("✈️ Flight Price Tracker — Dashboard & Notifications (Simu)")

# ---------------- Sidebar: global settings ----------------
st.sidebar.header("⚙️ Paramètres globaux")

global_email = st.sidebar.text_input("Email global (pour notifications)", value=email_cfg.get("email",""))
global_enabled = st.sidebar.checkbox("Activer notifications globales", value=email_cfg.get("enabled", False))

if st.sidebar.button("Enregistrer paramètres"):
    save_email_config({"email": global_email, "enabled": bool(global_enabled)})
    st.sidebar.success("Paramètres enregistrés")
    append_log(f"{datetime.now().isoformat()} - Global email saved: {global_email}")

st.sidebar.markdown("---")
st.sidebar.write("SendGrid: ajoute ta clé `SENDGRID_KEY` dans les Secrets (GitHub + Streamlit).")

# ---------------- Sidebar: add route ----------------
st.sidebar.header("➕ Ajouter un suivi")
origin = st.sidebar.text_input("Origine (IATA)", "PAR")
destination = st.sidebar.text_input("Destination (IATA)", "TYO")
departure_date = st.sidebar.date_input("Date départ (approx.)", date.today() + timedelta(days=90))

departure_flex_days = st.sidebar.number_input("Plage départ ± jours", min_value=0, max_value=30, value=1)
return_airport = st.sidebar.text_input("Aéroport retour (IATA) - vide = même", "")
stay_min = st.sidebar.number_input("Séjour min (jours)", min_value=1, max_value=365, value=6)
stay_max = st.sidebar.number_input("Séjour max (jours)", min_value=1, max_value=365, value=10)
return_flex_days = st.sidebar.number_input("Plage retour ± jours", min_value=0, max_value=30, value=1)

# CORRECTION float-safe
target_price = st.sidebar.number_input("Seuil alerte (€)", min_value=1.0, value=450.0, step=1.0)

tracking_per_day = st.sidebar.number_input("Trackings par jour", min_value=1, max_value=24, value=2)
notifications_on = st.sidebar.checkbox("Activer notifications pour ce vol", value=True)
min_bags = st.sidebar.number_input("Min bagages (préférence)", min_value=0, max_value=5, value=0)
direct_only = st.sidebar.checkbox("Vol direct uniquement (préférence)", value=False)
max_stops = st.sidebar.selectbox("Max escales (préférence)", ["any", 0, 1, 2])
avoid_airlines = st.sidebar.text_input("Compagnies à éviter (IATA, séparées par ,)", value="")
preferred_airlines = st.sidebar.text_input("Compagnies préférées (IATA, séparées par ,)", value="")
route_email = st.sidebar.text_input("Email pour ce suivi (laisser vide = email global)","")

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
        "last_tracked": None
    }
    routes.append(new)
    save_routes(routes)
    append_log(f"{datetime.now().isoformat()} - Added route {new['id']}")
    st.success("Vol ajouté ✔")
    st.rerun()

# ---------------- Main Dashboard ----------------
st.header("📊 Dashboard")
if not routes:
    st.info("Aucun suivi — ajoute un vol dans la barre latérale.")
else:
    import pandas as pd
    df = pd.DataFrame([
        {
            "id": r.get("id")[:8],
            "origin": r.get("origin"),
            "destination": r.get("destination"),
            "departure": r.get("departure"),
            "stay": f"{r.get('stay_min')}–{r.get('stay_max')}",
            "target": r.get("target_price"),
            "last_price": (r.get("history")[-1]["price"] if r.get("history") else None),
            "notif": "ON" if r.get("notifications") else "OFF",
            "email": r.get("email") or global_email
        } for r in routes
    ])
    st.dataframe(df, width='stretch')

    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        if st.button("Exporter CSV"):
            path = export_csv(routes)
            st.success(f"CSV exporté: {path}")
            st.download_button("Télécharger CSV", path, file_name=path)
    with c2:
        if st.button("Exporter PDF"):
            path = export_pdf(routes)
            st.success(f"PDF exporté: {path}")
            st.download_button("Télécharger PDF", path, file_name=path)
    with c3:
        if st.button("Mettre à jour tous les prix (simu)"):
            for r in routes:
                price = random.randint(150, 900)
                r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
                r["last_tracked"] = datetime.now().isoformat()
                recipient = r.get("email") or global_email
                if r.get("notifications") and recipient and (r.get("email") or global_enabled):
                    target = r.get("target_price")
                    if target is not None and price <= target:
                        ok, status = send_email(recipient,
                                               f"[ALERTE] {r['origin']}→{r['destination']}: {price}€",
                                               f"<p>Prix: {price}€ (seuil {target}€)</p>")
                        append_log(f"{datetime.now().isoformat()} - immediate notify {recipient} ok={ok} status={status}")
            save_routes(routes)
            st.success("Mise à jour simulée effectuée.")
            st.rerun()

    st.markdown("---")

    for idx, r in enumerate(routes):
        st.subheader(f"{r['origin']} → {r['destination']}  (id: {r['id'][:8]})")
        cols = st.columns([1,1,1,1])

        with cols[0]:
            if st.button("Mettre à jour", key=f"update_{idx}"):
                price = random.randint(150,900)
                r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
                r["last_tracked"] = datetime.now().isoformat()
                save_routes(routes)
                append_log(f"{datetime.now().isoformat()} - Manual update {r['id']} price={price}")
                st.rerun()

        with cols[1]:
            if st.button("Toggle notif", key=f"toggle_{idx}"):
                r["notifications"] = not r.get("notifications", False)
                save_routes(routes)
                append_log(f"{datetime.now().isoformat()} - Toggle notif {r['id']} -> {r['notifications']}")
                st.rerun()

        with cols[2]:
            if st.button("Supprimer", key=f"del_{idx}"):
                append_log(f"{datetime.now().isoformat()} - Delete route {r['id']}")
                routes.pop(idx)
                save_routes(routes)
                st.rerun()

        with cols[3]:
            if st.button("Envoyer test mail", key=f"testmail_{idx}"):
                recipient = r.get("email") or global_email
                if not recipient:
                    st.warning("Aucune adresse email configurée (route/global).")
                else:
                    ok, status = send_email(recipient, f"Test alerte {r['origin']}→{r['destination']}", "<p>Test d'alerte</p>")
                    st.info("Email envoyé" if ok else "Erreur d'envoi (voir logs)")
                    append_log(f"{datetime.now().isoformat()} - Test mail {r['id']} -> {recipient} ok={ok} status={status}")

        # Edit form
        with st.expander("✏️ Éditer ce suivi"):
            with st.form(key=f"form_edit_{r['id']}"):
                origin_e = st.text_input("Origine (IATA)", value=r.get("origin"))
                destination_e = st.text_input("Destination (IATA)", value=r.get("destination"))
                departure_e = st.date_input("Date départ", value=datetime.fromisoformat(r.get("departure")).date() if r.get("departure") else date.today())
                dep_flex_e = st.number_input("Plage départ ± jours", min_value=0, max_value=30, value=int(r.get("departure_flex_days",0)))
                return_airport_e = st.text_input("Aéroport retour (laisser vide = même)", value=r.get("return_airport") or "")
                stay_min_e = st.number_input("Séjour min (jours)", min_value=1, max_value=365, value=int(r.get("stay_min",1)))
                stay_max_e = st.number_input("Séjour max (jours)", min_value=1, max_value=365, value=int(r.get("stay_max",1)))

                return_flex_e = st.number_input("Plage retour ± jours", min_value=0, max_value=30, value=int(r.get("return_flex_days",0)))

                # CORRECTION float-safe
                target_e = st.number_input("Seuil alerte (€)", min_value=1.0,
                                           value=float(r.get("target_price", 450.0)),
                                           step=1.0)

                trackpd_e = st.number_input("Trackings/jour", min_value=1, max_value=24, value=int(r.get("tracking_per_day",1)))
                notif_e = st.checkbox("Activer notifications", value=bool(r.get("notifications", False)))
                min_bags_e = st.number_input("Min bagages", min_value=0, max_value=5, value=int(r.get("min_bags",0)))
                direct_only_e = st.checkbox("Vol direct uniquement", value=bool(r.get("direct_only", False)))
                max_stops_e = st.selectbox("Max escales", ["any", 0, 1, 2], index=["any",0,1,2].index(r.get("max_stops") if r.get("max_stops") in ["any",0,1,2] else "any"))
                avoid_e = st.text_input("Compagnies à éviter (IATA, séparées par ,)", value=",".join(r.get("avoid_airlines", [])))
                preferred_e = st.text_input("Compagnies préférées (IATA, séparées par ,)", value=",".join(r.get("preferred_airlines", [])))
                email_e = st.text_input("Email pour ce suivi (vide = global)", value=r.get("email",""))

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

        # show last price
        if r.get("history"):
            last = r["history"][-1]["price"]
            st.write(f"Prix actuel: **{last} €** (dernière maj: {r.get('last_tracked')})")
            fig = plot_price_history(r["history"])
            st.pyplot(fig)
        else:
            st.info("Aucun historique encore pour ce vol.")
