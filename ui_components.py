# ui_components.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import uuid
import random

from utils.storage import (
    ensure_data_file, load_routes, save_routes,
    load_email_config, save_email_config,
    append_log, count_updates_last_24h, ensure_route_fields, sanitize_dict
)
from utils.plotting import plot_price_history
from email_utils import send_email
from exporters_detailed import export_xlsx_detailed, export_pdf_detailed

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
        if st.button("Exporter XLSX détaillé"):
            path = export_xlsx_detailed(routes)
            st.download_button("Télécharger XLSX détaillé", data=open(path,"rb").read(), file_name="export_detailed.xlsx")
        if st.button("Exporter PDF détaillé"):
            path = export_pdf_detailed(routes)
            st.download_button("Télécharger PDF détaillé", data=open(path,"rb").read(), file_name="export_detailed.pdf")


# -----------------------------
# DASHBOARD
# -----------------------------
def render_dashboard(routes, email_cfg):
    st.header("📊 Dashboard — Récapitulatif des suivis")
    if not routes:
        st.info("Aucun suivi pour l'instant. Ajoute un suivi dans l'onglet « Ajouter un suivi ».") 
        return

    # Résumé métriques
    total = len(routes)
    notif_on = sum(1 for r in routes if r.get("notifications"))
    updates_24h = sum(count_updates_last_24h(r) for r in routes)
    c1, c2, c3 = st.columns(3)
    c1.metric("Suivis", total)
    c2.metric("Notifications ON", notif_on)
    c3.metric("Mises à jour (24h)", updates_24h)
    st.markdown("---")

    for idx, r in enumerate(routes):
        ensure_route_fields(r)
        st.subheader(f"{r['origin']} → {r['destination']} (id: {r['id'][:8]})")
        cols = st.columns([2,1,1,1])

        # LEFT COL
        with cols[0]:
            st.write(
                f"**Dates :** {r.get('departure')} (±{r.get('departure_flex_days',0)} j) → "
                f"{r.get('return')} (±{r.get('return_flex_days',0)} j)\n"
                f"**Classe :** {r.get('travel_class','Economy')}\n"
                f"**Aéroport retour :** {r.get('return_airport') or '—'}\n"
                f"**Séjour :** {r.get('stay_min')}–{r.get('stay_max')} j\n"
                f"**Seuil :** {r.get('target_price')}€\n"
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

        # PRICE HISTORY
        if r.get("history"):
            fig = plot_price_history(r["history"])
            st.pyplot(fig)
        else:
            st.info("Aucun historique encore pour ce vol.")

        # EDIT ROUTE
        render_edit_route(r, routes, email_cfg)


# -----------------------------
# EDIT ROUTE
# -----------------------------
def render_edit_route(r, routes, email_cfg):
    with st.expander("✏️ Éditer ce suivi"):
        with st.form(key=f"dash_form_{r['id']}"):
            origin_e = st.text_input("Origine (IATA)", value=r.get("origin", ""))
            dest_e = st.text_input("Destination (IATA)", value=r.get("destination", ""))
            departure_e = st.date_input("Date départ", value=date.today())
            return_e = st.date_input("Date retour (optionnelle)", value=None)
            stay_min_e = st.number_input("Séjour min (jours)", min_value=1, max_value=365, value=int(r.get("stay_min",1)))
            stay_max_e = st.number_input("Séjour max (jours)", min_value=1, max_value=365, value=int(r.get("stay_max",1)))
            target_e = st.number_input("Seuil alerte (€)", min_value=1.0, value=float(r.get("target_price",100.0)))
            notif_e = st.checkbox("Activer notifications pour ce vol", value=r.get("notifications", False))
            email_e = st.text_input("Email pour ce suivi (vide = global)", value=r.get("email",""))
            travel_class_e = st.selectbox("Classe voyage", ["Economy","Premium Economy","Business","First"], index=["Economy","Premium Economy","Business","First"].index(r.get("travel_class","Economy")))
            submit_edit = st.form_submit_button("Enregistrer les modifications")

        if submit_edit:
            r.update({
                "origin": origin_e.upper().strip(),
                "destination": dest_e.upper().strip(),
                "departure": departure_e.isoformat(),
                "return": return_e.isoformat() if return_e else None,
                "stay_min": int(stay_min_e),
                "stay_max": int(stay_max_e),
                "target_price": float(target_e),
                "notifications": bool(notif_e),
                "email": email_e.strip(),
                "travel_class": travel_class_e
            })
            ensure_route_fields(r)
            save_routes(routes)
            append_log(f"{datetime.now().isoformat()} - Edited route {r['id']}")
            st.success("Modifications enregistrées.")
            st.rerun()


# -----------------------------
# ADD TAB
# -----------------------------
def render_add_tab(routes):
    st.header("➕ Ajouter un suivi")
    with st.form("form_add_new"):
        origins = st.text_area("Origines (IATA, séparées par ,)", value="PAR")
        destinations = st.text_area("Destinations (IATA, séparées par ,)", value="TYO")
        departure_date = st.date_input("Date départ (approx.)", date.today() + timedelta(days=90))
        return_date = st.date_input("Date retour (optionnelle)", value=None)
        stay_min = st.number_input("Séjour min (jours)", min_value=1, max_value=365, value=6)
        stay_max = st.number_input("Séjour max (jours)", min_value=1, max_value=365, value=10)
        target_price = st.number_input("Seuil alerte (€)", min_value=1.0, value=450.0)
        notif_on = st.checkbox("Activer notifications", value=True)
        email_route = st.text_input("Email pour ce suivi (vide = global)", value="")
        travel_class = st.selectbox("Classe voyage", ["Economy","Premium Economy","Business","First"])
        add_submit = st.form_submit_button("Ajouter ce suivi")

    if add_submit:
        for o in [x.strip().upper() for x in origins.split(",") if x.strip()]:
            for d in [x.strip().upper() for x in destinations.split(",") if x.strip()]:
                new = {
                    "id": str(uuid.uuid4()),
                    "origin": o,
                    "destination": d,
                    "departure": departure_date.isoformat(),
                    "return": return_date.isoformat() if return_date else None,
                    "stay_min": int(stay_min),
                    "stay_max": int(stay_max),
                    "target_price": float(target_price),
                    "notifications": bool(notif_on),
                    "email": email_route.strip(),
                    "travel_class": travel_class,
                    "history": [],
                    "last_tracked": None,
                    "stats": {}
                }
                routes.append(sanitize_dict(new))
                append_log(f"{datetime.now().isoformat()} - Added route {new['id']}")
        save_routes(routes)
        st.success("Suivi(s) ajouté(s) ✔")
        st.rerun()


# -----------------------------
# SEARCH TAB
# -----------------------------
def render_search_tab(routes):
    import random
    st.header("🔎 Recherche & Suggestions (Simulation)")
    with st.expander("Paramètres de recherche"):
        origins_input = st.text_input("Origines (IATA, séparées par ,)", value="PAR,CDG")
        destinations_input = st.text_input("Destinations (IATA, séparées par ,)", value="NYC,JFK,EWR")
        start_date = st.date_input("Date départ approx.", date.today() + timedelta(days=90))
        stay_days = st.number_input("Durée de séjour (jours)", min_value=1, max_value=60, value=7)
        return_date_opt = st.date_input("Date retour (optionnelle)", value=None)
        if st.button("Lancer la recherche (simulation)"):
            origins = [x.strip().upper() for x in origins_input.split(",") if x.strip()]
            dests = [x.strip().upper() for x in destinations_input.split(",") if x.strip()]
            results = []
            for o in origins:
                for d in dests:
                    for _ in range(8):
                        dep = start_date + timedelta(days=random.randint(-3,3))
                        ret = return_date_opt or (dep + timedelta(days=stay_days))
                        price = random.randint(120,1200)
                        results.append({
                            "origin": o,
                            "destination": d,
                            "departure": dep.isoformat(),
                            "return": ret.isoformat() if ret else None,
                            "stay_days": stay_days,
                            "price": price
                        })
            df_res = pd.DataFrame(results)
            st.session_state["last_search"] = df_res
            st.success(f"Simulation terminée : {len(df_res)} résultats générés.")

    # Top 10 et ajout
    if "last_search" in st.session_state:
        df_res = st.session_state["last_search"]
        st.subheader("💸 Top 10 des vols les moins chers")
        top10 = df_res.sort_values("price").head(10).reset_index(drop=True)
        st.table(top10[["origin","destination","departure","return","stay_days","price"]])

        st.subheader("➕ Ajouter un ou plusieurs résultats comme suivi (Top 10 uniquement)")
        st.write("Indiquez les indices (0 à 9) séparés par des virgules.")
        ids_input = st.text_input("Indices à ajouter (ex: 0,2,5)")
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
                                "return": row["return"],
                                "stay_min": int(row["stay_days"]),
                                "stay_max": int(row["stay_days"]),
                                "target_price": float(row["price"])*0.9,
                                "notifications": False,
                                "email": "",
                                "travel_class": "Economy",
                                "history": [{"date": datetime.now().isoformat(), "price": int(row["price"])}],
                                "last_tracked": datetime.now().isoformat(),
                                "stats": {}
                            }
                            routes.append(sanitize_dict(new))
                            append_log(f"{datetime.now().isoformat()} - Added from search {new['id']}")
                            created += 1
                    save_routes(routes)
                    st.success(f"{created} suivi(s) ajouté(s) ✔")
                except Exception as e:
                    st.error(f"Erreur : {e}")
            else:
                st.warning("Veuillez entrer au moins un indice.")


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
