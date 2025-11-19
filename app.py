# app.py — PARTIE 1 (colle en premier)
import streamlit as st
from datetime import datetime, date, timedelta
import uuid
import random
import pandas as pd
from utils.storage import (
    ensure_data_file, load_routes, save_routes,
    load_email_config, save_email_config,
    append_log, count_updates_last_24h, ensure_route_fields, sanitize_dict
)
from exporters import export_csv, export_pdf, export_xlsx
from utils.plotting import plot_price_history
from utils.email_utils import send_email
import io
import os

# -----------------------------
# INIT
# -----------------------------
ensure_data_file()
routes = load_routes()
email_cfg = load_email_config()
global_notif_enabled = bool(email_cfg.get("enabled", False))

st.set_page_config(page_title="Flight Price Tracker", layout="wide")
st.title("✈️ Flight Price Tracker — Multi-onglets")

# -----------------------------
# TOP BAR — actions globales
# -----------------------------
col_top_left, col_top_mid, col_top_right = st.columns([1,2,1])

with col_top_left:
    if st.button("Mettre à jour tous (simu)"):
        # simulate a single random price update for each route
        changed = False
        for r in routes:
            try:
                price = random.randint(120, 1000)
                r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
                r["last_tracked"] = datetime.now().isoformat()
                changed = True
            except Exception:
                continue
        if changed:
            # save + attempt git commit & push (if enabled in env)
            save_routes(routes, commit_and_push=True)
            append_log(f"{datetime.now().isoformat()} - Bulk update (simu)")
            st.success("Mise à jour globale simulée ✔")
            st.rerun()

with col_top_right:
    if st.button("Exporter CSV (tout)"):
        try:
            fname, data = export_csv(routes)  # exporters should return (filename, bytes)
            st.download_button("Télécharger export CSV (tout)", data=data, file_name=fname)
        except Exception as e:
            st.error(f"Erreur export CSV global : {e}")

    if st.button("Exporter XLSX (tout)"):
        try:
            fname, data = export_xlsx(routes)
            st.download_button("Télécharger export XLSX (tout)", data=data, file_name=fname)
        except Exception as e:
            st.error(f"Erreur export XLSX global : {e}")

    if st.button("Exporter PDF (tout)"):
        try:
            fname, data = export_pdf(routes)
            st.download_button("Télécharger export PDF (tout)", data=data, file_name=fname)
        except Exception as e:
            st.error(f"Erreur export PDF global : {e}")

# -----------------------------
# SIDEBAR / NAV
# -----------------------------
tab = st.sidebar.radio("Navigation", ["Dashboard","Ajouter suivi","Recherche/Simulation","Configuration","Exports"])

