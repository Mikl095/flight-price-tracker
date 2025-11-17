import matplotlib.pyplot as plt
from datetime import datetime

def plot_price_history(history):
    if not history:
        fig, ax = plt.subplots(figsize=(6,3))
        ax.text(0.5, 0.5, "Aucun historique", ha="center")
        ax.axis("off")
        return fig

    dates = []
    prices = []
    for h in history:
        try:
            dates.append(datetime.fromisoformat(h["date"]))
            prices.append(h["price"])
        except Exception:
            continue

    fig, ax = plt.subplots(figsize=(7,3))
    ax.plot(dates, prices, marker="o", linewidth=1)
    ax.set_title("Évolution du prix")
    ax.set_xlabel("Date")
    ax.set_ylabel("Prix (€)")
    ax.grid(True)
    fig.autofmt_xdate()
    plt.tight_layout()
    return fig
