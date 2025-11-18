# utils/storage.py
import json
import os
import uuid
from datetime import datetime, timedelta

DATA_FILE = "data/routes.json"
EMAIL_CFG_FILE = "data/email_config.json"
LOG_FILE = "data/log.txt"

def ensure_data_file():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)
    if not os.path.exists(EMAIL_CFG_FILE):
        with open(EMAIL_CFG_FILE, "w") as f:
            json.dump({"enabled": False, "email": "", "api_user": "", "api_pass": ""}, f)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write("")

def load_routes():
    ensure_data_file()
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_routes(routes):
    with open(DATA_FILE, "w") as f:
        json.dump(routes, f, indent=2)

def load_email_config():
    ensure_data_file()
    with open(EMAIL_CFG_FILE, "r") as f:
        return json.load(f)

def save_email_config(cfg):
    ensure_data_file()
    with open(EMAIL_CFG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def append_log(msg):
    ensure_data_file()
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")

def count_updates_last_24h(route):
    now = datetime.now()
    count = 0
    for h in route.get("history", []):
        d = datetime.fromisoformat(h["date"])
        if now - d < timedelta(days=1):
            count += 1
    return count

def ensure_route_fields(route):
    defaults = {
        "id": str(uuid.uuid4()),
        "origin": "",
        "destination": "",
        "departure": None,
        "departure_flex_days": 0,
        "return": None,
        "return_flex_days": 0,
        "priority_stay": False,
        "return_airport": None,
        "stay_min": 1,
        "stay_max": 1,
        "target_price": 0.0,
        "tracking_per_day": 1,
        "notifications": False,
        "email": "",
        "cabin_class": "Economy",
        "min_bags": 0,
        "direct_only": False,
        "max_stops": "any",
        "avoid_airlines": [],
        "preferred_airlines": [],
        "history": [],
        "last_tracked": None,
        "stats": {}
    }
    for k,v in defaults.items():
        if k not in route:
            route[k] = v

def sanitize_dict(d):
    # convert all values to serializable types
    import copy
    dd = copy.deepcopy(d)
    for k,v in dd.items():
        if isinstance(v, datetime):
            dd[k] = v.isoformat()
        elif isinstance(v, list):
            dd[k] = [sanitize_dict(i) if isinstance(i, dict) else i for i in v]
        elif isinstance(v, dict):
            dd[k] = sanitize_dict(v)
    return dd
