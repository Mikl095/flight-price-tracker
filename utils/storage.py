# utils/storage.py
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

DATA_DIR = "."
ROUTES_FILE = os.path.join(DATA_DIR, "routes.json")
EMAIL_CFG_FILE = os.path.join(DATA_DIR, "email_config.json")
LOG_FILE = os.path.join(DATA_DIR, "last_updates.log")


def _atomic_write(path: str, data_bytes: bytes):
    """Write bytes to a temp file and atomically replace target."""
    tmp = f"{path}.tmp"
    with open(tmp, "wb") as f:
        f.write(data_bytes)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)  # atomic on POSIX and Windows


def ensure_data_file():
    """Ensure data files exist (create defaults if missing)."""
    if not os.path.exists(ROUTES_FILE):
        _atomic_write(ROUTES_FILE, b"[]")
    if not os.path.exists(EMAIL_CFG_FILE):
        _atomic_write(EMAIL_CFG_FILE, json.dumps({"enabled": False, "email": "", "api_user": "", "api_pass": ""}).encode("utf-8"))
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, "a").close()


def load_routes() -> List[Dict[str, Any]]:
    """Load list of routes from JSON, return [] on parse error but avoid crash."""
    try:
        with open(ROUTES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except FileNotFoundError:
        return []
    except Exception:
        # if malformed, rename the old file for inspection and return empty list
        try:
            ts = datetime.now().strftime("%Y%m%d%H%M%S")
            bad = f"{ROUTES_FILE}.broken.{ts}"
            os.replace(ROUTES_FILE, bad)
        except Exception:
            pass
        return []


def save_routes(routes: List[Dict[str, Any]]):
    """Save routes to JSON atomically."""
    b = json.dumps(routes, ensure_ascii=False, indent=2).encode("utf-8")
    _atomic_write(ROUTES_FILE, b)


def load_email_config() -> dict:
    try:
        with open(EMAIL_CFG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


def save_email_config(cfg: dict):
    b = json.dumps(cfg, ensure_ascii=False, indent=2).encode("utf-8")
    _atomic_write(EMAIL_CFG_FILE, b)


def append_log(line: str):
    """Append a single line to the log file (with newline)."""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line.rstrip("\n") + "\n")
    except Exception:
        # last resort: ignore log writes to avoid breaking app
        pass


def count_updates_last_24h(route: dict) -> int:
    """Return number of history entries in the last 24 hours (robust to formats)."""
    now = datetime.now()
    cutoff = now - timedelta(hours=24)
    cnt = 0
    for h in route.get("history", []) or []:
        d = h.get("date")
        if not d:
            continue
        try:
            # accept isoformat strings or epoch numbers
            if isinstance(d, (int, float)):
                dt = datetime.fromtimestamp(d)
            else:
                # assume string
                dt = datetime.fromisoformat(str(d))
            if dt >= cutoff:
                cnt += 1
        except Exception:
            # ignore malformed dates
            continue
    return cnt


def ensure_route_fields(r: dict):
    """Ensure a route dict has minimal expected keys (safe defaults)."""
    # minimal fields used by UI
    r.setdefault("id", "")
    r.setdefault("origin", "")
    r.setdefault("destination", "")
    r.setdefault("departure", None)
    r.setdefault("departure_flex_days", 0)
    r.setdefault("return", None)
    r.setdefault("return_flex_days", 0)
    r.setdefault("return_airport", None)
    r.setdefault("stay_min", 1)
    r.setdefault("stay_max", 1)
    r.setdefault("target_price", 100.0)
    r.setdefault("tracking_per_day", 1)
    r.setdefault("notifications", False)
    r.setdefault("email", "")
    r.setdefault("min_bags", 0)
    r.setdefault("direct_only", False)
    r.setdefault("max_stops", "any")
    r.setdefault("avoid_airlines", [])
    r.setdefault("preferred_airlines", [])
    r.setdefault("history", [])
    r.setdefault("last_tracked", None)
    r.setdefault("stats", {})

import numpy as np
import pandas as pd
from datetime import date, datetime

def json_safe(v):
    """Convert any value into a JSON-serializable type."""
    if v is None:
        return None
    if isinstance(v, np.generic):
        return v.item()
    if isinstance(v, float) and np.isnan(v):
        return None
    if v is pd.NA or v is pd.NaT:
        return None
    if isinstance(v, pd.Timestamp):
        return v.isoformat()
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    return v

def sanitize_dict(d):
    """Recursively sanitize any dict for JSON writing."""
    out = {}
    for k, v in d.items():
        if isinstance(v, list):
            out[k] = [json_safe(x) for x in v]
        elif isinstance(v, dict):
            out[k] = sanitize_dict(v)
        else:
            out[k] = json_safe(v)
    return out
