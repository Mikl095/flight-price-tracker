import streamlit as st
from datetime import datetime, date, timedelta
import random
import uuid
import pandas as pd
from utils.storage import (
    ensure_data_file, load_routes, save_routes,
    load_email_config, save_email_config,
    append_log, count_updates_last_24h, ensure_route_fields, sanitize_dict
)
from utils.plotting import plot_price_history
from exporters import export_csv, export_pdf, export_xlsx
from email_utils import send_email

# -----------------------------
# TOP BAR
# -----------------------------
def render_top_bar(routes, email_cfg):
    st.set_page_config(page_title="Flight Price Tracker", layout="wide")
    st.title("✈️ Flight Price Tracker — Multi-onglets (Simu)")

    global_notif_enabled = bool(email_cfg.get("enabled", False))
    notif_color = "🟢" if global_notif_enabled else "🔴"
    st.markdown(
        f"<div style='font-size:18px; margin-bottom:15px;'>{notif_color} "
        f"<b>Notifications globales : {'ACTIVÉES' if global_notif_enabled else 'DÉSACTIVÉES'}</b></div>",
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1,2,1])

    with col1:
        if st.button("Mettre à jour tous (simu)"):
            for r in routes:
                price = random.randint(120, 1000)
                r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
                r["last_tracked"] = datetime.now().isoformat()
            save_routes(routes)
            append_log(f"{datetime.now().isoformat()} - Bulk update (simu)")
            st.success("Mise à jour globale simulée.")
            st.rerun()

    with col3:
        if st.button("Exporter CSV"):
            path = export_csv(routes, path="export.csv")
            st.download_button("Télécharger CSV", data=open(path,"rb").read(), file_name="export.csv")

        if st.button("Exporter PDF"):
            path = export_pdf(routes, path="export.pdf")
            st.download_button("Télécharger PDF", data=open(path,"rb").read(), file_name="export.pdf")

        if st.button("Exporter XLSX"):
            path = export_xlsx(routes, path="export.xlsx")
            st.download_button("Télécharger XLSX", data=open(path,"rb").read(), file_name="export.xlsx")


# -----------------------------
# DASHBOARD
# -----------------------------
def render_dashboard(routes, email_cfg, global_notif_enabled):
    st.header("📊 Dashboard — Récapitulatif des suivis")

    if not routes:
        st.info("Aucun suivi pour l'instant. Ajoute un suivi dans l'onglet « Ajouter un suivi ».")
        return

    # Summary metrics
    total = len(routes)
    notif_on = sum(1 for r in routes if r.get("notifications"))
    updates_24h = sum(count_updates_last_24h(r) for r in routes)
    c1, c2, c3 = st.columns(3)
    c1.metric("Suivis", total)
    c2.metric("Notifications ON", notif_on)
    c3.metric("Mises à jour (24h)", updates_24h)
    st.markdown("---")

    # Table recap
    df_rows = []
    for r in routes:
        last_price = r.get("history")[-1]["price"] if r.get("history") else None
        min_price = min((h["price"] for h in r.get("history", [])), default=None)
        df_rows.append({
            "id": r.get("id")[:8],
            "origin": r.get("origin"),
            "destination": r.get("destination"),
            "departure": r.get("departure"),
            "return": r.get("return"),
            "last_price": last_price,
            "min_price": min_price,
            "target": r.get("target_price"),
            "notif": "ON" if r.get("notifications") else "OFF",
            "email": r.get("email") or email_cfg.get("email", "")
        })
    df = pd.DataFrame(df_rows)
    st.dataframe(df, use_container_width=True)
    st.markdown("---")

    for idx, r in enumerate(routes):
        ensure_route_fields(r)
        st.subheader(f"{r['origin']} → {r['destination']}  (id: {r['id'][:8]})")
        cols = st.columns([2,1,1,1])

        # LEFT COL
        with cols[0]:
            st.write(
                f"**Dates :** {r.get('departure')} (±{r.get('departure_flex_days',0)} j) → "
                f"{r.get('return')} (±{r.get('return_flex_days',0)} j)\n\n"
                f"**Aéroport retour :** {r.get('return_airport') or '—'}\n\n"
                f"**Séjour :** {r.get('stay_min')}–{r.get('stay_max')} j\n\n"
                f"**Seuil :** {r.get('target_price')}€\n\n"
                f"**Email :** {r.get('email') or email_cfg.get('email','—')}"
            )

        # UPDATE BUTTON
        with cols[1]:
            if st.button("Update", key=f"dash_update_{idx}"):
                price = random.randint(120, 1000)
                r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
                r["last_tracked"] = datetime.now().isoformat()
                save_routes(routes)
                append_log(f"{datetime.now().isoformat()} - Manual update {r['id']} price={price}")
                st.rerun()

        # NOTIF BUTTON
        with cols[2]:
            if r.get("notifications"):
                if st.button("Désactiver notif", key=f"dash_notif_off_{idx}"):
                    r["notifications"] = False
                    save_routes(routes)
                    append_log(f"{datetime.now().isoformat()} - Notifications OFF {r['id']}")
                    st.rerun()
            else:
                if st.button("Activer notif", key=f"dash_notif_on_{idx}"):
                    r["notifications"] = True
                    save_routes(routes)
                    append_log(f"{datetime.now().isoformat()} - Notifications ON {r['id']}")
                    st.rerun()

        # DELETE BUTTON
        with cols[3]:
            if st.button("Supprimer", key=f"dash_del_{idx}"):
                append_log(f"{datetime.now().isoformat()} - Delete route {r['id']}")
                routes.pop(idx)
                save_routes(routes)
                st.rerun()

        # SMALL ACTIONS
        a1, a2, a3 = st.columns([1,1,1])
        with a1:
            if st.button("Test mail", key=f"dash_testmail_{idx}"):
                if not global_notif_enabled:
                    st.warning("Notifications globales désactivées.")
                else:
                    rcpt = r.get("email") or email_cfg.get("email", "")
                    if not rcpt:
                        st.warning("Aucune adresse email configurée.")
                    else:
                        ok, status = send_email(rcpt, f"Test alerte {r['origin']}→{r['destination']}", "<p>Test</p>")
                        st.info("Email envoyé" if ok else f"Erreur (status {status})")
        with a2:
            st.write(f"Last tracked: {r.get('last_tracked') or 'Never'}")
        with a3:
            st.write(f"Updates(24h): {count_updates_last_24h(r)}")

        # PRICE HISTORY PLOT
        if r.get("history"):
            fig = plot_price_history(r["history"])
            st.pyplot(fig)
        else:
            st.info("Aucun historique encore pour ce vol.")

        # EDIT ROUTE
        render_edit_route(r, routes, email_cfg)