# -----------------------------
# DASHBOARD
# -----------------------------
if tab=="Dashboard":
    st.header("📊 Dashboard — Récapitulatif des suivis")
    if not routes:
        st.info("Aucun suivi pour l'instant. Ajoute un suivi dans l'onglet « Ajouter suivi ».")    
    else:
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
            # app.py — PARTIE 2 (colle après PARTIE 1)
        # Details for each route
        for idx, r in enumerate(routes):
            ensure_route_fields(r)
            st.subheader(f"{r['origin']} → {r['destination']}  (id: {r['id'][:8]})")
            cols = st.columns([2,1,1,1])

            with cols[0]:
                st.write(
                    f"**Dates :** {r.get('departure')} (±{r.get('departure_flex_days',0)} j) → "
                    f"{r.get('return')} (±{r.get('return_flex_days',0)} j)\n\n"
                    f"**Aéroport retour :** {r.get('return_airport') or '—'}\n\n"
                    f"**Classe :** {r.get('cabin_class')}\n\n"
                    f"**Séjour :** {r.get('stay_min')}–{r.get('stay_max')} j\n\n"
                    f"**Seuil :** {r.get('target_price')}€\n\n"
                    f"**Email :** {r.get('email') or email_cfg.get('email','—')}"
                )
            with cols[1]:
                if st.button("Update", key=f"dash_update_{idx}"):
                    price = random.randint(120, 1000)
                    r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
                    r["last_tracked"] = datetime.now().isoformat()
                    save_routes(routes, commit_and_push=True)
                    append_log(f"{datetime.now().isoformat()} - Manual update {r['id']} price={price}")
                    st.rerun()
            with cols[2]:
                if r.get("notifications"):
                    if st.button("Désactiver notif", key=f"dash_notif_off_{idx}"):
                        r["notifications"] = False
                        save_routes(routes, commit_and_push=True)
                        append_log(f"{datetime.now().isoformat()} - Notifications OFF {r['id']}")
                        st.rerun()
                else:
                    if st.button("Activer notif", key=f"dash_notif_on_{idx}"):
                        r["notifications"] = True
                        save_routes(routes, commit_and_push=True)
                        append_log(f"{datetime.now().isoformat()} - Notifications ON {r['id']}")
                        st.rerun()
            with cols[3]:
                if st.button("Supprimer", key=f"dash_del_{idx}"):
                    append_log(f"{datetime.now().isoformat()} - Delete route {r['id']}")
                    routes.pop(idx)
                    save_routes(routes, commit_and_push=True)
                    st.rerun()

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

            if r.get("history"):
                fig = plot_price_history(r["history"])
                st.pyplot(fig)
            else:
                st.info("Aucun historique encore pour ce vol.")
            
            # Edition
            with st.expander("✏️ Éditer ce suivi"):
                with st.form(key=f"dash_form_{r['id']}"):
                    origin_e = st.text_input("Origine (IATA)", value=r.get("origin",""))
                    dest_e = st.text_input("Destination (IATA)", value=r.get("destination",""))
                    departure_e = st.date_input("Date départ", value=(datetime.fromisoformat(r.get("departure")).date() if r.get("departure") else date.today()))
                    # allow return optional: use value=None if missing
                    try:
                        return_default = (datetime.fromisoformat(r.get("return")).date() if r.get("return") else None)
                    except Exception:
                        return_default = None
                    return_e = st.date_input("Date retour (optionnelle)", value=return_default)
                    stay_min_e = st.number_input("Séjour min (jours)", min_value=1, max_value=365, value=r.get("stay_min",1))
                    stay_max_e = st.number_input("Séjour max (jours)", min_value=1, max_value=365, value=r.get("stay_max",1))
                    target_e = st.number_input("Seuil alerte (€)", min_value=1.0, value=r.get("target_price",100.0))
                    tracking_pd_e = st.number_input("Trackings par jour", min_value=1, max_value=24, value=r.get("tracking_per_day",1))
                    notif_e = st.checkbox("Activer notifications", value=r.get("notifications",False))
                    email_e = st.text_input("Email pour ce suivi", value=r.get("email",""))
                    cabin_e = st.selectbox("Classe", ["Economy","Premium Economy","Business","First"], index=["Economy","Premium Economy","Business","First"].index(r.get("cabin_class","Economy")))
                    min_bags_e = st.number_input("Min bagages", min_value=0, max_value=5, value=r.get("min_bags",0))
                    direct_only_e = st.checkbox("Vol direct uniquement", value=r.get("direct_only",False))
                    max_stops_e = st.selectbox("Max escales", ["any",0,1,2], index=["any",0,1,2].index(r.get("max_stops","any")))
                    avoid_e = st.text_input("Compagnies à éviter", value=",".join(r.get("avoid_airlines",[])))
                    pref_e = st.text_input("Compagnies préférées", value=",".join(r.get("preferred_airlines",[])))
                    return_airport_e = st.text_input("Aéroport retour (optionnel)", value=r.get("return_airport") or "")
                    submit_edit = st.form_submit_button("Enregistrer")
                if submit_edit:
                    r.update({
                        "origin": origin_e.upper().strip(),
                        "destination": dest_e.upper().strip(),
                        "departure": departure_e.isoformat(),
                        "return": return_e.isoformat() if return_e else None,
                        "stay_min": int(stay_min_e),
                        "stay_max": int(stay_max_e),
                        "target_price": float(target_e),
                        "tracking_per_day": int(tracking_pd_e),
                        "notifications": notif_e,
                        "email": email_e.strip(),
                        "cabin_class": cabin_e,
                        "min_bags": int(min_bags_e),
                        "direct_only": direct_only_e,
                        "max_stops": max_stops_e,
                        "avoid_airlines": [x.strip().upper() for x in avoid_e.split(",") if x.strip()],
                        "preferred_airlines": [x.strip().upper() for x in pref_e.split(",") if x.strip()],
                        "return_airport": return_airport_e.upper().strip() if return_airport_e else None
                    })
                    save_routes(routes, commit_and_push=True)
                    append_log(f"{datetime.now().isoformat()} - Edited route {r['id']}")
                    st.success("Modifications enregistrées.")
                    st.rerun()

