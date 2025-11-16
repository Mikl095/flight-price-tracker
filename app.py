import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ---------- CONFIG ----------
API_KEY = st.secrets["RAPIDAPI_KEY"]
HOST = "flights-sky.p.rapidapi.com"

st.set_page_config(page_title="Flight Price Tracker", layout="wide")
st.title("📉 Tracker de prix de vols - Round-Trip")

# ----- Inputs utilisateur -----
origin = st.text_input("Aéroport de départ (IATA)", "PAR")
destinations_input = st.text_input("Destinations (IATA séparés par des virgules)", "NRT,HND,KIX")
departure_date = st.text_input("Date départ (YYYY-MM-DD)", datetime.now().strftime("%Y-%m-%d"))
return_date = st.text_input("Date retour (YYYY-MM-DD)", (datetime.now().replace(year=datetime.now().year+1)).strftime("%Y-%m-%d"))

# Nettoyage des destinations
destinations = [d.strip().upper() for d in destinations_input.split(",") if d.strip()]

if st.button("Chercher les prix"):

    for dest in destinations:
        url = f"https://{HOST}/round-trip"
        params = {
            "origin": origin,
            "destination": dest,
            "departureDate": departure_date,
            "returnDate": return_date,
            "adults": 1,
            "currency": "EUR"
        }
        headers = {
            "X-RapidAPI-Key": API_KEY,
            "X-RapidAPI-Host": HOST
        }

        st.write(f"🔵 Paramètres envoyés pour {dest} :", params)

        try:
            r = requests.get(url, headers=headers, params=params, timeout=30)
            data = r.json()

            # Vérification du résultat
            if "flights" in data and data["flights"]:
                flights = data["flights"]
                df = pd.DataFrame(flights)
                df["departure"] = pd.to_datetime(df["departure"], errors="coerce")
                df["return"] = pd.to_datetime(df["return"], errors="coerce")

                st.subheader(f"{origin} → {dest} → {origin} (Round-trip)")
                st.line_chart(df.set_index("departure")["price"])
                st.write(df)

            else:
                st.warning(f"⚠ Aucun vol round-trip trouvé pour {dest}")

        except Exception as e:
            st.error(f"Erreur pour {dest} : {e}")
