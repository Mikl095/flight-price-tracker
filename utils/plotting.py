import matplotlib.pyplot as plt
from datetime import datetime

def plot_price_history(history):
    dates = [datetime.fromisoformat(entry['date']) for entry in history]
    prices = [entry['price'] for entry in history]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(dates, prices, marker='o')
    ax.set_xlabel("Date")
    ax.set_ylabel("Prix (€)")
    ax.set_title("Historique des prix")
    ax.grid(True)
    fig.autofmt_xdate()
    return fig
    