# -----------------------------
# AJOUTER SUIVI
# -----------------------------
elif tab=="Ajouter suivi":
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
        cabin_class = st.selectbox("Classe", ["Economy","Premium Economy","Business","First"])
        min_bags = st.number_input("Min bagages (préférence)", min_value=0, max_value=5, value=0)
        direct_only = st.checkbox("Vol direct uniquement (préférence)", value=False)
        max_stops = st.selectbox("Max escales (préférence)", ["any",0,1,2])
        avoid_airlines = st.text_input("Compagnies à éviter (IATA, séparées par ,)", value="")
        preferred_airlines = st.text_input("Compagnies préférées (IATA, séparées par ,)", value="")
        route_email = st.text_input("Email pour ce suivi (vide = email global)", value="")
        add_submit = st.form_submit_button("Ajouter ce suivi")
    if add_submit:
        created = 0
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
                    "cabin_class": cabin_class,
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
                created += 1
        # save and attempt git push
        save_routes(routes, commit_and_push=True)
        st.success(f"{created} Suivi(s) ajouté(s) ✔")
        st.rerun()

# -----------------------------
# RECHERCHE / SIMULATION
# -----------------------------
elif tab=="Recherche/Simulation":
    st.header("🔎 Recherche & Suggestions (Simulation)")
    st.write("Simulation de prix selon origines, destinations, date et durée de séjour.")

    with st.expander("Paramètres de recherche"):
        origins_input = st.text_input("Origines (IATA, séparées par ,)", value="PAR,CDG")
        destinations_input = st.text_input("Destinations (IATA, séparées par ,)", value="NYC,JFK,EWR")
        start_date = st.date_input("Date départ approximative", date.today() + timedelta(days=90))
        search_window_days = st.number_input("Fenêtre recherche (± jours)", min_value=0, max_value=30, value=7)
        stay_days = st.number_input("Durée de séjour (jours)", min_value=1, max_value=60, value=7)
        return_date_opt = st.date_input("Date retour (optionnelle)", value=None)
        samples_per_option = st.number_input("Échantillons par combinaison", min_value=3, max_value=30, value=8)

        if st.button("Lancer la recherche (simulation)"):
            origins = [o.strip().upper() for o in origins_input.split(",") if o.strip()]
            dests = [d.strip().upper() for d in destinations_input.split(",") if d.strip()]
            results = [
                {
                    "origin": o,
                    "destination": d,
                    "departure": (start_date + timedelta(days=delta)).isoformat(),
                    "return": (return_date_opt if return_date_opt else (start_date + timedelta(days=delta + int(stay_days)))).isoformat(),
                    "stay_days": int(stay_days),
                    "price": random.randint(120, 1200)
                }
                for o in origins for d in dests
                for delta in range(-search_window_days, search_window_days + 1)
                for _ in range(samples_per_option)
            ]
            df_res = pd.DataFrame(results)
            st.session_state["last_search"] = df_res
            st.success(f"Simulation terminée : {len(df_res)} résultats générés.")

    # Top 10 et sélection
    if "last_search" in st.session_state:
        df_res = st.session_state["last_search"]
        st.subheader("💸 Top 10 des vols les moins chers")
        top10 = df_res.sort_values("price").head(10).reset_index(drop=True)
        st.table(top10[["origin","destination","departure","return","stay_days","price"]])
        ids_input = st.text_input("Indices à ajouter (0 à 9, séparés par ,)")
        if st.button("Ajouter sélection au suivi"):
            if ids_input.strip():
                try:
                    indices = [int(i.strip()) for i in ids_input.split(",") if i.strip()]
                    created = 0
                    for idx in indices:
                        if 0 <= idx < len(top10):
                            row = top10.iloc[idx]
                            new = {
                                "id": str(uuid.uuid4()),
                                "origin": row["origin"],
                                "destination": row["destination"],
                                "departure": row["departure"],
                                "departure_flex_days": 0,
                                "return": row["return"],
                                "return_flex_days": 0,
                                "return_airport": None,
                                "stay_min": int(row["stay_days"]),
                                "stay_max": int(row["stay_days"]),
                                "target_price": float(row["price"])*0.9,
                                "tracking_per_day": 2,
                                "notifications": False,
                                "email": "",
                                "min_bags": 0,
                                "direct_only": False,
                                "max_stops": "any",
                                "avoid_airlines": [],
                                "preferred_airlines": [],
                                "history": [{"date": datetime.now().isoformat(),"price":int(row["price"])}],
                                "last_tracked": datetime.now().isoformat(),
                                "cabin_class": "Economy",
                                "stats": {}
                            }
                            routes.append(sanitize_dict(new))
                            append_log(f"{datetime.now().isoformat()} - Added from search {new['id']}")
                            created += 1
                    # save changes and attempt git push
                    save_routes(routes, commit_and_push=True)
                    st.success(f"{created} suivi(s) ajouté(s) ✔")
                except Exception as e:
                    st.error(f"Erreur dans la saisie des indices : {e}")
            else:
                st.warning("Veuillez entrer au moins un indice.")

