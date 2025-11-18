import streamlit as st
from datetime import date, datetime, timedelta
import random
import uuid
import pandas as pd
from utils.storage import ensure_route_fields, sanitize_dict
from utils.plotting import plot_price_history
from exporters import export_csv, export_pdf, export_xlsx
from utils.email_utils import send_email

# --- helpers ---
def safe_iso_to_datetime(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, date):
        return datetime.combine(val, datetime.min.time())
    if isinstance(val, str) and val.strip():
        try:
            return datetime.fromisoformat(val)
        except Exception:
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y"):
                try:
                    return datetime.strptime(val, fmt)
                except Exception:
                    continue
    return None

def file_bytes_for_path(path):
    with open(path, "rb") as f:
        return f.read()

# --- top bar ---
def render_top_bar(routes):
    col1, col2, col3 = st.columns([1,2,1])
    with col1:
        if st.button("Mettre à jour tous (simu)"):
            for r in routes:
                price = random.randint(120, 1000)
                r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
                r["last_tracked"] = datetime.now().isoformat()
            st.success("Mise à jour globale simulée.")
            st.experimental_rerun()
    with col3:
        if st.button("Exporter CSV"):
            path = export_csv(routes, path="export.csv")
            st.download_button("Télécharger CSV", data=file_bytes_for_path(path), file_name="export.csv")
        if st.button("Exporter PDF"):
            path = export_pdf(routes, path="export.pdf")
            st.download_button("Télécharger PDF", data=file_bytes_for_path(path), file_name="export.pdf")
        if st.button("Exporter XLSX"):
            path = export_xlsx(routes, path="export.xlsx")
            st.download_button("Télécharger XLSX", data=file_bytes_for_path(path), file_name="export.xlsx")

# --- dashboard tab ---
def render_dashboard(routes, email_cfg):
    st.header("📊 Dashboard — Récapitulatif des suivis")
    if not routes:
        st.info("Aucun suivi pour l'instant.")
        return

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

    for idx, r in enumerate(routes):
        ensure_route_fields(r)
        st.subheader(f"{r['origin']} → {r['destination']}  (id: {r['id'][:8]})")
        with st.expander("✏️ Éditer ce suivi"):
            with st.form(key=f"dash_form_{r['id']}"):
                dep_dt_default = safe_iso_to_datetime(r.get("departure"))
                dep_default = dep_dt_default.date() if dep_dt_default else date.today()
                departure_e = st.date_input("Date départ", value=dep_default)
                depflex = st.number_input("Flex départ ± jours", 0, 30, int(r.get("departure_flex_days",0)))

                ret_dt_default = safe_iso_to_datetime(r.get("return"))
                return_e = st.date_input("Date retour (optionnelle)", value=ret_dt_default.date() if ret_dt_default else None)
                return_flex_e = st.number_input("Flex retour ± jours", 0, 30, int(r.get("return_flex_days",0)))

                stay_min_e = st.number_input("Séjour min (jours)", 1, 365, int(r.get("stay_min",1)))
                stay_max_e = st.number_input("Séjour max (jours)", 1, 365, int(r.get("stay_max",1)))

                target_e = st.number_input("Seuil alerte (€)", 1.0, 10000.0, float(r.get("target_price",100)))
                notif_e = st.checkbox("Activer notifications", value=bool(r.get("notifications",False)))
                email_e = st.text_input("Email pour ce suivi", value=r.get("email",""))

                submit_edit = st.form_submit_button("Enregistrer")
            if submit_edit:
                r["departure"] = departure_e.isoformat()
                r["departure_flex_days"] = depflex
                if return_e:
                    r["return"] = return_e.isoformat()
                else:
                    # ajustement automatique de la durée si pas de retour
                    r["return"] = (departure_e + timedelta(days=stay_min_e)).isoformat()
                r["return_flex_days"] = return_flex_e
                r["stay_min"] = stay_min_e
                r["stay_max"] = stay_max_e
                r["target_price"] = target_e
                r["notifications"] = notif_e
                r["email"] = email_e.strip()
                st.success("Modifications enregistrées.")
                st.experimental_rerun()

# --- search tab ---
def render_search_tab(df_res, routes):
    st.header("🔎 Recherche & Suggestions")
    if df_res is None:
        st.info("Aucune recherche effectuée.")
        return

    with st.form("add_from_search"):
        selected_ids = st.multiselect(
            "Sélectionner les résultats à ajouter",
            options=df_res["id"].tolist(),
            format_func=lambda x: f"{x} — {df_res.loc[df_res['id']==x, 'origin'].values[0]} → {df_res.loc[df_res['id']==x,'destination'].values[0]}"
        )
        add_submit = st.form_submit_button("Ajouter")

    if add_submit and selected_ids:
        created = 0
        for sid in selected_ids:
            row = df_res.loc[df_res["id"]==sid].iloc[0]
            new = {
                "id": str(uuid.uuid4()),
                "origin": row["origin"],
                "destination": row["destination"],
                "departure": row["departure"],
                "return": row.get("return", None),
                "departure_flex_days": 0,
                "return_flex_days": 0,
                "stay_min": int(row.get("stay_days",7)),
                "stay_max": int(row.get("stay_days",7)),
                "target_price": float(row.get("price",100)*0.9),
                "tracking_per_day": 2,
                "notifications": False,
                "email": "",
                "min_bags": 0,
                "direct_only": False,
                "max_stops": "any",
                "avoid_airlines": [],
                "preferred_airlines": [],
                "history": [{"date": datetime.now().isoformat(), "price": int(row.get("price",100))}],
                "last_tracked": datetime.now().isoformat(),
                "stats": {}
            }
            routes.append(sanitize_dict(new))
            created += 1
        st.success(f"{created} suivi(s) ajouté(s)")
        st.experimental_rerun()
