# utils/json_utils.py
import numpy as np
import pandas as pd
from datetime import date, datetime

def json_safe(v):
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