# -----------------------------
# EDIT ROUTE (comme création)
# -----------------------------
def render_edit_route(r, routes, email_cfg):
    with st.expander("✏️ Éditer ce suivi"):
        with st.form(key=f"dash_form_{r['id']}"):
            # BASE
            origin_e = st.text_input("Origine (IATA)", value=r.get("origin", ""))
            dest_e = st.text_input("Destination (IATA)", value=r.get("destination", ""))

            # DEPART
            dep_dt_default = r.get("departure")
            dep_date_default = date.today()
            try:
                dep_dt_default = datetime.fromisoformat(dep_dt_default)
                dep_date_default = dep_dt_default.date()
            except Exception:
                pass
            departure_e = st.date_input("Date départ", value=dep_date_default)
            depflex = st.number_input("Flex départ ± jours", min_value=0, max_value=30, value=int(r.get("departure_flex_days",0)))

            # RETOUR
            ret_dt_default = r.get("return")
            return_date_default = None
            if ret_dt_default:
                try:
                    return_date_default = datetime.fromisoformat(ret_dt_default).date()
                except Exception:
                    pass
            return_e = st.date_input("Date retour (optionnelle)", value=return_date_default)
            return_flex_e = st.number_input("Flex retour ± jours", min_value=0, max_value=30, value=int(r.get("return_flex_days",0)))
            priority_stay_e = st.checkbox("Priorité durée de séjour si pas de date de retour", value=r.get("priority_stay", False))

            # SÉJOUR
            stay_min_e = st.number_input("Séjour min (jours)", min_value=1, max_value=365, value=int(r.get("stay_min",1)))
            stay_max_e = st.number_input("Séjour max (jours)", min_value=1, max_value=365, value=int(r.get("stay_max",1)))

            # PRIX / TRACKING
            target_e = st.number_input("Seuil alerte (€)", min_value=1.0, value=float(r.get("target_price",100.0)))
            tracking_pd_e = st.number_input("Trackings par jour", min_value=1, max_value=24, value=int(r.get("tracking_per_day",1)))
            notif_e = st.checkbox("Activer notifications pour ce vol", value=r.get("notifications", False))
            email_e = st.text_input("Email pour ce suivi (vide = global)", value=r.get("email",""))

            # PREFERENCES
            min_bags_e = st.number_input("Min bagages", min_value=0, max_value=5, value=int(r.get("min_bags",0)))
            direct_only_e = st.checkbox("Vol direct uniquement", value=r.get("direct_only",False))
            max_stops_e = st.selectbox("Max escales", ["any",0,1,2], index=["any",0,1,2].index(r.get("max_stops","any")))
            avoid_e = st.text_input("Compagnies à éviter (IATA, séparées par ,)", value=",".join(r.get("avoid_airlines",[])))
            pref_e = st.text_input("Compagnies préférées (IATA, séparées par ,)", value=",".join(r.get("preferred_airlines",[])))

            submit_edit = st.form_submit_button("Enregistrer les modifications")

        if submit_edit:
            r["origin"] = origin_e.upper().strip()
            r["destination"] = dest_e.upper().strip()
            r["departure"] = departure_e.isoformat()
            r["departure_flex_days"] = int(depflex)
            r["return"] = return_e.isoformat() if return_e else None
            r["return_flex_days"] = int(return_flex_e)
            r["priority_stay"] = bool(priority_stay_e)
            r["stay_min"] = int(stay_min_e)
            r["stay_max"] = int(stay_max_e)
            r["target_price"] = float(target_e)
            r["tracking_per_day"] = int(tracking_pd_e)
            r["notifications"] = bool(notif_e)
            r["email"] = email_e.strip()
            r["min_bags"] = int(min_bags_e)
            r["direct_only"] = bool(direct_only_e)
            r["max_stops"] = max_stops_e
            r["avoid_airlines"] = [a.strip().upper() for a in avoid_e.split(",") if a.strip()]
            r["preferred_airlines"] = [a.strip().upper() for a in pref_e.split(",") if a.strip()]
            save_routes(routes)
            append_log(f"{datetime.now().isoformat()} - Edited route {r['id']}")
            st.success("Modifications enregistrées.")
            st.rerun()


