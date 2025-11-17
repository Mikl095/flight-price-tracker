import matplotlib.pyplot as plt
from datetime import datetime

def plot_price_history(history):
    dates = [datetime.fromisoformat(h["date"]) for h in history]
    prices = [h["price"] for h in history]

    fig, ax = plt.subplots()
    ax.plot(dates, prices, marker="o")
    ax.set_title("Évolution des prix")
    ax.set_xlabel("Date")
    ax.set_ylabel("Prix (€)")
    ax.grid(True)

    return fig
