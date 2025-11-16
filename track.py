from utils import load_routes, save_routes
from datetime import datetime
import random

def simulate_auto_tracking(route):
    now = datetime.now()

    # Assure que les clés existent
    history = route.setdefault("history", [])
    route.setdefault("tracking_per_day", 1)
    
    last_tracked = route.get("last_tracked")
    interval_hours = 24 / max(route["tracking_per_day"], 1)

    if last_tracked:
        last = datetime.fromisoformat(last_tracked)
        hours_passed = (now - last).total_seconds() / 3600
        updates_needed = int(hours_passed // interval_hours)
    else:
        updates_needed = 1

    for _ in range(updates_needed):
        price = random.randint(200, 800)
        history.append({
            "date": str(now),
            "price": price
        })
        route["last_tracked"] = str(now)

if __name__ == "__main__":
    routes = load_routes()

    for route in routes:
        simulate_auto_tracking(route)

    save_routes(routes)
    print("Tracking automatique effectué ✔️")
