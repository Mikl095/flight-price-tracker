import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ---------------- CONFIG ----------------
API_KEY = st.secrets["RAPIDAPI_KEY"]
HOST = "flights-scraper-real-time.p.rapidapi.com"

st.set_page_config(page_title="Flight Price Tracker - Gratuit", layout="wide")
st.title("📉 Tracker gratuit de prix de vols - Flights Scraper Real-Time")

# ---------------- INPUT UTILISATEUR ----------------
origin_input = st.text_input("Départ (ville ou IATA)", "Paris")
destinations_input = st.text_input("Destinations (villes ou IATA séparés par des virgules)", "Tokyo,Osaka")
date_from = st.text_input("Date départ (YYYY-MM-DD)", datetime.now().strftime("%Y-%m-%d"))
date_to = st.text_input("Date retour (YYYY-MM-DD)", (datetime.now().replace(year=datetime.now().year+1)).strftime("%Y-%m-%d"))
adults = st.number_input("Nombre de passagers", min_value=1, value=1)

destinations = [d.strip() for d in destinations_input.split(",") if d.strip()]

# ---------------- DICTIONNAIRE VILLE -> SkyId ----------------
city_to_skyid = {
    "Paris": "sky:CDG",
    "Tokyo": "sky:NRT",
    "Osaka": "sky:KIX",
    "New York": "sky:JFK",
    "London": "sky:LHR"
    # Ajouter d'autres villes si nécessaire
}

# ---------------- FONCTION POUR FAIRE UNE REQUETE ----------------
def search_flights(originSkyId, destinationSkyId, depart, ret):
    url = f"https://{HOST}/flights/search-return"
    headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}
    params = {
        "originSkyId": originSkyId,
        "destinationSkyId": destinationSkyId,
        "departureDate": depart,
        "returnDate": ret,
        "adults": adults,
        "currency": "EUR"
    }
    r = requests.get(url, headers=headers, params=params, timeout=30)
    data = r.json()
    return data

# ---------------- BOUTON ----------------
if st.button("Chercher vols"):

    originSkyId = city_to_skyid.get(origin_input)
    if not originSkyId:
        st.error(f"Impossible de trouver SkyId pour {origin_input}")
    else:
        for dest in destinations:
            st.header(f"🔹 {origin_input} → {dest}")
            destinationSkyId = city_to_skyid.get(dest)
            if not destinationSkyId:
                st.warning(f"Impossible de trouver SkyId pour {dest}")
                continue

            # ---------------- SEARCH RETURN ----------------
            try:
                data = search_flights(originSkyId, destinationSkyId, date_from, date_to)

                st.subheader("Réponse brute API")
                st.json(data)

                if "flights" in data and len(data["flights"]) > 0:
                    df = pd.DataFrame(data["flights"])
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
                st.error(f"Erreur pour {dest}: {e}")
