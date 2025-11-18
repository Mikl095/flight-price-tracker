# helpers.py
from datetime import date, datetime
import numpy as np
import pandas as pd
import os

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
    """Sanitize recursively any dict for JSON writing."""
    out = {}
    for k, v in d.items():
        if isinstance(v, list):
            out[k] = [json_safe(x) for x in v]
            continue
        if isinstance(v, dict):
            out[k] = sanitize_dict(v)
            continue
        out[k] = json_safe(v)
    return out

def safe_iso_to_datetime(val):
    """Return a datetime or None for different possible input types."""
    if val is None:
        return None

    if isinstance(val, datetime):
        return val

    if isinstance(val, date) and not isinstance(val, datetime):
        return datetime.combine(val, datetime.min.time())

    if isinstance(val, str):
        if not val.strip():
            return None
        try:
            return datetime.fromisoformat(val)
        except Exception:
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y"):
                try:
                    return datetime.strptime(val, fmt)
                except Exception:
                    continue
            return None

    return None

def file_bytes_for_path(path):
    """Return bytes for a path; raise FileNotFoundError if missing."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found")
    with open(path, "rb") as f:
        return f.read()
