import json
from datetime import datetime
import random
import os

# Chemin du fichier JSON
ROUTE_FILE = "data/tracked_routes.json"

# Crée le dossier si besoin
os.makedirs(os.path.dirname(ROUTE_FILE), exist_ok=True)

# Crée le fichier si inexistant
if not os.path.exists(ROUTE_FILE):
    with open(ROUTE_FILE, "w") as f:
        json.dump([], f)

# Charge les routes
with open(ROUTE_FILE, "r") as f:
    try:
        routes = json.load(f)
    except json.JSONDecodeError:
        routes = []

def simulate_auto_tracking(route):
    now = datetime.now()
    last_tracked_str = route.get("last_tracked")
    route.setdefault("history", [])
    interval = 24 / max(route.get("tracking_per_day", 1), 1)  # heures

    updates_needed = 0
    if last_tracked_str:
        try:
            last = datetime.fromisoformat(last_tracked_str)
            hours_passed = (now - last).total_seconds() / 3600
            updates_needed = int(hours_passed // interval)
        except Exception:
            updates_needed = 1
    else:
        updates_needed = 1

    for _ in range(updates_needed):
        price = random.randint(200, 800)
        route["history"].append({"date": str(now), "price": price})
        route["last_tracked"] = str(now)

# Met à jour toutes les routes
for route in routes:
    simulate_auto_tracking(route)

# Sauvegarde le fichier
with open(ROUTE_FILE, "w") as f:
    json.dump(routes, f, indent=4)

print("✅ Routes mises à jour avec succès !")
                   
