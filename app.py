import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
from utils.db import load_db, save_db
from utils.forms import route_form_empty, route_form_edit
from utils.simulation import simulate_price
from utils.email_utils import send_email

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Flight Price Tracker",
    page_icon="✈️",
    layout="centered"
)

st.title("✈️ Flight Price Tracker")
st.write("Suivi automatique de prix – simulation locale (pas d’Amadeus)")

# ---------------------------------------------------------
# LOAD DATABASE
# ---------------------------------------------------------
db = load_db()

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None


# ---------------------------------------------------------
# TABLEAU RECAP
# ---------------------------------------------------------
st.header("📋 Suivis enregistrés")

if len(db["routes"]) == 0:
    st.info("Aucun suivi enregistré.")
else:

    # Récap avec dernières infos
    recap = []
    for r in db["routes"]:
        recap.append({
            "ID": r["id"],
            "Origine": r["origin"],
            "Destination": r["destination"],
            "Départ": r["departure"],
            "Durée (j)": r["stay_days"],
            "Notif": r["notify"],
            "Dernier prix": r.get("last_price", "—"),
            "Maj": r.get("last_check", "—"),
        })

    df = pd.DataFrame(recap)

    st.dataframe(df, use_container_width=True)

    # Export Excel
    if st.button("📥 Exporter en Excel"):
        df.to_excel("suivis.xlsx", index=False)
        with open("suivis.xlsx", "rb") as f:
            st.download_button(
                "Télécharger le fichier",
                f,
                "suivis.xlsx"
            )


# ---------------------------------------------------------
# ACTIONS SUR UN SUIVI EXISTANT
# ---------------------------------------------------------
st.subheader("🛠 Modifier ou supprimer un suivi")

if len(db["routes"]) > 0:
    selected_id = st.selectbox(
        "Sélectionner un suivi",
        [r["id"] for r in db["routes"]],
        format_func=lambda x: f"ID {x}"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✏️ Modifier ce suivi"):
            st.session_state.edit_id = selected_id
            st.rerun()

    with col2:
        if st.button("🗑 Supprimer"):
            db["routes"] = [r for r in db["routes"] if r["id"] != selected_id]
            save_db(db)
            st.success("Suivi supprimé.")
            st.rerun()


# ---------------------------------------------------------
# FORMULAIRE EDITION
# ---------------------------------------------------------
if st.session_state.edit_id is not None:
    st.divider()
    route = next(r for r in db["routes"] if r["id"] == st.session_state.edit_id)

    st.subheader(f"✏️ Modifier le suivi ID {route['id']}")

    form_values = route_form_edit(route)

    if st.button("💾 Enregistrer modifications"):
        route.update({
            "origin": form_values["origin"],
            "destination": form_values["destination"],
            "departure": form_values["departure"].isoformat(),
            "stay_days": form_values["stay_days"],
            "notify": form_values["notify"],
        })
        save_db(db)
        st.success("Modifié avec succès.")
        st.session_state.edit_id = None
        st.rerun()

    st.stop()


# ---------------------------------------------------------
# FORMULAIRE AJOUT
# ---------------------------------------------------------
st.divider()
st.header("➕ Ajouter un nouveau suivi")

form_values = route_form_empty()

if st.button("Ajouter ce suivi"):
    new_id = max([r["id"] for r in db["routes"]], default=0) + 1

    db["routes"].append({
        "id": new_id,
        "origin": form_values["origin"],
        "destination": form_values["destination"],
        "departure": form_values["departure"].isoformat(),
        "stay_days": form_values["stay_days"],
        "notify": form_values["notify"],
        "last_price": None,
        "last_check": None
    })

    save_db(db)
    st.success("Suivi ajouté !")
    st.rerun()


# ---------------------------------------------------------
# SIMULATION : METTRE A JOUR TOUS LES SUIVIS
# ---------------------------------------------------------
st.divider()
st.header("🔄 Simulation des prix")

if st.button("Mettre à jour les prix"):
    now = datetime.now().isoformat(timespec="seconds")

    for route in db["routes"]:
        price = simulate_price(route)
        route["last_price"] = price
        route["last_check"] = now

        if route["notify"] == "ON":
            send_email(
                to="zendugan95@gmail.com",
                subject=f"Update prix {route['origin']} → {route['destination']}",
                body=f"Le prix actuel simulé est de {price} €."
            )

    save_db(db)
    st.success("Mise à jour terminée.")
    st.rerun()
