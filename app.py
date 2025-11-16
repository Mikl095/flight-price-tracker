import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ---------------- CONFIG ----------------
API_KEY = st.secrets["RAPIDAPI_KEY"]
HOST = "flights-scraper-real-time.p.rapidapi.com"

st.set_page_config(page_title="Flight Price Tracker - Aller Simple", layout="wide")
st.title("📉 Tracker gratuit de prix de vols - Aller Simple")

# ---------------- INPUT UTILISATEUR ----------------
origin_input = st.text_input("Départ (ville ou IATA)", "Paris")
destinations_input = st.text_input(
    "Destinations (villes ou IATA séparés par des virgules)", 
    "Tokyo,Osaka,Guadeloupe"
)
date_from = st.text_input("Date départ (YYYY-MM-DD)", datetime.now().strftime("%Y-%m-%d"))
adults = st.number_input("Nombre de passagers", min_value=1, value=1)

destinations = [d.strip() for d in destinations_input.split(",") if d.strip()]

# ---------------- DICTIONNAIRE VILLE / IATA -> SkyId ----------------
city_to_skyid = {
    # Paris
    "Paris": ["sky:CDG", "sky:ORY"],
    
    # Japon
    "Tokyo": ["sky:NRT", "sky:HND"],
    "Osaka": ["sky:KIX", "sky:ITM"],
    "Sapporo": ["sky:CTS"],
    "Fukuoka": ["sky:FUK"],
    "Nagoya": ["sky:NGO"],
    
    # Guadeloupe
    "Guadeloupe": ["sky:PTP"]
}

# ---------------- FONCTION POUR FAIRE UNE REQUETE ----------------
def search_flights(originSkyId, destinationSkyId, depart):
    url = f"https://{HOST}/flights/search-return"
    headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": HOST}
    params = {
        "originSkyId": originSkyId,
        "destinationSkyId": destinationSkyId,
        "departureDate": depart,
        "adults": adults,
        "currency": "EUR"
    }
    r = requests.get(url, headers=headers, params=params, timeout=30)
    return r.json()

# ---------------- BOUTON ----------------
if st.button("Chercher vols"):

    origin_ids = city_to_skyid.get(origin_input)
    if not origin_ids:
        st.error(f"Impossible de trouver SkyId pour {origin_input}")
    else:
        for dest in destinations:
            st.header(f"🔹 {origin_input} → {dest}")
            destination_ids = city_to_skyid.get(dest)
            if not destination_ids:
                st.warning(f"Impossible de trouver SkyId pour {dest}")
                continue

            all_results = []

            # Boucle sur toutes les combinaisons origin/destination possibles
            for o_id in origin_ids:
                for d_id in destination_ids:
                    try:
                        data = search_flights(o_id, d_id, date_from)
                        if "flights" in data and len(data["flights"]) > 0:
                            df = pd.DataFrame(data["flights"])
                            if "departure" in df.columns:
                                df["departure"] = pd.to_datetime(df["departure"], errors="coerce")
                            all_results.append(df)
                    except Exception as e:
                        st.error(f"Erreur pour {o_id} → {d_id}: {e}")

            if all_results:
                result_df = pd.concat(all_results, ignore_index=True)
                st.subheader("Graphique des prix")
                if "departure" in result_df.columns and "price" in result_df.columns:
                    st.line_chart(result_df.set_index("departure")["price"])
                st.write(result_df)
            else:
                st.warning("⚠ Aucun vol trouvé pour cette destination.")
