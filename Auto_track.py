import json
from datetime import datetime
import random
import os

ROUTE_FILE = "data/tracked_routes.json"

# Vérifier si le fichier existe
if not os.path.exists(ROUTE_FILE):
    print(f"{ROUTE_FILE} introuvable !")
    exit()

# Charger les routes
with open(ROUTE_FILE, "r") as f:
    routes = json.load(f)

# Fonction de tracking simulé
def simulate_auto_tracking(route):
    now = datetime.now()
    last_tracked_str = route.get("last_tracked")
    route.setdefault("history", [])
    last = datetime.fromisoformat(last_tracked_str) if last_tracked_str else None
    interval = 24 / max(route.get("tracking_per_day", 1), 1)  # heures

    updates_needed = 0
    if last:
        hours_passed = (now - last).total_seconds() / 3600
        updates_needed = int(hours_passed // interval)
    else:
        updates_needed = 1

    for _ in range(updates_needed):
        price = random.randint(200, 800)
        route["history"].append({"date": str(now), "price": price})
        route["last_tracked"] = str(now)

# Mettre à jour tous les vols
for route in routes:
    simulate_auto_tracking(route)

# Sauvegarder
with open(ROUTE_FILE, "w") as f:
    json.dump(routes, f, indent=4)

print("✅ Routes mises à jour avec succès !")
