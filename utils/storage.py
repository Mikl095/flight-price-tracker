import json
import os
from datetime import datetime, timedelta

DATA_FILE = "data.json"
EMAIL_CONFIG_FILE = "email_config.json"
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "track.log")

def ensure_data_file():
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

def load_routes():
    ensure_data_file()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_routes(routes):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(routes, f, indent=2, ensure_ascii=False)

def load_email_config():
    if not os.path.exists(EMAIL_CONFIG_FILE):
        return {"email": "", "enabled": False}
    try:
        with open(EMAIL_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"email": "", "enabled": False}

def save_email_config(cfg):
    with open(EMAIL_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def append_log(line):
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line.rstrip() + "\n")

# ------------------------------------------------------------------
# helpers for tracking frequency and stats
# ------------------------------------------------------------------
def count_updates_last_24h(route):
    """Count history entries in last 24 hours."""
    if not route.get("history"):
        return 0
    now = datetime.now()
    cutoff = now - timedelta(hours=24)
    cnt = 0
    for h in route.get("history", []):
        try:
            d = datetime.fromisoformat(h["date"])
        except Exception:
            continue
        if d >= cutoff:
            cnt += 1
    return cnt

def increment_route_stat(route, key):
    """Add a numeric stat under route['stats'] (creates dict if missing)."""
    stats = route.setdefault("stats", {})
    stats[key] = stats.get(key, 0) + 1

def ensure_route_fields(route):
    """Ensure route has fields used by tracker to avoid KeyErrors."""
    route.setdefault("history", [])
    route.setdefault("notifications", False)
    route.setdefault("tracking_per_day", 1)
    route.setdefault("target_price", None)
    route.setdefault("email", "")
    route.setdefault("stats", {})
