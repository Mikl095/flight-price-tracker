# ui_components.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import uuid
import random
from utils.storage import (
    load_routes, save_routes, ensure_route_fields, sanitize_dict,
    load_email_config, save_email_config, append_log, count_updates_last_24h
)
from utils.plotting import plot_price_history
from exporters import export_csv, export_pdf, export_xlsx
from email_utils import send_email

# -----------------------------
# TOP BAR
# -----------------------------
def render_top_bar():
    st.set_page_config(page_title="Flight Price Tracker", layout="wide")
    st.title("✈️ Flight Price Tracker — Multi-onglets")
    cfg = load_email_config()
    notif_enabled = cfg.get("enabled", False)
    st.markdown(f"<b>Notifications globales : {'🟢 ACTIVÉES' if notif_enabled else '🔴 DÉSACTIVÉES'}</b>", unsafe_allow_html=True)
    st.markdown("---")

# -----------------------------
# DASHBOARD
# -----------------------------
def render_dashboard(routes):
    st.header("📊 Dashboard — Récapitulatif des suivis")
    if not routes:
        st.info("Aucun suivi pour l'instant. Ajoutez un suivi dans l'onglet « Ajouter un suivi ».")
        return

    # Récap résumé
    total = len(routes)
    notif_on = sum(1 for r in routes if r.get("notifications"))
    updates_24h = sum(count_updates_last_24h(r) for r in routes)
    c1, c2, c3 = st.columns(3)
    c1.metric("Suivis", total)
    c2.metric("Notifications ON", notif_on)
    c3.metric("Mises à jour (24h)", updates_24h)
    st.markdown("---")

    # Tableau récap
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
            "email": r.get("email") or ""
        })
    df = pd.DataFrame(df_rows)
    st.dataframe(df, use_container_width=True)
    st.markdown("---")

    # Détails par suivi
    for idx, r in enumerate(routes):
        ensure_route_fields(r)
        st.subheader(f"{r['origin']} → {r['destination']}  (id: {r['id'][:8]})")
        cols = st.columns([2,1,1,1])

        # Informations
        with cols[0]:
            st.write(
                f"**Dates :** {r.get('departure')} (±{r.get('departure_flex_days',0)} j) → "
                f"{r.get('return')} (±{r.get('return_flex_days',0)} j)\n"
                f"**Aéroport retour :** {r.get('return_airport') or '—'}\n"
                f"**Séjour :** {r.get('stay_min')}–{r.get('stay_max')} j\n"
                f"**Classe :** {r.get('cabin_class','Economy')}\n"
                f"**Vol direct uniquement :** {r.get('direct_only')}\n"
                f"**Max escales :** {r.get('max_stops')}\n"
                f"**Min bagages :** {r.get('min_bags')}\n"
                f"**Seuil :** {r.get('target_price')}€\n"
                f"**Email :** {r.get('email') or '—'}"
            )

        # Actions
        with cols[1]:
            if st.button("Update", key=f"dash_update_{idx}"):
                price = random.randint(120, 1000)
                r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
                r["last_tracked"] = datetime.now().isoformat()
                save_routes(routes)
                append_log(f"{datetime.now().isoformat()} - Manual update {r['id']} price={price}")
                st.rerun()
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
        with cols[3]:
            if st.button("Supprimer", key=f"dash_del_{idx}"):
                append_log(f"{datetime.now().isoformat()} - Delete route {r['id']}")
                routes.pop(idx)
                save_routes(routes)
                st.rerun()

        # Infos + mail test
        a1, a2, a3 = st.columns([1,1,1])
        with a1:
            if st.button("Test mail", key=f"dash_testmail_{idx}"):
                cfg = load_email_config()
                global_enabled = cfg.get("enabled", False)
                rcpt = r.get("email") or cfg.get("email", "")
                if not global_enabled or not rcpt:
                    st.warning("Email non configuré ou notifications désactivées.")
                else:
                    ok,_ = send_email(rcpt,f"Test alerte {r['origin']}→{r['destination']}","<p>Test</p>")
                    st.info("Email envoyé" if ok else "Erreur envoi")
        with a2:
            st.write(f"Last tracked: {r.get('last_tracked') or 'Never'}")
        with a3:
            st.write(f"Updates(24h): {count_updates_last_24h(r)}")

        # Graph historique
        if r.get("history"):
            fig = plot_price_history(r["history"])
            st.pyplot(fig)
        else:
            st.info("Aucun historique encore pour ce vol.")

        # Edition
        render_edit_tab(r, routes)

