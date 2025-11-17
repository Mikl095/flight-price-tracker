import pandas as pd
import matplotlib.pyplot as plt

def create_flight_table(routes):
    rows = []
    for r in routes:
        price = r["history"][-1]["price"] if r["history"] else None
        rows.append({
            "Origine": r["origin"],
            "Destination": r["destination"],
            "Départ": r["departure"],
            "Retour": r["return"],
            "Prix Actuel": price,
            "Seuil": r["target_price"],
            "Écart": price - r["target_price"] if price else None,
            "Notif": "ON" if r.get("notifications") else "OFF"
        })
    return pd.DataFrame(rows)
