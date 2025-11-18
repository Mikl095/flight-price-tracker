# ui_components.py
"""
Composants Streamlit réutilisables pour Flight Price Tracker.

Fonctions exportées :
- render_top_bar(routes, save_routes)
- render_dashboard(routes, save_routes, email_cfg, global_notif_enabled)
- render_add_tab(routes, save_routes)
- render_config_tab(email_cfg, save_email_config)
- render_search_tab(routes, save_routes)
"""
import os
import streamlit as st
from datetime import datetime, date, timedelta
import random
import uuid
import pandas as pd

# Helpers & storage
from helpers import safe_iso_to_datetime, file_bytes_for_path, sanitize_dict
from utils.storage import ensure_route_fields, count_updates_last_24h, append_log
from utils import forms as forms  # utils/forms.py (contenant add_route_form & edit_route_form)

# Plotting & email
from utils.plotting import plot_price_history
from email_utils import send_email


def render_top_bar(routes, save_routes):
    """Top quick-actions bar (bulk update + export buttons)."""
    col1, _, col3 = st.columns([1, 2, 1])
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
            from exporters import export_csv
            path = export_csv(routes, path="export.csv")
            try:
                data = file_bytes_for_path(path)
                st.download_button("Télécharger CSV", data=data, file_name="export.csv")
            except Exception as e:
                st.error(f"Erreur export CSV : {e}")

        if st.button("Exporter PDF"):
            from exporters import export_pdf
            path = export_pdf(routes, path="export.pdf")
            try:
                data = file_bytes_for_path(path)
                st.download_button("Télécharger PDF", data=data, file_name="export.pdf")
            except Exception as e:
                st.error(f"Erreur export PDF : {e}")

        if st.button("Exporter XLSX"):
            from exporters import export_xlsx
            path = export_xlsx(routes, path="export.xlsx")
            try:
                data = file_bytes_for_path(path)
                st.download_button("Télécharger XLSX", data=data, file_name="export.xlsx")
            except Exception as e:
                st.error(f"Erreur export XLSX : {e}")


def render_dashboard(routes, save_routes, email_cfg, global_notif_enabled):
    """Dashboard : métriques, tableau récap et panneaux par suivi."""
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

    st.dataframe(pd.DataFrame(df_rows), use_container_width=True)
    st.markdown("---")

    # Detailed per-route panels
    for idx, r in enumerate(routes):
        ensure_route_fields(r)

        st.subheader(f"{r['origin']} → {r['destination']}  (id: {r['id'][:8]})")
        cols = st.columns([2, 1, 1, 1])

        # LEFT: route info
        with cols[0]:
            st.write(
                f"**Dates :** {r.get('departure')} (±{r.get('departure_flex_days',0)} j) → "
                f"{r.get('return')} (±{r.get('return_flex_days',0)} j)\n\n"
                f"**Aéroport retour :** {r.get('return_airport') or '—'}\n\n"
                f"**Séjour :** {r.get('stay_min')}–{r.get('stay_max')} j\n\n"
                f"**Seuil :** {r.get('target_price')}€\n\n"
                f"**Email :** {r.get('email') or email_cfg.get('email','—')}"
            )

        # Update button
        with cols[1]:
            if st.button("Update", key=f"dash_update_{idx}"):
                price = random.randint(120, 1000)
                r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
                r["last_tracked"] = datetime.now().isoformat()
                save_routes(routes)
                append_log(f"{datetime.now().isoformat()} - Manual update {r['id']} price={price}")
                st.rerun()

        # Notification toggle (per route)
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

        # Delete
        with cols[3]:
            if st.button("Supprimer", key=f"dash_del_{idx}"):
                append_log(f"{datetime.now().isoformat()} - Delete route {r['id']}")
                routes.pop(idx)
                save_routes(routes)
                st.rerun()

        # Small actions row
        a1, a2, a3 = st.columns([1, 1, 1])

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

        # Price history plot
        if r.get("history"):
            try:
                fig = plot_price_history(r["history"])
                st.pyplot(fig)
            except Exception as e:
                st.warning(f"Impossible d'afficher le graphique : {e}")
        else:
            st.info("Aucun historique encore pour ce vol.")

        # Edit form: delegate to utils.forms.edit_route_form
        try:
            forms.edit_route_form(r, idx, routes, save_routes, append_log, email_cfg)
        except Exception as e:
            st.error(f"Erreur formulaire d'édition : {e}")

        st.markdown("---")


