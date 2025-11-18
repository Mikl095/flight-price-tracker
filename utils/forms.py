import streamlit as st
from datetime import date

# ---------------------------------------------------------
#  FORMULAIRE : CREATION D’UN NOUVEAU SUIVI
# ---------------------------------------------------------
def route_form_empty():
    st.subheader("🆕 Ajouter un suivi")

    origin = st.text_input("Origine (IATA)", value="PAR")
    origin = origin.upper() if origin else ""

    destination = st.text_input("Destination (IATA)", value="TYO")
    destination = destination.upper() if destination else ""

    departure = st.date_input("Date de départ", value=date.today())

    stay_days = st.number_input(
        "Durée sur place (jours)",
        min_value=1,
        max_value=60,
        value=7
    )

    notify = st.selectbox(
        "Notifications",
        ["ON", "OFF"],
        index=0
    )

    return {
        "origin": origin,
        "destination": destination,
        "departure": departure,
        "stay_days": stay_days,
        "notify": notify
    }


# ---------------------------------------------------------
#  FORMULAIRE : EDITION D’UN SUIVI EXISTANT
# ---------------------------------------------------------
def route_form_edit(row):
    st.subheader("✏️ Modifier le suivi")

    origin = st.text_input("Origine (IATA)", value=row["origin"])
    origin = origin.upper() if origin else ""

    destination = st.text_input("Destination (IATA)", value=row["destination"])
    destination = destination.upper() if destination else ""

    departure = st.date_input(
        "Date de départ",
        value=date.fromisoformat(row["departure"])
    )

    stay_days = st.number_input(
        "Durée sur place (jours)",
        min_value=1,
        max_value=60,
        value=int(row["stay_days"])
    )

    notify = st.selectbox(
        "Notifications",
        ["ON", "OFF"],
        index=0 if row["notify"] == "ON" else 1
    )

    return {
        "origin": origin,
        "destination": destination,
        "departure": departure,
        "stay_days": stay_days,
        "notify": notify
    }
