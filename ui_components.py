import streamlit as st
import random
from datetime import datetime, timedelta
from utils.storage import save_routes, count_updates_last_24h, ensure_route_fields, sanitize_dict
from utils.plotting import plot_price_history
from utils.email_utils import send_email
import uuid
import pandas as pd

# ============================================================
# TOP BAR / QUICK ACTIONS
# ============================================================
def render_top_bar(routes):
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("Mettre à jour tous (simu)"):
            for r in routes:
                price = random.randint(120, 1000)
                r.setdefault("history", []).append(
                    {"date": datetime.now().isoformat(), "price": price}
                )
                r["last_tracked"] = datetime.now().isoformat()
            save_routes(routes)
            st.success("Mise à jour globale simulée.")
            st.experimental_rerun()

    with col3:
        st.write("Exporter… (à compléter selon tes besoins)")


# ============================================================
# DASHBOARD
# ============================================================
def render_dashboard(routes, email_cfg):
    st.header("📊 Dashboard")
    if not routes:
        st.info("Aucun suivi pour l'instant.")
        return

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

    # Detailed per route
    for idx, r in enumerate(routes):
        ensure_route_fields(r)
        st.subheader(f"{r['origin']} → {r['destination']}  (id: {r['id'][:8]})")
        cols = st.columns([2,1,1,1])

        # LEFT: info
        with cols[0]:
            st.write(f"**Dates :** {r.get('departure')} → {r.get('return') or '—'}\n"
                     f"**Séjour :** {r.get('stay_min')}–{r.get('stay_max')} j\n"
                     f"**Seuil :** {r.get('target_price')}€\n"
                     f"**Email :** {r.get('email') or email_cfg.get('email','—')}")

        # UPDATE button
        with cols[1]:
            if st.button("Update", key=f"dash_update_{idx}"):
                price = random.randint(120, 1000)
                r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
                r["last_tracked"] = datetime.now().isoformat()
                save_routes(routes)
                st.success(f"Updated {r['origin']}→{r['destination']}")
                st.experimental_rerun()

        # Notification toggle
        with cols[2]:
            if r.get("notifications"):
                if st.button("Désactiver notif", key=f"dash_notif_off_{idx}"):
                    r["notifications"] = False
                    save_routes(routes)
                    st.experimental_rerun()
            else:
                if st.button("Activer notif", key=f"dash_notif_on_{idx}"):
                    r["notifications"] = True
                    save_routes(routes)
                    st.experimental_rerun()

        # DELETE
        with cols[3]:
            if st.button("Supprimer", key=f"dash_del_{idx}"):
                routes.pop(idx)
                save_routes(routes)
                st.experimental_rerun()

        # PRICE HISTORY
        if r.get("history"):
            fig = plot_price_history(r["history"])
            st.pyplot(fig)
        else:
            st.info("Aucun historique encore pour ce vol.")

        # EDIT
        with st.expander("✏️ Éditer ce suivi"):
            with st.form(key=f"dash_form_{r['id']}"):

                departure_e = st.date_input("Date départ", value=datetime.fromisoformat(r.get("departure")).date() if r.get("departure") else datetime.today())
                # Retour optionnel
                if r.get("return") is not None:
                    return_e_default = datetime.fromisoformat(r["return"]).date()
                else:
                    return_e_default = None
                return_e = st.date_input("Date retour (optionnelle)", value=return_e_default)
                stay_days = st.number_input("Durée de séjour si pas de retour", min_value=1, max_value=365,
                                            value=r.get("stay_min"))

                target_e = st.number_input("Seuil alerte (€)", value=r.get("target_price"))
                notif_e = st.checkbox("Activer notifications", value=r.get("notifications"))
                email_e = st.text_input("Email", value=r.get("email",""))

                submit_edit = st.form_submit_button("Enregistrer")
            if submit_edit:
                r["departure"] = departure_e.isoformat()
                r["return"] = return_e.isoformat() if return_e else None
                if not return_e:
                    r["stay_min"] = stay_days
                    r["stay_max"] = stay_days
                r["target_price"] = target_e
                r["notifications"] = notif_e
                r["email"] = email_e
                save_routes(routes)
                st.success("Modifications enregistrées")
                st.experimental_rerun()


# ============================================================
# SEARCH TAB
# ============================================================
def render_search_tab(df_res, routes):
    st.dataframe(df_res)

    with st.form("add_from_search"):
        selected_ids = st.multiselect(
            "Sélectionner les résultats à ajouter",
            options=list(df_res['id']),
            format_func=lambda x: f"{df_res.loc[df_res['id']==x, 'origin'].values[0]} → {df_res.loc[df_res['id']==x, 'destination'].values[0]} ({df_res.loc[df_res['id']==x, 'departure'].values[0]})"
        )
        add_submit = st.form_submit_button("Ajouter")

    if add_submit and selected_ids:
        for sid in selected_ids:
            row = df_res[df_res['id']==sid].iloc[0]
            new = {
                "id": str(uuid.uuid4()),
                "origin": row["origin"],
                "destination": row["destination"],
                "departure": row["departure"],
                "return": None,
                "stay_min": int(row.get("stay_days", 7)),
                "stay_max": int(row.get("stay_days", 7)),
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
        save_routes(routes)
        st.success(f"{len(selected_ids)} suivi(s) ajouté(s) ✔")
        st.experimental_rerun()
