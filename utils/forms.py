import streamlit as st

def route_form_empty():
    origin = st.text_input("Origine (IATA)", value="PAR")
    if origin:
        origin = origin.upper()
    else:
        origin = ""

    destination = st.text_input("Destination (IATA)", value="TYO")
    if destination:
        destination = destination.upper()
    else:
        destination = ""

    departure = st.date_input("Date de départ")
    stay_days = st.number_input("Durée sur place (jours)", min_value=1, value=7)

    notify = st.selectbox("Notifications", ["ON", "OFF"], index=0)

    return {
        "origin": origin,
        "destination": destination,
        "departure": departure,
        "stay_days": stay_days,
        "notify": notify,
    }
