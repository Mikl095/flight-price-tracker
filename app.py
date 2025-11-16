import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ---------- CONFIG ----------
API_KEY = st.secrets["RAPIDAPI_KEY"]
HOST = "flights-scraper-real-time.p.rapidapi.com"

st.set_page_config(page_title="Flight Price Tracker - Debug", layout="wide")
st.title("📉 Tracker vols - Flights Scraper Real-Time (Diagnostic)")

# ----- Inputs utilisateur -----
origin = st.text_input("Départ (IATA)", "PAR")
destinations_input = st.text_input("Destinations (IATA séparés par des virgules)", "NRT,HND,KIX")
date_from = st.text_input("Date départ (YYYY-MM-DD)", datetime.now().strftime("%Y-%m-%d"))
date_to = st.text_input("Date retour (YYYY-MM-DD)", (datetime.now().replace(year=datetime.now().year+1)).strftime("%Y-%m-%d"))

destinations = [d.strip().upper() for d in destinations_input.split(",") if d.strip()]

if st.button("Chercher vols"):

    for dest in destinations:
        st.header(f"🔹 {origin} → {dest}")

        # --- Test Aller simple ---
        st.subheader("✈️ Test Aller Simple")
        url_simple = f"https://{HOST}/search"  # Vérifie le endpoint exact
        params_simple = {
            "origin": origin,
            "destination": dest,
            "date_from": date_from,
            "adults": 1,
            "currency": "EUR"
        }
        headers = {
            "X-RapidAPI-Key": API_KEY,
            "X-RapidAPI-Host": HOST
        }

        try:
            r = requests.get(url_simple, headers=headers, params=params_simple, timeout=30)
            data_simple = r.json()
            st.subheader("Réponse brute (Aller simple)")
            st.json(data_simple)

            if "flights" in data_simple and data_simple["flights"]:
                df_simple = pd.DataFrame(data_simple["flights"])
                df_simple["departure"] = pd.to_datetime(df_simple["departure"], errors="coerce")
                st.line_chart(df_simple.set_index("departure")["price"])
                st.write(df_simple)
            else:
                st.warning("Aucun vol aller simple trouvé.")

        except Exception as e:
            st.error(f"Erreur Aller Simple : {e}")

        # --- Test Aller-Retour (si supporté) ---
        st.subheader("🔄 Test Aller-Retour (round-trip)")
        url_round = f"https://{HOST}/round-trip"  # Vérifie que ce endpoint existe
        params_round = {
            "origin": origin,
            "destination": dest,
            "departureDate": date_from,
            "returnDate": date_to,
            "adults": 1,
            "currency": "EUR"
        }

        try:
            r = requests.get(url_round, headers=headers, params=params_round, timeout=30)
            data_round = r.json()
            st.subheader("Réponse brute (Aller-Retour)")
            st.json(data_round)

            if "flights" in data_round and data_round["flights"]:
                df_round = pd.DataFrame(data_round["flights"])
                df_round["departure"] = pd.to_datetime(df_round["departure"], errors="coerce")
                df_round["return"] = pd.to_datetime(df_round.get("return", None), errors="coerce")
                st.line_chart(df_round.set_index("departure")["price"])
                st.write(df_round)
            else:
                st.warning("Aucun vol round-trip trouvé ou endpoint non supporté.")

        except Exception as e:
            st.error(f"Erreur Round-Trip : {e}")
