# ui_components.py
import streamlit as st
import random
import uuid
import pandas as pd
from datetime import date, datetime, timedelta

from utils.storage import ensure_route_fields
from utils.plotting import plot_price_history
from utils.email_utils import send_email
from exporters import export_csv, export_pdf, export_xlsx
from utils.storage import sanitize_dict


# ----------------------------------------------------------
# TOP BAR
# ----------------------------------------------------------
def render_top_bar(routes, save_routes, append_log):
    top_col1, top_col2, top_col3 = st.columns([1,2,1])
    with top_col1:
        if st.button("Mettre à jour tous (simu)"):
            for r in routes:
                price = random.randint(120, 1000)
                r.setdefault("history", []).append(
                    {"date": datetime.now().isoformat(), "price": price}
                )
                r["last_tracked"] = datetime.now().isoformat()
            save_routes(routes)
            append_log(f"{datetime.now().isoformat()} - Bulk update (simu)")
            st.success("Mise à jour globale simulée.")
            st.rerun()

    with top_col3:
        if st.button("Exporter CSV"):
            path = export_csv(routes, path="export.csv")
            st.download_button("Télécharger CSV", data=open(path, "rb").read(), file_name="export.csv")

        if st.button("Exporter PDF"):
            path = export_pdf(routes, path="export.pdf")
            st.download_button("Télécharger PDF", data=open(path, "rb").read(), file_name="export.pdf")

        if st.button("Exporter XLSX"):
            path = export_xlsx(routes, path="export.xlsx")
            st.download_button("Télécharger XLSX", data=open(path, "rb").read(), file_name="export.xlsx")


