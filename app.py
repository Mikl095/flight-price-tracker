import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

# ---------- CONFIG ----------
API_KEY = st.secrets["RAPIDAPI_KEY"]  # clé RapidAPI

st.set_page_config(page_title="Flight Price Tracker", layout="wide")
st.title("📉 Tracker de prix de vols Kiwi.com via RapidAPI")

# Inputs utilisateur
origin = st.text_input("Aéroport de départ (IATA)", "CDG")
destinations_input = st.text_input("Destinations (IATA séparés par des virgules)", "NRT,HND,KIX")
date_from = st.text_input("Date départ (YYYY-MM-DD)", datetime.now().strftime("%Y-%m-%d"))
date_to = st.text_input("Date retour (YYYY-MM-DD)", (datetime.now().replace(year=datetime.now().year+1)).strftime("%Y-%m-%d"))

destinations = [d.strip().upper() for d in destinations_input.split(",") if d.strip()]

if st.button("Chercher les prix"):
    for dest in destinations:
        url = "https://kiwi-com.p.rapidapi.com/v2/search"
        
from datetime import datetime

# Exemple pour convertir YYYY-MM-DD -> DD/MM/YYYY
try:
    date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
    date_from_api = date_from_obj.strftime("%d/%m/%Y")
    date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
    date_to_api = date_to_obj.strftime("%d/%m/%Y")
except Exception as e:
    st.error(f"Erreur format date : {e}")
    date_from_api = date_from
    date_to_api = date_to

params = {
    "fly_from": origin,
    "fly_to": dest,
    "date_from": date_from_api,
    "date_to": date_to_api,
    "curr": "EUR",
    "limit": 10
}


st.write("Paramètres envoyés à l'API :", params)

r = requests.get(url, headers=headers, params=params, timeout=30)

        
        headers = {
            "X-RapidAPI-Key": API_KEY,
            "X-RapidAPI-Host": "kiwi-com.p.rapidapi.com"
        }

        try:
            r = requests.get(url, headers=headers, params=params, timeout=30)
            data = r.json()
            st.write("Réponse brute de l'API :", data)
            if "data" in data and len(data["data"])>0:
                prices = [{"price": f["price"], "departure": f["local_departure"]} for f in data["data"]]
                df = pd.DataFrame(prices)
                df["departure"] = pd.to_datetime(df["departure"])
                st.subheader(f"{origin} → {dest}")
                st.line_chart(df.set_index("departure")["price"])
                st.write(df)
            else:
                st.warning(f"Aucun vol trouvé pour {dest}")
        except Exception as e:
            st.error(f"Erreur pour {dest} : {e}")
