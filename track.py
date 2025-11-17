import json
import random
from datetime import datetime

from utils import load_routes, save_routes, load_email_config
from email_utils import send_email

routes = load_routes()
email_cfg = load_email_config()
EMAIL = email_cfg.get("email", "")

for r in routes:
    # simulation prix
    price = random.randint(250, 900)

    r["history"].append({
        "date": str(datetime.now()),
        "price": price
    })
    r["last_tracked"] = str(datetime.now())

    # Envoi email
    if EMAIL and r["notifications"] and price <= r["target_price"]:
        subject = f"🔥 Alerte prix {r['origin']} → {r['destination']} : {price}€"
        msg = (
            f"Prix actuel : {price}€\n"
            f"Objectif : {r['target_price']}€\n\n"
            f"Dates : {r['departure']} → {r['return']}"
        )
        send_email(EMAIL, subject, msg)

save_routes(routes)