# -----------------------------
# TAB AJOUT
# -----------------------------
def render_add_tab(routes):
    st.header("➕ Ajouter un suivi")
    with st.form("form_add_new"):
        origins = st.text_area("Origines (IATA, séparées par ,)", value="PAR")
        destinations = st.text_area("Destinations (IATA, séparées par ,)", value="TYO")
        departure_date = st.date_input("Date départ (approx.)", date.today() + timedelta(days=90))
        dep_flex = st.number_input("Plage départ ± jours", min_value=0, max_value=30, value=1)
        return_date = st.date_input("Date retour (optionnelle)", value=None)
        return_flex = st.number_input("Plage retour ± jours", min_value=0, max_value=30, value=1)
        return_airport = st.text_input("Aéroport retour (IATA) — vide = même", "")
        priority_stay = st.checkbox("Priorité durée de séjour si pas de date de retour", value=False)
        stay_min = st.number_input("Séjour min (jours)", min_value=1, max_value=365, value=6)
        stay_max = st.number_input("Séjour max (jours)", min_value=1, max_value=365, value=10)
        target_price = st.number_input("Seuil alerte (€)", min_value=1.0, value=450.0)
        tracking_per_day = st.number_input("Trackings par jour", min_value=1, max_value=24, value=2)
        notifications_on = st.checkbox("Activer notifications pour ce suivi", value=True)
        min_bags = st.number_input("Min bagages (préférence)", min_value=0, max_value=5, value=0)
        direct_only = st.checkbox("Vol direct uniquement (préférence)", value=False)
        max_stops = st.selectbox("Max escales (préférence)", ["any",0,1,2])
        avoid_airlines = st.text_input("Compagnies à éviter (IATA, séparées par ,)", value="")
        preferred_airlines = st.text_input("Compagnies préférées (IATA, séparées par ,)", value="")
        route_email = st.text_input("Email pour ce suivi (vide = email global)", value="")
        add_submit = st.form_submit_button("Ajouter ce suivi")

    if add_submit:
        for origin in [o.strip().upper() for o in origins.split(",") if o.strip()]:
            for dest in [d.strip().upper() for d in destinations.split(",") if d.strip()]:
                new = {
                    "id": str(uuid.uuid4()),
                    "origin": origin,
                    "destination": dest,
                    "departure": departure_date.isoformat(),
                    "departure_flex_days": int(dep_flex),
                    "return": return_date.isoformat() if return_date else None,
                    "return_flex_days": int(return_flex),
                    "priority_stay": priority_stay,
                    "return_airport": return_airport.upper().strip() if return_airport else None,
                    "stay_min": int(stay_min),
                    "stay_max": int(stay_max),
                    "target_price": float(target_price),
                    "tracking_per_day": int(tracking_per_day),
                    "notifications": bool(notifications_on),
                    "email": route_email.strip(),
                    "min_bags": int(min_bags),
                    "direct_only": bool(direct_only),
                    "max_stops": max_stops,
                    "avoid_airlines": [a.strip().upper() for a in avoid_airlines.split(",") if a.strip()],
                    "preferred_airlines": [a.strip().upper() for a in preferred_airlines.split(",") if a.strip()],
                    "history": [],
                    "last_tracked": None,
                    "stats": {}
                }
                routes.append(new)
                append_log(f"{datetime.now().isoformat()} - Added route {new['id']}")
        save_routes(routes)
        st.success("Suivi(s) ajouté(s) ✔")
        st.rerun()


