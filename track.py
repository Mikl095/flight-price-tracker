import random
from datetime import datetime
from utils.storage import load_routes, save_routes, load_email_config, append_log, count_updates_last_24h, ensure_route_fields, increment_route_stat
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
    ensure_route_fields(r)
    per_day = int(r.get("tracking_per_day", 1))
    already_today = count_updates_last_24h(r)
    if already_today >= per_day:
        append_log(f"{datetime.now().isoformat()} - SKIP {r.get('id','?')} already_today={already_today} per_day={per_day}")
        continue

    # simulate price fetch (replace with real API)
    price = random.randint(120, 1000)
    now = datetime.now().isoformat()
    r.setdefault("history", []).append({"date": now, "price": price})
    r["last_tracked"] = now
    increment_route_stat(r, "updates_total")
    increment_route_stat(r, "updates_today")
    changed = True
    append_log(f"{datetime.now().isoformat()} - UPDATED {r.get('id','?')} price={price}")

    # Notification
    recipient = r.get("email") or GLOBAL_EMAIL
    if r.get("notifications") and recipient and (r.get("email") or GLOBAL_ENABLED):
        target = r.get("target_price")
        if target is not None and price <= target:
            subject = f"[ALERTE] {r['origin']}→{r['destination']}: {price}€"
            body = f"Prix actuel: {price}€\nSeuil: {target}€\nDates: {r.get('departure')} → {r.get('return')}"
            ok, status = send_email(recipient, subject, body)
            append_log(f"{datetime.now().isoformat()} - NOTIFY to={recipient} ok={ok} status={status}")
            if ok:
                increment_route_stat(r, "notifications_sent")

if changed:
    save_routes(routes)
    append_log(f"{datetime.now().isoformat()} - track.py done: saved")
else:
    append_log(f"{datetime.now().isoformat()} - track.py done: no changes")
