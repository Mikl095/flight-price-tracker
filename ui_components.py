import streamlit as st
import random
from datetime import datetime, timedelta, date
from utils.storage import save_routes, ensure_route_fields, append_log, sanitize_dict
from utils.plotting import plot_price_history
from utils.email_utils import send_email
import uuid

# ------------------------------------------------------------
# TOP BAR (mise à jour globale + export)
# ------------------------------------------------------------
def render_top_bar(routes):
    col1, col2, col3 = st.columns([1,2,1])
    with col1:
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
            st.experimental_rerun()
    # Export
    with col3:
        st.write("Export options can be added here (CSV/PDF/XLSX)")

# ------------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------------
def render_dashboard(routes, email_cfg):
    st.header("📊 Dashboard — Récapitulatif des suivis")
    if not routes:
        st.info("Aucun suivi pour l'instant.")
        return

    # Metrics
    total = len(routes)
    notif_on = sum(1 for r in routes if r.get("notifications"))
    st.metric("Suivis", total)
    st.metric("Notifications ON", notif_on)
    st.markdown("---")

    # Table récap
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
    st.dataframe(df_rows, use_container_width=True)
    st.markdown("---")

    # Panels par route
    for idx, r in enumerate(routes):
        ensure_route_fields(r)
        st.subheader(f"{r['origin']} → {r['destination']}  (id: {r['id'][:8]})")
        cols = st.columns([2,1,1,1])
        # LEFT COLUMN INFO
        with cols[0]:
            st.write(
                f"**Dates :** {r.get('departure')} (±{r.get('departure_flex_days',0)} j) → "
                f"{r.get('return') or '—'} (±{r.get('return_flex_days',0)} j)\n\n"
                f"**Séjour :** {r.get('stay_min')}–{r.get('stay_max')} j\n\n"
                f"**Seuil :** {r.get('target_price')}€\n\n"
                f"**Email :** {r.get('email') or email_cfg.get('email','—')}"
            )
        # UPDATE BUTTON
        with cols[1]:
            if st.button("Update", key=f"dash_update_{idx}"):
                price = random.randint(120, 1000)
                r.setdefault("history", []).append(
                    {"date": datetime.now().isoformat(), "price": price}
                )
                r["last_tracked"] = datetime.now().isoformat()
                save_routes(routes)
                append_log(f"{datetime.now().isoformat()} - Manual update {r['id']} price={price}")
                st.experimental_rerun()
        # Notifications
        with cols[2]:
            if r.get("notifications"):
                if st.button("Désactiver notif", key=f"dash_notif_off_{idx}"):
                    r["notifications"] = False
                    save_routes(routes)
                    append_log(f"{datetime.now().isoformat()} - Notifications OFF {r['id']}")
                    st.experimental_rerun()
            else:
                if st.button("Activer notif", key=f"dash_notif_on_{idx}"):
                    r["notifications"] = True
                    save_routes(routes)
                    append_log(f"{datetime.now().isoformat()} - Notifications ON {r['id']}")
                    st.experimental_rerun()
        # DELETE BUTTON
        with cols[3]:
            if st.button("Supprimer", key=f"dash_del_{idx}"):
                append_log(f"{datetime.now().isoformat()} - Delete route {r['id']}")
                routes.pop(idx)
                save_routes(routes)
                st.experimental_rerun()
        # PRICE HISTORY
        if r.get("history"):
            fig = plot_price_history(r["history"])
            st.pyplot(fig)
        else:
            st.info("Aucun historique pour ce vol.")

        # EDIT ROUTE (FULL FORM)
        with st.expander("✏️ Éditer ce suivi"):
            with st.form(key=f"dash_form_{r['id']}"):
                # Dates
                dep_dt_default = datetime.fromisoformat(r.get("departure")) if r.get("departure") else date.today()
                dep_default = dep_dt_default.date() if isinstance(dep_dt_default, datetime) else dep_dt_default
                departure_e = st.date_input("Date départ", value=dep_default)
                depflex = st.number_input("Flex départ ± jours", min_value=0,max_value=30,value=int(r.get("departure_flex_days",0)))
                # Retour optionnel
                return_dt_default = datetime.fromisoformat(r.get("return")) if r.get("return") else None
                return_default = return_dt_default.date() if return_dt_default else None
                return_e = st.date_input("Date retour (optionnelle)", value=return_default)
                return_flex_e = st.number_input("Flex retour ± jours", min_value=0,max_value=30,value=int(r.get("return_flex_days",0)))
                # Séjour si pas de retour
                stay_min_e = st.number_input("Séjour min (jours)", min_value=1,max_value=365,value=int(r.get("stay_min",1)))
                stay_max_e = st.number_input("Séjour max (jours)", min_value=1,max_value=365,value=int(r.get("stay_max",1)))
                # Prix
                target_e = st.number_input("Seuil alerte (€)", min_value=1.0,value=float(r.get("target_price",100)))
                tracking_pd_e = st.number_input("Trackings/jour", min_value=1,max_value=24,value=int(r.get("tracking_per_day",1)))
                notif_e = st.checkbox("Activer notifications", value=bool(r.get("notifications",False)))
                email_e = st.text_input("Email pour ce suivi", value=r.get("email",""))
                # Préférences
                min_bags_e = st.number_input("Min bagages", min_value=0,max_value=5,value=int(r.get("min_bags",0)))
                direct_only_e = st.checkbox("Vol direct uniquement", value=r.get("direct_only",False))
                max_stops_e = st.selectbox("Max escales", ["any",0,1,2], index=["any",0,1,2].index(r.get("max_stops","any")))
                avoid_e = st.text_input("Compagnies à éviter", value=",".join(r.get("avoid_airlines",[])))
                pref_e = st.text_input("Compagnies préférées", value=",".join(r.get("preferred_airlines",[])))
                submit_edit = st.form_submit_button("Enregistrer modifications")
            if submit_edit:
                r["departure"] = departure_e.isoformat()
                r["departure_flex_days"] = int(depflex)
                r["return"] = return_e.isoformat() if return_e else None
                r["return_flex_days"] = int(return_flex_e)
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
                st.success("Modifications enregistrées")
                st.experimental_rerun()

# ------------------------------------------------------------
# SEARCH TAB (ADD FROM SUGGESTIONS)
# ------------------------------------------------------------
def render_search_tab(df_res, routes):
    st.subheader("➕ Ajouter un ou plusieurs résultats comme suivi")
    if df_res.empty:
        st.info("Aucun résultat de recherche")
        return
    with st.form("add_from_search"):
        # Multi-select via IDs
        selected_ids = st.multiselect(
            "Sélectionner les résultats à ajouter",
            options=list(df_res["id"]),
            format_func=lambda x: f"{df_res.loc[df_res['id']==x,'origin'].values[0]} → {df_res.loc[df_res['id']==x,'destination'].values[0]} ({df_res.loc[df_res['id']==x,'departure'].values[0]})"
        )
        add_submit = st.form_submit_button("Ajouter")
    if add_submit and selected_ids:
        for sid in selected_ids:
            row = df_res[df_res["id"]==sid].iloc[0]
            new = {
                "id": str(uuid.uuid4()),
                "origin": row["origin"],
                "destination": row["destination"],
                "departure": row["departure"],
                "return": None,
                "departure_flex_days": 0,
                "return_flex_days": 0,
                "stay_min": int(row.get("stay_days",1)),
                "stay_max": int(row.get("stay_days",1)),
                "target_price": float(row["price"])*0.9,
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
        save_routes(routes)
        st.success(f"{len(selected_ids)} suivi(s) ajouté(s)")
        st.experimental_rerun()
