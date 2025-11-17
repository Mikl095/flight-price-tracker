from utils.storage import load_routes, save_routes
from datetime import datetime
import random

routes = load_routes()

def simulate_price(route):
    now = datetime.now()
    price = random.randint(200, 900)
    route["history"].append({
        "date": now.isoformat(),
        "price": price
    })
    route["last_tracked"] = now.isoformat()

for r in routes:
    simulate_price(r)

save_routes(routes)
