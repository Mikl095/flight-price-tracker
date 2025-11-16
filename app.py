import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ----------------- CONFIG -----------------
API_KEY = st.secrets["RAPIDAPI_KEY"]
HOST = "flights-scraper-real-time.p.rapidapi.com"

st.set_page_config(page_title="Flight Price Tracker - Flights Scraper", layout="wide")
st.title("📉 Tracker de prix de vols - Flights Scraper Real-Time")

# ----------------- INPUT UTILISATEUR -----------------
origin = st.text_input("Départ (IATA)", "PAR")
destinations_input = st.text_input("Destinations (IATA séparés par des virgules)", "NRT,HND,KIX")
date_from = st.text_input("Date départ (YYYY-MM-DD)", datetime.now().strftime("%Y-%m-%d"))
date_to = st.text_input("Date retour (YYYY-MM-DD)", (datetime.now().replace(year=datetime.now().year+1)).strftime("%Y-%m-%d"))
adults = st.number_input("Nombre de passagers", min_value=1, value=1)

# Nettoyage destinations
destinations = [d.strip().upper() for d in destinations_input.split(",") if d.strip()]

# ----------------- BOUTON -----------------
if st.button("Chercher vols"):

    for dest in destinations:
        st.header(f"🔹 {origin} → {dest}")

        # ----------------- PARAMETRES -----------------
        url = f"https://{HOST}/flights/search-return"
        params = {
            "origin": origin,
            "destination": dest,
            "departureDate": date_from,
            "returnDate": date_to,
            "adults": adults,
            "currency": "EUR"
        }
        headers = {
            "X-RapidAPI-Key": API_KEY,
            "X-RapidAPI-Host": HOST
        }

        # ----------------- REQUETE -----------------
        try:
            r = requests.get(url, headers=headers, params=params, timeout=30)
            data = r.json()

            st.subheader("Réponse brute de l'API")
            st.json(data)

            # ----------------- VERIFICATION -----------------
            if "flights" in data and len(data["flights"]) > 0:
                flights = data["flights"]
                df = pd.DataFrame(flights)
                
                # Conversion des dates en datetime si existant
                if "departure" in df.columns:
                    df["departure"] = pd.to_datetime(df["departure"], errors="coerce")
                if "return" in df.columns:
                    df["return"] = pd.to_datetime(df["return"], errors="coerce")
                
                st.subheader("Graphique des prix")
                if "departure" in df.columns and "price" in df.columns:
                    st.line_chart(df.set_index("departure")["price"])
                st.write(df)

            else:
                st.warning("⚠ Aucun vol trouvé pour cette destination ou problème de paramètres.")

        except Exception as e:
            st.error(f"Erreur pour {dest} : {e}")
