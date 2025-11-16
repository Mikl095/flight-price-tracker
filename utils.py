import json
import os
import matplotlib.pyplot as plt
import pandas as pd

DATA_DIR = "data"
ROUTE_FILE = os.path.join(DATA_DIR, "tracked_routes.json")

def ensure_data_file():
    """
    Assure que le dossier data/ et le fichier tracked_routes.json existent.
    Compatible avec Streamlit Cloud.
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(ROUTE_FILE):
        with open(ROUTE_FILE, "w") as f:
            json.dump([], f)

def load_routes():
    ensure_data_file()
    with open(ROUTE_FILE, "r") as f:
        return json.load(f)

def save_routes(routes):
    ensure_data_file()
    with open(ROUTE_FILE, "w") as f:
        json.dump(routes, f, indent=4)

def plot_price_history(history):
    df = pd.DataFrame(history)
    plt.figure(figsize=(8,4))
    plt.plot(df["date"], df["price"], marker="o")
    plt.xlabel("Date")
    plt.ylabel("Prix (€)")
    plt.title("Évolution du prix du vol")
    plt.grid(True)
    return plt
