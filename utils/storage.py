import json
import os

DATA_FILE = "data.json"
EMAIL_CONFIG_FILE = "email_config.json"
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "track.log")

def ensure_data_file():
    os.makedirs(os.path.dirname(DATA_FILE) or ".", exist_ok=True)
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