def render_add_tab(routes, save_routes):
    """Tab: Ajouter un suivi — délègue au formulaire centralisé."""
    try:
        forms.add_route_form(routes, save_routes, append_log)
    except Exception as e:
        st.error(f"Erreur formulaire d'ajout : {e}")


def render_config_tab(email_cfg, save_email_config):
    """Tab: Configuration générale (notifications, email global, logs)."""
    st.header("⚙️ Configuration générale")

    # Notifications globales
    st.subheader("🔔 Notifications globales")
    colA, colB = st.columns([1, 2])
    with colA:
        notif_toggle = st.checkbox("Activer les notifications globales", value=bool(email_cfg.get("enabled", False)))
    with colB:
        color = "green" if notif_toggle else "red"
        status = "ACTIVÉES" if notif_toggle else "DÉSACTIVÉES"
        st.markdown(
            f"""<div style='padding:10px; border-radius:8px; background:{color}; color:white;'>
                🔔 Notifications globales : <b>{status}</b>
            </div>""",
            unsafe_allow_html=True
        )

    # Email global
    st.subheader("📧 Email global")
    global_email = st.text_input("Adresse email par défaut pour les suivis (si champ vide dans un suivi)", value=email_cfg.get("email", ""))

    # API keys
    st.subheader("🔑 Identifiants API (si utilisés)")
    api_user = st.text_input("API user", value=email_cfg.get("api_user", ""))
    api_pass = st.text_input("API password", value=email_cfg.get("api_pass", ""), type="password")

    if st.button("💾 Enregistrer la configuration"):
        email_cfg["enabled"] = bool(notif_toggle)
        email_cfg["email"] = global_email.strip()
        email_cfg["api_user"] = api_user.strip()
        email_cfg["api_pass"] = api_pass.strip()
        try:
            save_email_config = getattr(__import__("utils.storage", fromlist=["save_email_config"]), "save_email_config")
            save_email_config(email_cfg)
            st.success("Configuration enregistrée ✔")
            st.rerun()
        except Exception as e:
            st.error(f"Impossible d'enregistrer la config : {e}")

    st.markdown("---")
    st.subheader("📝 Derniers logs")
    log_path = "last_updates.log"
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                logs = f.read()
            st.code(logs, language="text")
        except Exception as e:
            st.error(f"Impossible de lire les logs : {e}")
    else:
        st.info("Aucun log pour l'instant.")


def render_search_tab(routes, save_routes, append_log):
    """Tab: Recherche & Suggestions (Simulation)."""
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
                    "price": random.randint(120, 1200),
                    "id": str(uuid.uuid4())
                }
                for o in origins for d in dests
                for delta in range(-search_window_days, search_window_days + 1)
                for _ in range(samples_per_option)
            ]

            df_res = pd.DataFrame(results)
            st.session_state["last_search"] = df_res
            st.success(f"Simulation terminée : {len(df_res)} résultats générés.")

    # Display results if available
    if "last_search" in st.session_state:
        df_res = st.session_state["last_search"]

        st.subheader("⭐ Meilleurs prix par origine/destination")
        try:
            bests = df_res.loc[df_res.groupby(["origin", "destination"])["price"].idxmin()]
            st.dataframe(bests.sort_values("price"), use_container_width=True)
        except Exception:
            st.dataframe(df_res)

        st.subheader("💸 Top 10 des dates les moins chères")
        st.table(df_res.sort_values("price").head(10)[["origin", "destination", "departure]()]()
