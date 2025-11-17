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

routes = load_routes()

# email global enregistré dans streamlit
try:
    with open("email_config.json", "r") as f:
        config = json.load(f)
        EMAIL = config.get("email", None)
except:
    EMAIL = None

for r in routes:
    price = random.randint(300, 900)
    r["history"].append({"date": str(datetime.now()), "price": price})
    r["last_tracked"] = str(datetime.now())

    if r["notifications"] and EMAIL and price <= r["target_price"]:
        send_email(
            EMAIL,
            f"[ALERTE] {r['origin']} → {r['destination']} : {price}€",
            f"Prix actuel : {price}€\nObjectif : {r['target_price']}€"
        )

save_routes(routes)
