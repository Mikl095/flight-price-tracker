import json
import os
import matplotlib.pyplot as plt

DATA_FILE = "data.json"
EMAIL_CONFIG_FILE = "email_config.json"

def load_routes():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_routes(routes):
    with open(DATA_FILE, "w") as f:
        json.dump(routes, f, indent=4)

def load_email_config():
    if not os.path.exists(EMAIL_CONFIG_FILE):
        return {"email": ""}
    with open(EMAIL_CONFIG_FILE, "r") as f:
        return json.load(f)

def save_email_config(email):
    with open(EMAIL_CONFIG_FILE, "w") as f:
        json.dump({"email": email}, f, indent=4)

def plot_price_history(history):
    dates = [h["date"] for h in history]
    prices = [h["price"] for h in history]

    fig, ax = plt.subplots()
    ax.plot(dates, prices, marker="o")
    ax.set_xlabel("Date")
    ax.set_ylabel("Prix (€)")
    ax.set_title("Historique des prix")
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig
