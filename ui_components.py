# ui_components.py
import streamlit as st
from datetime import datetime, timedelta
import random
from utils.storage import ensure_route_fields, save_routes, append_log, count_updates_last_24h, sanitize_dict
from utils.plotting import plot_price_history
from utils.email_utils import send_email

# ----------------------------
# Top bar
# ----------------------------
def render_top_bar(routes, email_cfg):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("Mettre à jour tous (simu)"):
            for r in routes:
                price = random.randint(120, 1000)
                r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
                r["last_tracked"] = datetime.now().isoformat()
            save_routes(routes)
            append_log(f"{datetime.now().isoformat()} - Bulk update (simu)")
            st.success("Mise à jour globale simulée.")
            st.experimental_rerun()
    with col3:
        st.markdown("**Exporter**")
        if st.button("CSV"):
            import pandas as pd
            df = pd.DataFrame(routes)
            df.to_csv("export.csv", index=False)
            st.download_button("Télécharger CSV", data=open("export.csv","rb").read(), file_name="export.csv")
        if st.button("PDF"):
            # Placeholder PDF export
            with open("export.pdf","wb") as f: f.write(b"PDF Placeholder")
            st.download_button("Télécharger PDF", data=open("export.pdf","rb").read(), file_name="export.pdf")
        if st.button("XLSX"):
            import pandas as pd
            df = pd.DataFrame(routes)
            df.to_excel("export.xlsx", index=False)
            st.download_button("Télécharger XLSX", data=open("export.xlsx","rb").read(), file_name="export.xlsx")


# ----------------------------
# Dashboard tab
# ----------------------------
def render_dashboard(tab, routes, email_cfg):
    with tab:
        st.subheader("Dashboard des suivis")
        for i, r in enumerate(routes):
            ensure_route_fields(r)
            with st.expander(f"{r['origin']} → {r['destination']}"):
                st.write(f"Départ : {r['departure']}")
                st.write(f"Retour : {r['return'] or 'N/A'}")
                st.write(f"Target price : €{r['target_price']}")
                st.write(f"Notifications : {r['notifications']}")
                fig = plot_price_history(r.get("history", []))
                st.pyplot(fig)


# ----------------------------
# Ajouter / Edit tab
# ----------------------------
def render_add_tab(tab, routes):
    with tab:
        st.subheader("Ajouter un suivi")
        with st.form("add_route_form"):
            origin = st.text_input("Ville de départ")
            destination = st.text_input("Ville d'arrivée")
            departure = st.date_input("Date de départ")
            priority_stay = st.checkbox("Prioriser durée de séjour si pas de date de retour")
            return_date = st.date_input("Date de retour (optionnel)", value=None)
            target_price = st.number_input("Prix cible (€)", value=100.0)
            notifications = st.checkbox("Activer notifications")
            submit = st.form_submit_button("Ajouter")

        if submit:
            new_route = {
                "id": str(len(routes)+1),
                "origin": origin,
                "destination": destination,
                "departure": departure.isoformat(),
                "return": return_date.isoformat() if return_date else None,
                "priority_stay": priority_stay,
                "target_price": target_price,
                "notifications": notifications,
                "history": []
            }
            ensure_route_fields(new_route)
            routes.append(new_route)
            save_routes(routes)
            st.success(f"Suivi ajouté : {origin} → {destination}")


# ----------------------------
# Config tab
# ----------------------------
def render_config_tab(tab, email_cfg):
    with tab:
        st.subheader("Configuration e-mail")
        with st.form("email_form"):
            enabled = st.checkbox("Activer notifications", value=email_cfg.get("enabled", False))
            email = st.text_input("E-mail de notification", value=email_cfg.get("email", ""))
            submit = st.form_submit_button("Enregistrer")

        if submit:
            email_cfg["enabled"] = enabled
            email_cfg["email"] = email
            from utils.storage import save_email_config
            save_email_config(email_cfg)
            st.success("Configuration sauvegardée")
            if enabled:
                ok, msg = send_email(email, "Test notification", "Ceci est un test")
                st.info(f"Test e-mail : {'Succès' if ok else 'Échec'} ({msg})")


# ----------------------------
# Recherche & Suggestions
# ----------------------------
def render_search_tab(tab, routes):
    with tab:
        st.subheader("Suggestions et multi-sélection")
        import pandas as pd
        # Simuler dataframe de suggestions
        df_res = pd.DataFrame([
            {"id": r["id"], "origin": r["origin"], "destination": r["destination"], "departure": r["departure"]}
            for r in routes
        ])
        if df_res.empty:
            st.info("Pas de suggestions disponibles")
            return

        with st.form("add_from_search"):
            selected_ids = st.multiselect(
                "Sélectionner les résultats à ajouter",
                options=list(df_res["id"]),
                format_func=lambda i: f"{df_res.loc[df_res['id']==i, 'origin'].values[0]} → {df_res.loc[df_res['id']==i, 'destination'].values[0]} ({df_res.loc[df_res['id']==i, 'departure'].values[0]})"
            )
            add_submit = st.form_submit_button("Ajouter")

        if add_submit and selected_ids:
            for r in routes:
                if r["id"] in selected_ids:
                    st.success(f"Ajouté : {r['origin']} → {r['destination']}")
            append_log(f"{datetime.now().isoformat()} - Ajout suggestions {selected_ids}")
            save_routes(routes)
