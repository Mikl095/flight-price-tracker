# utils/actions.py
import uuid
from datetime import datetime
import random

try:
    from ..email_utils import send_email
except Exception:
    # relative fallback if run as module
    from email_utils import send_email

def add_route_from_dict(d: dict) -> dict:
    # Build a full route dict from a minimal form dict
    new = {
        "id": str(uuid.uuid4()),
        "origin": d.get("origin","PAR").upper(),
        "destination": d.get("destination","TYO").upper(),
        "departure": d.get("departure") or "",
        "departure_flex_days": int(d.get("departure_flex_days",0)),
        "return": d.get("return") or "",
        "return_airport": d.get("return_airport") or None,
        "stay_min": int(d.get("stay_min", 6)),
        "stay_max": int(d.get("stay_max", 10)),
        "return_flex_days": int(d.get("return_flex_days", 0)),
        "target_price": float(d.get("target_price", 500.0)),
        "tracking_per_day": int(d.get("tracking_per_day", 1)),
        "notifications": bool(d.get("notifications", False)),
        "min_bags": int(d.get("min_bags", 0)),
        "direct_only": bool(d.get("direct_only", False)),
        "max_stops": d.get("max_stops", "any"),
        "avoid_airlines": d.get("avoid_airlines", []),
        "preferred_airlines": d.get("preferred_airlines", []),
        "email": d.get("email",""),
        "history": d.get("history", []),
        "last_tracked": d.get("last_tracked", None),
        "stats": {}
    }
    return new

def bulk_update_sim(routes):
    for r in routes:
        price = random.randint(120, 1000)
        r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
        r["last_tracked"] = datetime.now().isoformat()
    return routes

def send_test_email_for_route(route):
    rcpt = route.get("email") or ""
    if not rcpt:
        return False, "no-recipient"
    ok, status = send_email(rcpt, f"Test: {route.get('origin')}→{route.get('destination')}", "<p>Test</p>")
    return ok, status
