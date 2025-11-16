import json
import os
import matplotlib.pyplot as plt
from datetime import datetime

DATA_FILE = "Data/tracked_routes.json"


# ------------------------------------------
# Assurer que le fichier JSON existe
# ------------------------------------------
def ensure_data_file():
    os.makedirs("Data", exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)


# ------------------------------------------
# Charger les routes
# ------------------------------------------
def load_routes():
    ensure_data_file()
    with open(DATA_FILE, "r") as f:
        return json.load(f)


# ------------------------------------------
# Sauvegarder les routes
# ------------------------------------------
def save_routes(routes):
    with open(DATA_FILE, "w") as f:
        json.dump(routes, f, indent=4)


# ------------------------------------------
# Graphe historique
# ------------------------------------------
def plot_price_history(history):
    dates = [datetime.fromisoformat(item["date"]) for item in history]
    prices = [item["price"] for item in history]

    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(dates, prices, marker="o")
    ax.set_title("Évolution du prix")
    ax.set_xlabel("Date")
    ax.set_ylabel("Prix (€)")
    fig.autofmt_xdate()

    return fig
