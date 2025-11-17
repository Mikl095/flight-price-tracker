import json
import os

DATA_FILE = "data.json"
EMAIL_CONFIG_FILE = "email_config.json"

def ensure_data_file():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)

def load_routes():
    ensure_data_file()
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return []

def save_routes(routes):
    with open(DATA_FILE, "w") as f:
        json.dump(routes, f, indent=4, ensure_ascii=False)

def load_email_config():
    if not os.path.exists(EMAIL_CONFIG_FILE):
        return {"email": "", "enabled": False}
    with open(EMAIL_CONFIG_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {"email": "", "enabled": False}

def save_email_config(cfg):
    with open(EMAIL_CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)
