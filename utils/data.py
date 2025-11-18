# utils/data.py
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict

# try import your existing storage functions (keeps compatibility)
try:
    from .storage import (
        ensure_data_file as storage_ensure,
        load_routes as storage_load_routes,
        save_routes as storage_save_routes,
        load_email_config as storage_load_email_config,
        save_email_config as storage_save_email_config,
        append_log as storage_append_log
    )
except Exception:
    # fallback simple implementations if storage not present
    storage_ensure = None
    storage_load_routes = lambda: []
    storage_save_routes = lambda r: None
    storage_load_email_config = lambda: {}
    storage_save_email_config = lambda cfg: None
    storage_append_log = lambda s: None

DATA_FILE = "data.json"

def ensure_data_file():
    if storage_ensure:
        storage_ensure()
        return
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"routes": [], "email": {}}, f)

def load_routes():
    if storage_load_routes and storage_load_routes != (lambda: []):
        return storage_load_routes()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        doc = json.load(f)
    return doc.get("routes", [])

def save_routes(routes):
    if storage_save_routes and storage_save_routes != (lambda r: None):
        return storage_save_routes(routes)
    with open(DATA_FILE, "r+", encoding="utf-8") as f:
        doc = json.load(f)
        doc["routes"] = routes
        f.seek(0)
        json.dump(doc, f, indent=2)
        f.truncate()

def load_email_config():
    if storage_load_email_config:
        return storage_load_email_config()
    return {}

def save_email_config(cfg):
    if storage_save_email_config:
        return storage_save_email_config(cfg)
    return {}

def append_log(s: str):
    if storage_append_log:
        return storage_append_log(s)
    # fallback no-op

def ensure_route_fields(r: dict):
    # ensure some keys exist to avoid KeyError
    defaults = {
        "history": [], "stats": {}, "departure_flex_days": 0, "return_flex_days": 0,
        "stay_min": 1, "stay_max": 7, "tracking_per_day": 1, "notifications": False
    }
    for k, v in defaults.items():
        if k not in r:
            r[k] = v
    return r

def count_updates_last_24h(route: dict) -> int:
    cnt = 0
    for h in route.get("history", []):
        try:
            ts = datetime.fromisoformat(h.get("date"))
            if datetime.now() - ts <= timedelta(days=1):
                cnt += 1
        except Exception:
            continue
    return cnt
