import pandas as pd

def create_flight_table(routes):
    rows = []
    for r in routes:
        last_price = r.get("history")[-1]["price"] if r.get("history") else None
        gap = None
        if last_price is not None and r.get("target_price") is not None:
            gap = round(last_price - r["target_price"], 2)
        rows.append({
            "id": r.get("id"),
            "Origin": r.get("origin"),
            "Destination": r.get("destination"),
            "Departure": r.get("departure"),
            "Return": r.get("return"),
            "Last price (€)": last_price,
            "Target (€)": r.get("target_price"),
            "Gap (€)": gap,
            "Range depart (±j)": r.get("departure_range_days", 0),
            "Range retour (±j)": r.get("return_range_days", 0),
            "Min bags": r.get("min_bags", 0),
            "Max stops": r.get("max_stops", "any"),
            "Notif": "ON" if r.get("notifications") else "OFF",
            "Email": r.get("email", "")
        })
    return pd.DataFrame(rows)