# -----------------------------
# SEARCH & SUGGESTIONS
# -----------------------------
def render_search_tab(routes):
    st.header("🔎 Recherche & Suggestions (Simulation)")
    st.write("Simulation de prix selon origines, destinations, date et durée de séjour.")
    with st.expander("Paramètres de recherche"):
        origins_input = st.text_input("Origines (IATA, séparées par ,)", value="PAR,CDG")
        destinations_input = st.text_input("Destinations (IATA, séparées par ,)", value="NYC,JFK,EWR")
        start_date = st.date_input("Date départ approximative", date.today() + timedelta(days=90))
        search_window_days = st.number_input("Fenêtre recherche (± jours)", min_value=0, max_value=30, value=7)
        stay_days = st.number_input("Durée de séjour (jours)", min_value=1, max_value=60, value=7)
        return_date_opt = st.date_input("Date retour (optionnelle)", value=None)
        samples_per_option = st.number_input("Échantillons par combinaison", min_value=3, max_value=30, value=5)

    # Création dataframe simulé
    df_rows = []
    for o in [x.strip().upper() for x in origins_input.split(",") if x.strip()]:
        for d in [x.strip().upper() for x in destinations_input.split(",") if x.strip()]:
            for i in range(samples_per_option):
                df_rows.append({
                    "origin": o,
                    "destination": d,
                    "departure": (start_date + timedelta(days=random.randint(-search_window_days, search_window_days))).isoformat(),
                    "return": (start_date + timedelta(days=stay_days + random.randint(-2,2))).isoformat() if return_date_opt else None,
                    "price": random.randint(120, 1000),
                    "id": str(uuid.uuid4())
                })
    df_res = pd.DataFrame(df_rows)

    # Multi-select via ID
    with st.form("add_from_search"):
        selected_ids = st.multiselect(
            "Sélectionner les résultats à ajouter",
            options=df_res["id"].tolist(),
            format_func=lambda i: f"{df_res.loc[df_res['id']==i, 'origin'].values[0]} → "
                                 f"{df_res.loc[df_res['id']==i, 'destination'].values[0]} "
                                 f"({df_res.loc[df_res['id']==i, 'departure'].values[0]})"
        )
        add_submit = st.form_submit_button("Ajouter sélection")

    if add_submit and selected_ids:
        created = 0
        for sid in selected_ids:
            row = df_res.loc[df_res["id"]==sid].iloc[0]
            new = {
                "id": str(uuid.uuid4()),
                "origin": row["origin"],
                "destination": row["destination"],
                "departure": row["departure"],
                "return": row["return"],
                "stay_min": stay_days,
                "stay_max": stay_days+3,
                "target_price": 450.0,
                "tracking_per_day": 2,
                "notifications": True,
                "email": "",
                "min_bags": 0,
                "direct_only": False,
                "max_stops": "any",
                "avoid_airlines": [],
                "preferred_airlines": [],
                "history": [],
                "last_tracked": None,
                "stats": {}
            }
            routes.append(new)
            created += 1
        save_routes(routes)
        st.success(f"{created} suivi(s) ajouté(s) depuis la simulation.")


# -----------------------------
# CONFIGURATION
# -----------------------------
def render_config_tab():
    st.header("⚙️ Configuration globale")
    cfg = load_email_config()
    with st.form("cfg_form"):
        enabled = st.checkbox("Activer notifications globales", value=cfg.get("enabled", False))
        email = st.text_input("Email global", value=cfg.get("email", ""))
        api_user = st.text_input("SendGrid API user", value=cfg.get("api_user",""))
        api_pass = st.text_input("SendGrid API key", value=cfg.get("api_pass",""))
        submit = st.form_submit_button("Enregistrer")
    if submit:
        cfg["enabled"] = bool(enabled)
        cfg["email"] = email.strip()
        cfg["api_user"] = api_user.strip()
        cfg["api_pass"] = api_pass.strip()
        save_email_config(cfg)
        st.success("Configuration enregistrée ✔")
