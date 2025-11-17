import json
import os

DATA_FILE = "data/routes.json"

def ensure_data_file():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)

def load_routes():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_routes(routes):
    with open(DATA_FILE, "w") as f:
        json.dump(routes, f, indent=4)
