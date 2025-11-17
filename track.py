import random
from datetime import datetime
from utils.storage import load_routes, save_routes, load_email_config
from sendgrid_client import sendgrid_send

routes = load_routes()
email_cfg = load_email_config()
TO_EMAIL = email_cfg.get("email")
SEND_NOTIF_GLOBAL = email_cfg.get("enabled", False)

def simulate_price_update(route):
    # Simule prix — quand Amadeus sera connecté, remplace ici
    price = random.randint(200, 900)
    route.setdefault("history", [])
    route["history"].append({"date": datetime.now().isoformat(), "price": price})
    route["last_tracked"] = datetime.now().isoformat()
    return price

changed = False
for r in routes:
    price = simulate_price_update(r)
    changed = True
    # notification logic
    if r.get("notifications") and SEND_NOTIF_GLOBAL and TO_EMAIL:
        target = r.get("target_price")
        if target is not None and price <= target:
            subject = f"[ALERTE] {r['origin']} → {r['destination']} à {price}€"
            body = f"Prix actuel: {price}€\nSeuil: {target}€\nDates: {r.get('departure')} → {r.get('return')}"
            sendgrid_send(TO_EMAIL, subject, body)

if changed:
    save_routes(routes)
    print("Tracking done, data.json updated")
else:
    print("No routes to update")
