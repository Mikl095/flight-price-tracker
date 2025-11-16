import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_KEY = st.secrets["RAPIDAPI_KEY"]
HOST = "flights-scraper-real-time.p.rapidapi.com"

st.title("Tracker vols - Flights Scraper Real-Time")

# Inputs utilisateur
origin = st.text_input("Départ (IATA)", "PAR")
destinations_input = st.text_input("Destinations (IATA séparés par des virgules)", "NRT,HND,KIX")
date_from = st.text_input("Date départ (YYYY-MM-DD)", datetime.now().strftime("%Y-%m-%d"))
date_to = st.text_input("Date retour (YYYY-MM-DD)", (datetime.now().replace(year=datetime.now().year+1)).strftime("%Y-%m-%d"))

destinations = [d.strip().upper() for d in destinations_input.split(",") if d.strip()]

if st.button("Chercher vols"):

    for dest in destinations:
        url = f"https://{HOST}/search"  # Vérifie le nom exact sur RapidAPI
        params = {
            "origin": origin,
            "destination": dest,
            "date_from": date_from,
            "date_to": date_to,
            "adults": 1,
            "currency": "EUR"
        }
        headers = {
            "X-RapidAPI-Key": API_KEY,
            "X-RapidAPI-Host": HOST
        }

        try:
            r = requests.get(url, headers=headers, params=params, timeout=30)
            data = r.json()

            if "flights" in data and data["flights"]:
                df = pd.DataFrame(data["flights"])
                df["departure"] = pd.to_datetime(df["departure"], errors="coerce")
                df["return"] = pd.to_datetime(df.get("return", None), errors="coerce")
                st.subheader(f"{origin} → {dest}")
                st.line_chart(df.set_index("departure")["price"])
                st.write(df)
            else:
                st.warning(f"Aucun vol trouvé pour {dest}")

        except Exception as e:
            st.error(f"Erreur pour {dest} : {e}")
