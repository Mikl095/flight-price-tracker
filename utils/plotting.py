# utils/plotting.py
import matplotlib.pyplot as plt
from datetime import datetime

def plot_price_history(history):
    """
    Génère un graphique des prix dans le temps pour un vol donné.
    
    history : list de dicts {"date": iso_str, "price": float/int}
    """
    if not history:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Aucun historique", ha='center', va='center')
        ax.set_axis_off()
        return fig

    # Trier l'historique par date
    sorted_hist = sorted(history, key=lambda x: x.get("date") or "")
    dates = []
    prices = []

    for h in sorted_hist:
        d = h.get("date")
        p = h.get("price")
        if d and p is not None:
            try:
                dt = datetime.fromisoformat(d)
                dates.append(dt)
                prices.append(p)
            except Exception:
                continue

    fig, ax = plt.subplots(figsize=(6,3))
    ax.plot(dates, prices, marker='o', linestyle='-', color='tab:blue')
    ax.set_xlabel("Date")
    ax.set_ylabel("Prix (€)")
    ax.set_title("Historique des prix")
    ax.grid(True)
    fig.tight_layout()
    return fig