# -----------------------------
# AJOUT DE SUIVI
# -----------------------------
def render_add_tab(routes):
    st.header("➕ Ajouter un suivi")
    with st.form("form_add_new"):
        origin = st.text_input("Origine (IATA)")
        destination = st.text_input("Destination (IATA)")
        departure = st.date_input("Date départ")
        return_date = st.date_input("Date retour (optionnelle)", value=None)
        return_airport = st.text_input("Aéroport retour (IATA) — vide = même")
        stay_min = st.number_input("Séjour min (jours)", min_value=1, max_value=365, value=1)
        stay_max = st.number_input("Séjour max (jours)", min_value=1, max_value=365, value=1)
        target_price = st.number_input("Seuil alerte (€)", min_value=1.0, value=100.0)
        tracking_per_day = st.number_input("Trackings par jour", min_value=1, max_value=24, value=1)
        notif_enabled = st.checkbox("Activer notifications")
        email_notify = st.text_input("Email pour notification (vide = global)")
        min_bags = st.number_input("Min bagages", min_value=0, max_value=5, value=0)
        direct_only = st.checkbox("Vol direct uniquement")
        max_stops = st.selectbox("Max escales", ["any",0,1,2])
        cabin_class = st.selectbox("Classe", ["Economy","Premium Economy","Business","First"])
        avoid_airlines = st.text_input("Compagnies à éviter (IATA, séparées par ,)", value="")
        preferred_airlines = st.text_input("Compagnies préférées (IATA, séparées par ,)", value="")
        submit_add = st.form_submit_button("Ajouter ce suivi")

    if submit_add:
        new = {
            "id": str(uuid.uuid4()),
            "origin": origin.upper().strip(),
            "destination": destination.upper().strip(),
            "departure": departure.isoformat(),
            "return": return_date.isoformat() if return_date else None,
            "return_airport": return_airport.upper().strip() if return_airport else None,
            "stay_min": int(stay_min),
            "stay_max": int(stay_max),
            "target_price": float(target_price),
            "tracking_per_day": int(tracking_per_day),
            "notifications": bool(notif_enabled),
            "email": email_notify.strip(),
            "min_bags": int(min_bags),
            "direct_only": bool(direct_only),
            "max_stops": max_stops,
            "cabin_class": cabin_class,
            "avoid_airlines": [a.strip().upper() for a in avoid_airlines.split(",") if a.strip()],
            "preferred_airlines": [a.strip().upper() for a in preferred_airlines.split(",") if a.strip()],
            "history": [],
            "last_tracked": None,
            "stats": {}
        }
        ensure_route_fields(new)
        routes.append(new)
        save_routes(routes)
        append_log(f"{datetime.now().isoformat()} - Added route {new['id']}")
        st.success("Suivi ajouté ✔")
        st.rerun()

# -----------------------------
# EDITION DE SUIVI
# -----------------------------
def render_edit_tab(r, routes):
    with st.expander("✏️ Éditer ce suivi"):
        with st.form(f"edit_form_{r['id']}"):
            origin = st.text_input("Origine", value=r.get("origin",""))
            destination = st.text_input("Destination", value=r.get("destination",""))
            departure = st.date_input("Date départ", value=datetime.fromisoformat(r["departure"]) if r.get("departure") else date.today())
            return_date = st.date_input("Date retour (optionnelle)", value=datetime.fromisoformat(r["return"]) if r.get("return") else None)
            return_airport = st.text_input("Aéroport retour", value=r.get("return_airport",""))
            stay_min = st.number_input("Séjour min (jours)", value=r.get("stay_min",1))
            stay_max = st.number_input("Séjour max (jours)", value=r.get("stay_max",1))
            target_price = st.number_input("Seuil alerte (€)", value=r.get("target_price",100.0))
            tracking_per_day = st.number_input("Trackings par jour", value=r.get("tracking_per_day",1))
            notif_enabled = st.checkbox("Activer notifications", value=r.get("notifications",False))
            email_notify = st.text_input("Email pour notification", value=r.get("email",""))
            min_bags = st.number_input("Min bagages", value=r.get("min_bags",0))
            direct_only = st.checkbox("Vol direct uniquement", value=r.get("direct_only",False))
            max_stops = st.selectbox("Max escales", ["any",0,1,2], index=["any",0,1,2].index(r.get("max_stops","any")))
            cabin_class = st.selectbox("Classe", ["Economy","Premium Economy","Business","First"], index=["Economy","Premium Economy","Business","First"].index(r.get("cabin_class","Economy")))
            avoid_airlines = st.text_input("Compagnies à éviter", value=",".join(r.get("avoid_airlines",[])))
            preferred_airlines = st.text_input("Compagnies préférées", value=",".join(r.get("preferred_airlines",[])))
            submit = st.form_submit_button("Enregistrer")

        if submit:
            r.update({
                "origin": origin.upper().strip(),
                "destination": destination.upper().strip(),
                "departure": departure.isoformat(),
                "return": return_date.isoformat() if return_date else None,
                "return_airport": return_airport.upper().strip() if return_airport else None,
                "stay_min": int(stay_min),
                "stay_max": int(stay_max),
                "target_price": float(target_price),
                "tracking_per_day": int(tracking_per_day),
                "notifications": bool(notif_enabled),
                "email": email_notify.strip(),
                "min_bags": int(min_bags),
                "direct_only": bool(direct_only),
                "max_stops": max_stops,
                "cabin_class": cabin_class,
                "avoid_airlines": [a.strip().upper() for a in avoid_airlines.split(",") if a.strip()],
                "preferred_airlines": [a.strip().upper() for a in preferred_airlines.split(",") if a.strip()]
            })
            ensure_route_fields(r)
            save_routes(routes)
            append_log(f"{datetime.now().isoformat()} - Edited route {r['id']}")
            st.success("Modifications enregistrées ✔")
            st.rerun()