# ----------------------------------------------------------
# DASHBOARD TAB
# ----------------------------------------------------------
def render_dashboard(routes, save_routes, append_log, email_cfg, global_notif_enabled):
    st.header("📊 Dashboard — Récapitulatif des suivis")

    if not routes:
        st.info("Aucun suivi pour l'instant. Ajoute un suivi dans l'onglet « Ajouter un suivi ».") 
        return

    # Summary metrics
    total = len(routes)
    notif_on = sum(1 for r in routes if r.get("notifications"))
    c1, c2, c3 = st.columns(3)
    c1.metric("Suivis", total)
    c2.metric("Notifications ON", notif_on)
    c3.metric("Mises à jour (24h)", 0)  # Placeholder

    st.markdown("---")

    # Per-route detailed panels
    for idx, r in enumerate(routes):
        ensure_route_fields(r)
        st.subheader(f"{r['origin']} → {r['destination']}  (id: {r['id'][:8]})")
        cols = st.columns([2,1,1,1])

        # -----------------------------
        # LEFT COLUMN (Route info)
        # -----------------------------
        with cols[0]:
            st.write(
                f"**Dates :** {r.get('departure')} (±{r.get('departure_flex_days',0)} j) → "
                f"{r.get('return') or '—'} (±{r.get('return_flex_days',0)} j)\n\n"
                f"**Séjour :** {r.get('stay_min')}–{r.get('stay_max')} j\n\n"
                f"**Seuil :** {r.get('target_price')}€\n\n"
                f"**Email :** {r.get('email') or email_cfg.get('email','—')}\n\n"
                f"Priority stay : {'Oui' if r.get('priority_stay') else 'Non'}"
            )

        # -----------------------------
        # UPDATE BUTTON
        # -----------------------------
        with cols[1]:
            if st.button("Update", key=f"dash_update_{idx}"):
                price = random.randint(120, 1000)
                r.setdefault("history", []).append(
                    {"date": datetime.now().isoformat(), "price": price}
                )
                r["last_tracked"] = datetime.now().isoformat()
                save_routes(routes)
                append_log(f"{datetime.now().isoformat()} - Manual update {r['id']} price={price}")
                st.rerun()

        # -----------------------------
        # NOTIFICATION PER ROUTE
        # -----------------------------
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

        # -----------------------------
        # DELETE BUTTON
        # -----------------------------
        with cols[3]:
            if st.button("Supprimer", key=f"dash_del_{idx}"):
                append_log(f"{datetime.now().isoformat()} - Delete route {r['id']}")
                routes.pop(idx)
                save_routes(routes)
                st.rerun()

        # -----------------------------
        # PRICE HISTORY PLOT
        # -----------------------------
        if r.get("history"):
            fig = plot_price_history(r["history"])
            st.pyplot(fig)
        else:
            st.info("Aucun historique encore pour ce vol.")

        # -----------------------------
        # EDIT ROUTE EXPANDER (FULL EDIT)
        # -----------------------------
        with st.expander("✏️ Éditer ce suivi"):
            with st.form(key=f"dash_form_{r['id']}"):
                # Departure / Return
                dep_dt_default = datetime.fromisoformat(r.get("departure")) if r.get("departure") else date.today()
                departure_e = st.date_input("Date départ", value=dep_dt_default.date() if isinstance(dep_dt_default, datetime) else dep_dt_default)
                return_dt_default = datetime.fromisoformat(r.get("return")) if r.get("return") else None
                return_e = st.date_input("Date retour (optionnelle)", value=return_dt_default.date() if return_dt_default else None)
                priority_stay_e = st.checkbox("Priorité durée de séjour si pas de date de retour", value=r.get("priority_stay", False))

                target_e = st.number_input("Seuil alerte (€)", min_value=1.0, value=float(r.get("target_price", 100.0)))
                notif_e = st.checkbox("Activer notifications pour ce vol", value=r.get("notifications", False))
                email_e = st.text_input("Email pour ce suivi (vide = global)", value=r.get("email", ""))

                submit_edit = st.form_submit_button("Enregistrer les modifications")

            if submit_edit:
                r["departure"] = departure_e.isoformat()
                if return_e:
                    r["return"] = return_e.isoformat()
                    r["priority_stay"] = False
                else:
                    r["return"] = None
                    r["priority_stay"] = True
                r["target_price"] = float(target_e)
                r["notifications"] = bool(notif_e)
                r["email"] = email_e.strip()
                save_routes(routes)
                append_log(f"{datetime.now().isoformat()} - Edited route {r['id']}")
                st.success("Modifications enregistrées.")
                st.rerun()

        st.markdown("---")


