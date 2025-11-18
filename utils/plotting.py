# utils/plotting.py
import matplotlib.pyplot as plt
from datetime import datetime
from typing import List, Dict, Any, Optional


def _parse_date(v) -> Optional[datetime]:
    """Parse a date value robustly: ISO string, or numeric timestamp."""
    if v is None:
        return None
    # already a datetime
    if isinstance(v, datetime):
        return v
    # numeric epoch
    try:
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(v)
    except Exception:
        pass
    # string - try isoformat then common fallbacks
    try:
        return datetime.fromisoformat(str(v))
    except Exception:
        # try common formats
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(str(v), fmt)
            except Exception:
                continue
    return None


def plot_price_history(history: List[Dict[str, Any]]):
    """
    history: list of {"date": iso-or-ts, "price": number}
    Returns a matplotlib.figure.Figure
    """
    if not history:
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.text(0.5, 0.5, "Aucun historique", ha="center", va="center", fontsize=12)
        ax.axis("off")
        return fig

    points = []
    for h in history:
        try:
            d = _parse_date(h.get("date"))
            p = h.get("price")
            if d is None or p is None:
                continue
            # ensure price is numeric
            p = float(p)
            points.append((d, p))
        except Exception:
            # ignore malformed entries
            continue

    if not points:
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.text(0.5, 0.5, "Aucun historique valide", ha="center", va="center", fontsize=12)
        ax.axis("off")
        return fig

    # sort by date
    points.sort(key=lambda x: x[0])
    dates, prices = zip(*points)

    fig, ax = plt.subplots(figsize=(7, 3))
    ax.plot(dates, prices, marker="o", linewidth=1)
    ax.set_title("Évolution du prix")
    ax.set_xlabel("Date")
    ax.set_ylabel("Prix (€)")
    ax.grid(True)
    fig.autofmt_xdate()
    plt.tight_layout()
    return fig
