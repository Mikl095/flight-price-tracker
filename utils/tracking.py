import random
from datetime import datetime
from utils.storage import load_routes, save_routes
from utils.scheduler import tracking_needed
from utils.emailer import send_email_alert

# -------------------------------------------------------------------
# Simulation locale (utilisée par le bouton "Mettre à jour maintenant")
# -------------------------------------------------------------------
def simulate_price_tracking(route):
    price = random.randint(200, 800)
    now = datetime.now().isoformat()

    route["history"].append({"date": now, "price": price})
    route["last_tracked"] = now

# -------------------------------------------------------------------
# Tracking utilisé par GitHub Actions
# -------------------------------------------------------------------
def auto_track_all_routes():
    routes = load_routes()
    updated = False

    for route in routes:
        if tracking_needed(route):
            price = random.randint(200, 800)  # ← Remplace ici par appel API

            now = datetime.now().isoformat()
            route["history"].append({"date": now, "price": price})
            route["last_tracked"] = now

            # Notification mail
            if route["notify"] and price <= route["target_price"]:
                send_email_alert(route, price)

            updated = True

    if updated:
        save_routes(routes)

if __name__ == "__main__":
    auto_track_all_routes()
          
