import random
from datetime import datetime
from utils.storage import load_routes, save_routes, load_email_config, append_log
from email_utils import send_email
import os

routes = load_routes()
email_cfg = load_email_config()
GLOBAL_EMAIL_ENABLED = email_cfg.get("enabled", False)
GLOBAL_EMAIL = email_cfg.get("email", "")

def simulate_price_update(route):
    price = random.randint(150, 900)
    route.setdefault("history", [])
    route["history"].append({"date": datetime.now().isoformat(), "price": price})
    route["last_tracked"] = datetime.now().isoformat()
    return price

changes = False
for r in routes:
    price = simulate_price_update(r)
    changes = True

    # determine email recipient: route-specific or global
    recipient = r.get("email") or GLOBAL_EMAIL
    if r.get("notifications") and (r.get("email") or GLOBAL_EMAIL_ENABLED) and recipient:
        target = r.get("target_price")
        if target is not None and price <= target:
            subject = f"[ALERTE] {r['origin']}→{r['destination']}: {price}€"
            body = f"Prix actuel: {price}€\nSeuil: {target}€\nDates: {r.get('departure')} → {r.get('return')}"
            ok = send_email(recipient, subject, body)
            append_log(f"{datetime.now().isoformat()} - Notification sent to {recipient}: {ok}")

if changes:
    save_routes(routes)
    append_log(f"{datetime.now().isoformat()} - Tracking run done, saved.")
else:
    append_log(f"{datetime.now().isoformat()} - Tracking run: no routes")
