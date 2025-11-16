import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ---------------- CONFIG ----------------
API_KEY = st.secrets["RAPIDAPI_KEY"]
HOST = "flights-scraper-real-time.p.rapidapi.com"

st.set_page_config(page_title="Flight Price Tracker - Flights Scraper", layout="wide")
st.title("📉 Tracker de prix de vols - Flights Scraper Real-Time")

# ---------------- INPUTS UTILISATEUR ----------------
origin_input = st.text_input("Départ (ville ou IATA)", "Paris")
destinations_input = st.text_input("Destinations (villes ou IATA séparés par des virgules)", "Tokyo,Osaka")
date_from = st.text_input("Date départ (YYYY-MM-DD)", datetime.now().strftime("%Y-%m-%d"))
date_to = st.text_input("Date retour (YYYY-MM-DD)", (datetime.now().replace(year=datetime.now().year+1)).strftime("%Y-%m-%d"))
adults = st.number_input("Nombre de passagers", min_value=1, value=1)

destinations = [d.strip() for d in destinations_input.split(",") if d.strip()]

headers = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": HOST
}

# ---------------- FONCTION POUR RECUPERER SKYID ----------------
def get_skyid(query):
    url = f"https://{HOST}/flights/auto-complete"
    params = {"query": query}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=30)
        data = r.json()
        if data and isinstance(data, list) and "id" in data[0]:
            return data[0]["id"]  # prend le premier résultat
        else:
            return None
    except Exception as e:
        st.error(f"Erreur auto-complete pour {query}: {e}")
        return None

# ---------------- BOUTON ----------------
if st.button("Chercher vols"):

    # Récupérer originSkyId
    originSkyId = get_skyid(origin_input)
    if not originSkyId:
        st.error(f"Impossible de trouver originSkyId pour {origin_input}")
    else:
        for dest in destinations:
            st.header(f"🔹 {origin_input} → {dest}")
            destinationSkyId = get_skyid(dest)
            if not destinationSkyId:
                st.warning(f"Impossible de trouver destinationSkyId pour {dest}")
                continue

            # ---------------- SEARCH RETURN ----------------
            url = f"https://{HOST}/flights/search-return"
            params = {
                "originSkyId": originSkyId,
                "destinationSkyId": destinationSkyId,
                "departureDate": date_from,
                "returnDate": date_to,
                "adults": adults,
                "currency": "EUR"
            }

            try:
                r = requests.get(url, headers=headers, params=params, timeout=30)
                data = r.json()

                st.subheader("Réponse brute de l'API")
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
