import pandas as pd

def create_flight_table(routes):
    rows = []
    for r in routes:
        last_price = r["history"][-1]["price"] if r.get("history") else None
        gap = None
        if last_price is not None and r.get("target_price") is not None:
            gap = round(last_price - r["target_price"], 2)
        rows.append({
            "Origin": r.get("origin"),
            "Destination": r.get("destination"),
            "Departure": r.get("departure"),
            "Return": r.get("return"),
            "Last price (€)": last_price,
            "Target (€)": r.get("target_price"),
            "Gap (€)": gap,
            "Stops allowed": r.get("max_stops", "any"),
            "Min baggage": r.get("min_bags", 0),
            "Notifications": "ON" if r.get("notifications") else "OFF"
        })
    return pd.DataFrame(rows)
