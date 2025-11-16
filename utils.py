import json
import matplotlib.pyplot as plt
import pandas as pd

ROUTE_FILE = "data/tracked_routes.json"

def load_routes():
    try:
        with open(ROUTE_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_routes(routes):
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
  