# -----------------------------
# RECHERCHE / SIMULATION
# -----------------------------
def render_search_tab(routes):
    st.header("🔎 Recherche & Suggestions (Simulation)")
    origins_input = st.text_input("Origines (IATA, séparées par ,)", value="PAR,CDG")
    destinations_input = st.text_input("Destinations (IATA, séparées par ,)", value="NYC,JFK")
    start_date = st.date_input("Date départ approximative", date.today()+timedelta(days=90))
    search_window = st.number_input("Fenêtre recherche ± jours", value=7)
    stay_days = st.number_input("Durée séjour (jours)", value=7)
    samples = st.number_input("Échantillons par combinaison", value=5)

    if st.button("Lancer la recherche"):
        origins = [o.strip().upper() for o in origins_input.split(",") if o.strip()]
        dests = [d.strip().upper() for d in destinations_input.split(",") if d.strip()]
        results = []
        for o in origins:
            for d in dests:
                for delta in range(-search_window, search_window+1):
                    for _ in range(samples):
                        dep = start_date + timedelta(days=delta)
                        ret = dep + timedelta(days=stay_days)
                        results.append({
                            "origin": o, "destination": d,
                            "departure": dep.isoformat(),
                            "return": ret.isoformat(),
                            "stay_days": stay_days,
                            "price": random.randint(120,1200)
                        })
        df_res = pd.DataFrame(results)
        st.session_state["last_search"] = df_res
        st.success(f"{len(df_res)} résultats générés")

    # Top 10 et multisélection
    if "last_search" in st.session_state:
        df_res = st.session_state["last_search"]
        top10 = df_res.sort_values("price").head(10).reset_index(drop=True)
        st.subheader("💸 Top 10 vols moins chers")
        st.table(top10[["origin","destination","departure","return","stay_days","price"]])
        indices_input = st.text_input("Indices à ajouter (ex: 0,2,5)")
        if st.button("Ajouter sélection au suivi"):
            if indices_input.strip():
                try:
                    indices = [int(i.strip()) for i in indices_input.split(",") if i.strip()]
                    created = 0
                    for idx in indices:
                        if 0 <= idx < len(top10):
                            row = top10.iloc[idx]
                            new = {
                                "id": str(uuid.uuid4()),
                                "origin": row["origin"], "destination": row["destination"],
                                "departure": row["departure"], "return": row["return"],
                                "stay_min": int(row["stay_days"]), "stay_max": int(row["stay_days"]),
                                "target_price": float(row["price"])*0.9, "tracking_per_day": 2,
                                "notifications": False, "email": "",
                                "min_bags": 0, "direct_only": False, "max_stops": "any",
                                "cabin_class": "Economy",
                                "avoid_airlines": [], "preferred_airlines": [],
                                "history":[{"date":datetime.now().isoformat(),"price":int(row["price"])}],
                                "last_tracked": datetime.now().isoformat(),
                                "stats": {}
                            }
                            routes.append(sanitize_dict(new))
                            append_log(f"{datetime.now().isoformat()} - Added from search {new['id']}")
                            created += 1
                    save_routes(routes)
                    st.success(f"{created} suivi(s) ajouté(s) ✔")
                except Exception as e:
                    st.error(f"Erreur indices : {e}")
            else:
                st.warning("Veuillez entrer au moins un indice.")

# -----------------------------
# EXPORT INDIVIDUEL / GLOBAL
# -----------------------------
def render_export_tab(routes):
    st.header("📤 Export")
    if routes:
        route_map = {f"{r['origin']}→{r['destination']} ({r['id'][:8]})": r for r in routes}
        selected = st.multiselect("Sélectionner suivi(s) à exporter", list(route_map.keys()))
        if st.button("Exporter sélection"):
            for key in selected:
                r = route_map[key]
                export_csv([r], f"export_{r['id']}.csv")
                export_xlsx([r], f"export_{r['id']}.xlsx")
                export_pdf([r], f"export_{r['id']}.pdf")
            st.success(f"{len(selected)} suivi(s) exporté(s) ✔")
        if st.button("Exporter tout"):
            export_csv(routes, "export_all.csv")
            export_xlsx(routes, "export_all.xlsx")
            export_pdf(routes, "export_all.pdf")
            st.success("Tous les suivis exportés ✔")
    else:
        st.info("Aucun suivi à exporter.")

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