# -----------------------------
# CONFIGURATION
# -----------------------------
elif tab=="Configuration":
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

    st.markdown("---")
    st.subheader("🔧 Push Git (optionnel)")
    st.write("Si tu veux forcer un push vers GitHub maintenant, utilise le bouton ci-dessous. Nécessite GIT_PUSH=true et GIT_PUSH_TOKEN configurés.")
    if st.button("Push routes.json vers GitHub maintenant"):
        ok, msg = False, "not attempted"
        try:
            # call save_routes with commit flag to attempt push
            save_routes(routes, commit_and_push=True)
            ok, msg = True, "attempted"
        except Exception as e:
            ok, msg = False, str(e)
        if ok:
            st.success("Tentative de push initiée — voir logs dans repository (ou GitHub Actions).")
        else:
            st.error(f"Push non effectué : {msg}")

# -----------------------------
# EXPORTS (page)
# -----------------------------
elif tab == "Exports":
    st.header("📤 Exports")
    st.write("Exporter tous les suivis ou un suivi individuel (CSV / XLSX / PDF).")

    if not routes:
        st.info("Aucun suivi à exporter.")
    else:
        export_choice = st.selectbox("Format d'export", ["CSV","XLSX","PDF"])
        st.markdown("**Exporter un suivi individuel**")
        idx_sel = st.number_input("Index du suivi", min_value=0, max_value=len(routes)-1, value=0)
        if st.button("Exporter suivi sélectionné"):
            try:
                route_to_export = [routes[int(idx_sel)]]
                if export_choice == "CSV":
                    fname, data = export_csv(route_to_export)
                elif export_choice == "XLSX":
                    fname, data = export_xlsx(route_to_export)
                else:
                    fname, data = export_pdf(route_to_export)
                st.download_button("Télécharger", data=data, file_name=fname)
            except Exception as e:
                st.error(f"Erreur export suivi {idx_sel} : {e}")

        st.markdown("---")
        st.markdown("**Exporter tous les suivis**")
        if st.button("Exporter tout"):
            try:
                if export_choice == "CSV":
                    fname, data = export_csv(routes)
                elif export_choice == "XLSX":
                    fname, data = export_xlsx(routes)
                else:
                    fname, data = export_pdf(routes)
                st.download_button("Télécharger export (tout)", data=data, file_name=fname)
            except Exception as e:
                st.error(f"Erreur export global : {e}")

# -----------------------------
# END
# -----------------------------
st.markdown("---")
st.markdown("<p style='text-align:center; color:#888;'>Flight Tracker — ©</p>", unsafe_allow_html=True)
