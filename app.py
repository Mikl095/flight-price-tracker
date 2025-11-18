# ------------------------------------------------------------
# app.py — Flight Price Tracker — Version corrigée complète
# ------------------------------------------------------------

import streamlit as st
from datetime import date, datetime, timedelta
import random
import uuid
import pandas as pd
from io import BytesIO
import os

from utils.storage import (
    ensure_data_file, load_routes, save_routes,
    load_email_config, save_email_config,
    append_log, count_updates_last_24h, ensure_route_fields
)
from utils.plotting import plot_price_history
from exporters import export_csv, export_pdf, export_xlsx
from email_utils import send_email

# ============================================================
# HELPERS
# ============================================================

def safe_iso_to_datetime(val):
    """Return a datetime or None for different possible input types."""
    if val is None:
        return None

    if isinstance(val, datetime):
        return val

    if isinstance(val, date) and not isinstance(val, datetime):
        return datetime.combine(val, datetime.min.time())

    if isinstance(val, str):
        if not val.strip():
            return None
        try:
            return datetime.fromisoformat(val)
        except Exception:
            # try some common formats
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y"):
                try:
                    return datetime.strptime(val, fmt)
                except Exception:
                    continue
            return None

    return None


def file_bytes_for_path(path):
    with open(path, "rb") as f:
        return f.read()


# ============================================================
# INIT
# ============================================================
ensure_data_file()
routes = load_routes()
email_cfg = load_email_config()

st.set_page_config(page_title="Flight Price Tracker", layout="wide")
st.title("✈️ Flight Price Tracker — Multi-onglets (Simu)")

# Global notification status
global_notif_enabled = bool(email_cfg.get("enabled", False))

