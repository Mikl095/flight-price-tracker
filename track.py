"""
Script lancé par GitHub Actions (ou local) — effectue un run de tracking.
Il respecte `tracking_per_day` en contrôlant le nombre d'updates sur les dernières 24h.
"""
import random
from datetime import datetime
from utils.storage import load_routes, save_routes, load_email_config, append_log, count_updates_last_24h
from email_utils import send_email
import os

routes = load_routes()
email_cfg = load_email_config()
GLOBAL_EMAIL = email_cfg.get("email", "")
GLOBAL_ENABLED = email_cfg.get("enabled", False)

run_ts = datetime.now().isoformat()
append_log(f"{run_ts} - track.py start")

changed = False
for r in routes:
    # compute if we should update this route now according to tracking_per_day
    per_day = int(r.get("tracking_per_day", 1))
    already_today = count_updates_last_24h(r)
    # if per_day <= already_today -> skip
    if already_today >= per_day:
        append_log(f"{datetime.now().isoformat()} - skipping {r.get('id','?')} already_today={already_today} per_day={per_day}")
        continue

    # simulate a price update (replace with Amadeus later)
    price = random.randint(150, 900)
    r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
    r["last_tracked"] = datetime.now().isoformat()
    changed = True
    append_log(f"{datetime.now().isoformat()} - updated {r.get('id','?')} price={price}")

    # notification logic
    recipient = r.get("email") or GLOBAL_EMAIL
    global_send_ok = GLOBAL_ENABLED
    if r.get("notifications") and recipient and (r.get("email") or global_send_ok):
        target = r.get("target_price")
        if target is not None and price <= target:
            subject = f"[ALERTE] {r['origin']}→{r['destination']}: {price}€"
            body = f"Prix actuel: {price}€\nSeuil: {target}€\nDates: {r.get('departure')} → {r.get('return')}"
            ok, status = send_email(recipient, subject, body)
            append_log(f"{datetime.now().isoformat()} - notify to={recipient} ok={ok} status={status}")

if changed:
    save_routes(routes)
    append_log(f"{datetime.now().isoformat()} - track.py done: saved")
else:
    append_log(f"{datetime.now().isoformat()} - track.py done: no changes")
