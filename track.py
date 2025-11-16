from utils import load_routes, save_routes
from datetime import datetime
import random

routes = load_routes()

def simulate_auto_tracking(route):
    now = datetime.now()
    route.setdefault("history", [])

    last = datetime.fromisoformat(route["last_tracked"]) if route.get("last_tracked") else None
    interval = 24 / max(route.get("tracking_per_day", 1), 1)

    updates_needed = 1
    if last:
        hours_passed = (now - last).total_seconds() / 3600
        updates_needed = int(hours_passed // interval)

    for _ in range(updates_needed):
        price = random.randint(200, 900)

        route["history"].append({
            "date": str(now),
            "price": price
        })
        route["last_tracked"] = str(now)

        if route.get("notifications_enabled") and price <= route["target_price"]:
            print(f"🔥 DEAL {route['origin']} → {route['destination']}: {price} € (sous {route['target_price']}€)")


for r in routes:
    simulate_auto_tracking(r)

save_routes(routes)

print("Tracking OK à", datetime.now())