# ------------------------------------------------------------
# Notification badge
# ------------------------------------------------------------
notif_color = "🟢" if global_notif_enabled else "🔴"
st.markdown(
    f"""
    <div style='font-size:18px; margin-bottom:15px;'>
        {notif_color} <b>Notifications globales : {'ACTIVÉES' if global_notif_enabled else 'DÉSACTIVÉES'}</b>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# QUICK ACTIONS TOP BAR
# ============================================================
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
        st.download_button("Télécharger CSV", data=file_bytes_for_path(path), file_name="export.csv")

    if st.button("Exporter PDF"):
        path = export_pdf(routes, path="export.pdf")
        st.download_button("Télécharger PDF", data=file_bytes_for_path(path), file_name="export.pdf")

    if st.button("Exporter XLSX"):
        path = export_xlsx(routes, path="export.xlsx")
        st.download_button("Télécharger XLSX", data=file_bytes_for_path(path), file_name="export.xlsx")


# ============================================================
# TABS
# ============================================================
tab_dashboard, tab_add, tab_config, tab_search = st.tabs([
    "Dashboard",
    "Ajouter un suivi",
    "Configuration",
    "Recherche & Suggestions (simu)"
])

# ============================================================
# DASHBOARD TAB
# ============================================================
with tab_dashboard:
    st.header("📊 Dashboard — Récapitulatif des suivis")

    if not routes:
        st.info("Aucun suivi pour l'instant. Ajoute un suivi dans l'onglet « Ajouter un suivi ».")
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
                    f"{r.get('return')} (±{r.get('return_flex_days',0)} j)\n\n"
                    f"**Aéroport retour :** {r.get('return_airport') or '—'}\n\n"
                    f"**Séjour :** {r.get('stay_min')}–{r.get('stay_max')} j\n\n"
                    f"**Seuil :** {r.get('target_price')}€\n\n"
                    f"**Email :** {r.get('email') or email_cfg.get('email','—')}"
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
            # SMALL ACTIONS ROW
            # -----------------------------
            a1, a2, a3 = st.columns([1,1,1])

            # TEST EMAIL
            with a1:
                if st.button("Test mail", key=f"dash_testmail_{idx}"):
                    if not global_notif_enabled:
                        st.warning("Notifications globales désactivées.")
                    else:
                        rcpt = r.get("email") or email_cfg.get("email", "")
                        if not rcpt:
                            st.warning("Aucune adresse email configurée.")
                        else:
                            ok, status = send_email(
                                rcpt,
                                f"Test alerte {r['origin']}→{r['destination']}",
                                "<p>Test</p>"
                            )
                            st.info("Email envoyé" if ok else f"Erreur (status {status})")

            with a2:
                st.write(f"Last tracked: {r.get('last_tracked') or 'Never'}")

            with a3:
                st.write(f"Updates(24h): {count_updates_last_24h(r)}")

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
            # (SUITE DANS PARTIE 2)
            # ============================================================
            # EDIT ROUTE EXPANDER — FULL EDIT
            # ============================================================
            with st.expander("✏️ Éditer ce suivi"):
                with st.form(key=f"dash_form_{r['id']}"):

                    # ---- ROUTE BASE ----
                    origin_e = st.text_input("Origine (IATA)", value=r.get("origin", ""))
                    dest_e = st.text_input("Destination (IATA)", value=r.get("destination", ""))

                    # ---- DÉPART ----
                    dep_dt_default = safe_iso_to_datetime(r.get("departure"))
                    dep_default = dep_dt_default.date() if dep_dt_default else date.today()

                    departure_e = st.date_input("Date départ", value=dep_default)
                    depflex = st.number_input(
                        "Flex départ ± jours",
                        min_value=0, max_value=30,
                        value=int(r.get("departure_flex_days", 0))
                    )

                    # ---- RETOUR ----
                    ret_dt_default = safe_iso_to_datetime(r.get("return"))
                    ret_default = ret_dt_default.date() if ret_dt_default else (dep_default + timedelta(days=7))

                    return_e = st.date_input("Date retour", value=ret_default)
                    return_flex_e = st.number_input(
                        "Flex retour ± jours",
                        min_value=0, max_value=30,
                        value=int(r.get("return_flex_days", 0))
                    )

                    return_airport_e = st.text_input(
                        "Aéroport retour (IATA) — vide = même",
                        value=r.get("return_airport") or ""
                    )

                    # ---- SÉJOUR ----
                    stay_min_e = st.number_input(
                        "Séjour min (jours)",
                        min_value=1, max_value=365,
                        value=int(r.get("stay_min", 1))
                    )
                    stay_max_e = st.number_input(
                        "Séjour max (jours)",
                        min_value=1, max_value=365,
                        value=int(r.get("stay_max", 1))
                    )

                    # ---- PRIX / TRACKING ----
                    target_e = st.number_input(
                        "Seuil alerte (€)",
                        min_value=1.0,
                        value=float(r.get("target_price", 100.0))
                    )

                    tracking_pd_e = st.number_input(
                        "Trackings par jour",
                        min_value=1, max_value=24,
                        value=int(r.get("tracking_per_day", 1))
                    )

                    notif_e = st.checkbox(
                        "Activer notifications pour ce vol",
                        value=bool(r.get("notifications", False))
                    )

                    email_e = st.text_input(
                        "Email pour ce suivi (vide = global)",
                        value=r.get("email", "")
                    )

                    # ---- PREFERENCES ----
                    min_bags_e = st.number_input(
                        "Min bagages",
                        min_value=0, max_value=5,
                        value=int(r.get("min_bags", 0))
                    )

                    direct_only_e = st.checkbox(
                        "Vol direct uniquement",
                        value=r.get("direct_only", False)
                    )

                    max_stops_e = st.selectbox(
                        "Max escales",
                        ["any", 0, 1, 2],
                        index=["any", 0, 1, 2].index(r.get("max_stops", "any"))
                    )

                    avoid_e = st.text_input(
                        "Compagnies à éviter (IATA, séparées par ,)",
                        value=",".join(r.get("avoid_airlines", []))
                    )
                    pref_e = st.text_input(
                        "Compagnies préférées (IATA, séparées par ,)",
                        value=",".join(r.get("preferred_airlines", []))
                    )

                    submit_edit = st.form_submit_button("Enregistrer les modifications")

                # ---- SAVE EDIT ----
                if submit_edit:
                    r["origin"] = origin_e.upper().strip()
                    r["destination"] = dest_e.upper().strip()
                    r["departure"] = departure_e.isoformat()
                    r["departure_flex_days"] = int(depflex)

                    r["return"] = return_e.isoformat()
                    r["return_flex_days"] = int(return_flex_e)
                    r["return_airport"] = return_airport_e.upper().strip() if return_airport_e else None

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

            st.markdown("---")


# ============================================================
# TAB — AJOUTER UN SUIVI
# ============================================================
with tab_add:

    st.header("➕ Ajouter un suivi")

    with st.form("form_add_new"):

        # ---- ORIGINE / DESTINATION ----
        origin = st.text_input("Origine (IATA)", value="PAR")
        destination = st.text_input("Destination (IATA)", value="TYO")

        # ---- DÉPART ----
        departure_date = st.date_input(
            "Date départ (approx.)",
            date.today() + timedelta(days=90)
        )
        dep_flex = st.number_input(
            "Plage départ ± jours",
            min_value=0, max_value=30,
            value=1
        )

        # ---- RETOUR ----
        return_date = st.date_input(
            "Date retour (approx.)",
            value=(date.today() + timedelta(days=97))
        )
        return_flex = st.number_input(
            "Plage retour ± jours",
            min_value=0, max_value=30,
            value=1
        )
        return_airport = st.text_input(
            "Aéroport retour (IATA) — vide = même",
            ""
        )

        # ---- SÉJOUR ----
        stay_min = st.number_input(
            "Séjour min (jours)",
            min_value=1, max_value=365,
            value=6
        )
        stay_max = st.number_input(
            "Séjour max (jours)",
            min_value=1,
            max_value=365,
            value=10
        )

        # ---- PRIX / TRACKING ----
        target_price = st.number_input(
            "Seuil alerte (€)",
            min_value=1.0,
            value=450.0
        )
        tracking_per_day = st.number_input(
            "Trackings par jour",
            min_value=1, max_value=24,
            value=2
        )
        notifications_on = st.checkbox(
            "Activer notifications pour ce vol",
            value=True
        )

        # ---- PREFERENCES ----
        min_bags = st.number_input(
            "Min bagages (préférence)",
            min_value=0, max_value=5,
            value=0
        )
        direct_only = st.checkbox(
            "Vol direct uniquement (préférence)",
            value=False
        )
        max_stops = st.selectbox(
            "Max escales (préférence)",
            ["any", 0, 1, 2]
        )
        avoid_airlines = st.text_input(
            "Compagnies à éviter (IATA, séparées par ,)",
            value=""
        )
        preferred_airlines = st.text_input(
            "Compagnies préférées (IATA, séparées par ,)",
            value=""
        )

        route_email = st.text_input(
            "Email pour ce suivi (vide = email global)",
            value=""
        )

        add_submit = st.form_submit_button("Ajouter ce suivi")

    # ---- ADD NEW ROUTE ----
    if add_submit:
        new = {
            "id": str(uuid.uuid4()),

            "origin": origin.upper().strip(),
            "destination": destination.upper().strip(),

            "departure": departure_date.isoformat(),
            "departure_flex_days": int(dep_flex),

            "return": return_date.isoformat(),
            "return_flex_days": int(return_flex),

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
        save_routes(routes)
        append_log(f"{datetime.now().isoformat()} - Added route {new['id']}")

        st.success("Suivi ajouté ✔")
        st.rerun()
               # ============================================================
# TAB — CONFIGURATION
# ============================================================
with tab_config:

    st.header("⚙️ Configuration générale")

    # ----------------------------
    # Notifications globales (switch visuel + badge S2)
    # ----------------------------
    st.subheader("🔔 Notifications globales")

    colA, colB = st.columns([1,2])

    with colA:
        notif_toggle = st.checkbox(
            "Activer les notifications globales",
            value=global_notif_enabled
        )

    with colB:
        color = "green" if notif_toggle else "red"
        status = "ACTIVÉES" if notif_toggle else "DÉSACTIVÉES"
        st.markdown(
            f"""
            <div style='padding:10px; border-radius:8px; background:{color}; color:white;'>
                🔔 Notifications globales : <b>{status}</b>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ----------------------------
    # Email global
    # ----------------------------
    st.subheader("📧 Email global")

    global_email = st.text_input(
        "Adresse email par défaut pour les suivis (si champ vide dans un suivi)",
        value=email_cfg.get("email", "")
    )

    # ----------------------------
    # API keys
    # ----------------------------
    st.subheader("🔑 Identifiants API (si utilisés)")
    api_user = st.text_input("API user", value=email_cfg.get("api_user", ""))
    api_pass = st.text_input("API password", value=email_cfg.get("api_pass", ""), type="password")

    if st.button("💾 Enregistrer la configuration"):
        email_cfg["enabled"] = bool(notif_toggle)
        email_cfg["email"] = global_email.strip()
        email_cfg["api_user"] = api_user.strip()
        email_cfg["api_pass"] = api_pass.strip()

        save_email_config(email_cfg)

        st.success("Configuration enregistrée ✔")
        st.rerun()

    st.markdown("---")

    # ----------------------------
    # Logs
    # ----------------------------
    st.subheader("📝 Derniers logs")
    log_path = "last_updates.log"

    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            logs = f.read()
        st.code(logs, language="text")
    else:
        st.info("Aucun log pour l'instant.")

# ============================================================
# TAB — RECHERCHE & SUGGESTIONS (SIMU)
# ============================================================
with tab_search:

    st.header("🔎 Recherche & Suggestions (Simulation)")
    st.write("Simulation de prix selon origines, destinations, date et durée de séjour.")

    with st.expander("Paramètres de recherche"):
        origins_input = st.text_input("Origines (IATA, séparées par ,)", value="PAR,CDG")
        destinations_input = st.text_input("Destinations (IATA, séparées par ,)", value="NYC,JFK,EWR")

        start_date = st.date_input("Date départ approximative", date.today() + timedelta(days=90))
        search_window_days = st.number_input("Fenêtre recherche (± jours)", min_value=0, max_value=30, value=7)

        stay_days = st.number_input(
            "Durée de séjour (jours)",
            min_value=1,
            max_value=60,
            value=7,
            help="Si aucune date de retour n'est fournie, la durée de séjour sera utilisée."
        )

        return_date_opt = st.date_input(
            "Date retour (optionnelle)",
            value=None,
            help="Laisse vide pour utiliser uniquement la durée de séjour."
        )

        samples_per_option = st.number_input(
            "Échantillons par combinaison",
            min_value=3,
            max_value=30,
            value=8
        )

        if st.button("Lancer la recherche (simulation)"):

            origins = [o.strip().upper() for o in origins_input.split(",") if o.strip()]
            dests = [d.strip().upper() for d in destinations_input.split(",") if d.strip()]

            results = []

            for origin in origins:
                for dest in dests:

                    for delta in range(-search_window_days, search_window_days + 1):
                        dep = start_date + timedelta(days=delta)

                        # -------------------------
                        # Return date logic
                        # -------------------------
                        if return_date_opt is None:
                            ret = dep + timedelta(days=int(stay_days))  # priorité séjour
                        else:
                            ret = return_date_opt
                            # stay_days is deduced for display
                            stay_days_value = (ret - dep).days
                        # -------------------------

                        for _ in range(samples_per_option):
                            price = random.randint(120, 1200)
                            results.append({
                                "origin": origin,
                                "destination": dest,
                                "departure": dep.isoformat(),
                                "return": ret.isoformat(),
                                "stay_days": int(stay_days),
                                "price": price
                            })

            df_res = pd.DataFrame(results)
            st.session_state["last_search"] = df_res

            st.success(f"Simulation terminée : {len(df_res)} résultats générés.")

    # -------------------------
    # Display results
    # -------------------------
    if "last_search" in st.session_state:
        df_res = st.session_state["last_search"]

        bests = df_res.loc[df_res.groupby(["origin", "destination"])["price"].idxmin()]
        st.subheader("⭐ Meilleurs prix par origine/destination")
        st.dataframe(bests.sort_values("price"), use_container_width=True)

        st.subheader("💸 Top 10 des dates les moins chères")
        cheapest = df_res.sort_values("price").head(10)
        st.table(cheapest[["origin", "destination", "departure", "return", "stay_days", "price"]])

        st.markdown("---")

        # -------------------------
        # Add a result as a route
        # -------------------------
        st.subheader("➕ Ajouter un des résultats comme suivi")

        with st.form("add_from_search"):
            sel_idx = st.number_input(
                "Index résultat à ajouter",
                min_value=0,
                max_value=max(0, len(df_res) - 1),
                value=0
            )
            add_submit = st.form_submit_button("Ajouter")

        if add_submit:
            row = df_res.iloc[int(sel_idx)]

            dep_dt = safe_iso_to_datetime(row["departure"])
            ret_dt = safe_iso_to_datetime(row["return"])

            new = {
                "id": str(uuid.uuid4()),
                "origin": row["origin"],
                "destination": row["destination"],
                "departure": row["departure"],
                "departure_flex_days": 0,
                "return": ret_dt.date().isoformat() if ret_dt else "",
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
                "history": [
                    {"date": datetime.now().isoformat(), "price": row["price"]}
                ],
                "last_tracked": datetime.now().isoformat(),
                "stats": {}
            }

            routes.append(new)
            save_routes(routes)
            append_log(f"{datetime.now().isoformat()} - Added from search {new['id']}")

            st.success("Suivi ajouté depuis les suggestions ✔")
            st.rerun()

# ============================================================
# END OF APP
# ============================================================
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#888;'>Flight Tracker — Version complète corrigée ©</p>",
    unsafe_allow_html=True
        )
        