# ----------------------------------------------------------
# ADD TAB
# ----------------------------------------------------------
def render_add_tab(routes, save_routes, append_log):
    st.header("➕ Ajouter un suivi")
    with st.form("form_add_new"):
        origin = st.text_input("Origine (IATA)", value="PAR")
        destination = st.text_input("Destination (IATA)", value="TYO")
        departure_date = st.date_input("Date départ", date.today() + timedelta(days=90))
        return_date = st.date_input("Date retour (optionnelle)", value=None)
        stay_days = st.number_input("Durée de séjour (jours)", min_value=1, max_value=60, value=7)
        add_submit = st.form_submit_button("Ajouter ce suivi")

    if add_submit:
        new = {
            "id": str(uuid.uuid4()),
            "origin": origin.upper(),
            "destination": destination.upper(),
            "departure": departure_date.isoformat(),
            "return": return_date.isoformat() if return_date else None,
            "priority_stay": return_date is None,
            "stay_min": stay_days,
            "stay_max": stay_days,
            "target_price": 450,
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
        routes.append(sanitize_dict(new))
        append_log(f"{datetime.now().isoformat()} - Added route {new['id']}")
        save_routes(routes)
        st.success("Suivi ajouté ✔")
        st.rerun()


# ----------------------------------------------------------
# CONFIG TAB
# ----------------------------------------------------------
def render_config_tab(email_cfg, save_email_config, global_notif_enabled):
    st.header("⚙️ Configuration générale")
    notif_toggle = st.checkbox("Activer les notifications globales", value=global_notif_enabled)
    global_email = st.text_input("Email global", value=email_cfg.get("email", ""))
    if st.button("💾 Enregistrer la configuration"):
        email_cfg["enabled"] = bool(notif_toggle)
        email_cfg["email"] = global_email.strip()
        save_email_config(email_cfg)
        st.success("Configuration enregistrée ✔")


# ----------------------------------------------------------
# SEARCH TAB
# ----------------------------------------------------------
def render_search_tab(routes, save_routes, append_log):
    st.header("🔎 Recherche & Suggestions (Simulation)")
    st.write("Simulation de prix selon origines, destinations, date et durée de séjour.")

    origins_input = st.text_input("Origines (IATA, séparées par ,)", value="PAR,CDG")
    destinations_input = st.text_input("Destinations (IATA, séparées par ,)", value="NYC,JFK")
    start_date = st.date_input("Date départ approximative", date.today() + timedelta(days=90))
    stay_days = st.number_input("Durée de séjour (jours)", min_value=1, max_value=60, value=7)
    return_date_opt = st.date_input("Date retour (optionnelle)", value=None)
    samples_per_option = st.number_input("Échantillons par combinaison", min_value=3, max_value=30, value=5)

    if st.button("Lancer la recherche (simulation)"):
        origins = [o.strip().upper() for o in origins_input.split(",") if o.strip()]
        dests = [d.strip().upper() for d in destinations_input.split(",") if d.strip()]
        results = [
            {
                "origin": o,
                "destination": d,
                "departure": (start_date + timedelta(days=random.randint(0, 10))).isoformat(),
                "return": (return_date_opt if return_date_opt else (start_date + timedelta(days=stay_days))).isoformat(),
                "stay_days": stay_days,
                "price": random.randint(120, 1200),
                "id": str(uuid.uuid4())
            }
            for o in origins for d in dests
        ]
        df_res = pd.DataFrame(results)
        st.session_state["last_search"] = df_res
        st.success(f"Simulation terminée : {len(df_res)} résultats générés.")

    if "last_search" in st.session_state:
        df_res = st.session_state["last_search"]

        # Multiselect via ID
        with st.form("add_from_search"):
            mapping = [
                {"id": row["id"], "desc": f"{row['origin']}→{row['destination']} ({row['departure']}) — {row['price']}€"}
                for _, row in df_res.iterrows()
            ]
            st.table(pd.DataFrame(mapping))
            selected_ids = st.multiselect(
                "Sélectionner les résultats à ajouter", options=[m["id"] for m in mapping], format_func=lambda i: i
            )
            add_submit = st.form_submit_button("Ajouter")

        if add_submit and selected_ids:
            created = 0
            for sel_id in selected_ids:
                row = next((r for _, r in df_res.iterrows() if r["id"] == sel_id), None)
                if row is None:
                    continue
                priority = False
                return_iso = row["return"] if row.get("return") else None
                if return_iso is None:
                    priority = True
                new = {
                    "id": str(uuid.uuid4()),
                    "origin": row["origin"],
                    "destination": row["destination"],
                    "departure": row["departure"],
                    "return": return_iso,
                    "priority_stay": priority,
                    "stay_min": int(row["stay_days"]),
                    "stay_max": int(row["stay_days"]),
                    "target_price": float(row["price"]) * 0.9,
                    "tracking_per_day": 2,
                    "notifications": False,
                    "email": "",
                    "min_bags": 0,
                    "direct_only": False,
                    "max_stops": "any",
                    "avoid_airlines": [],
                    "preferred_airlines": [],
                    "history": [{"date": datetime.now().isoformat(), "price": int(row["price"])}],
                    "last_tracked": datetime.now().isoformat(),
                    "stats": {}
                }
                routes.append(sanitize_dict(new))
                append_log(f"{datetime.now().isoformat()} - Added from search {new['id']}")
                created += 1
            save_routes(routes)
            st.success(f"{created} suivi(s) ajouté(s) ✔")
            st.rerun()
