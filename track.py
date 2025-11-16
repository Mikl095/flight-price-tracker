import json
import random
from datetime import datetime
from email_utils import send_email

DATA_FILE = "data.json"

def load_routes():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_routes(routes):
    with open(DATA_FILE, "w") as f:
        json.dump(routes, f, indent=4)

def simulate_tracking(route):
    price = random.randint(200, 800)
    entry = {
        "date": str(datetime.now()),
        "price": price
    }
    route["history"].append(entry)
    route["last_tracked"] = str(datetime.now())
    return price

routes = load_routes()

for route in routes:
    price = simulate_tracking(route)

    # Notification
    if price <= route["target_price"]:
        send_email(
            subject=f"🔥 Prix bas : {route['origin']} → {route['destination']}",
            text=(
                f"Prix actuel : {price}€\n"
                f"Seuil : {route['target_price']}€\n"
                f"Départ : {route['departure']}"
            )
        )

save_routes(routes)
