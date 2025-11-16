import os
import json

DATA_FILE = "data/routes.json"

def ensure_data_file():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump([], f)

def load_routes():
    ensure_data_file()
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_routes(routes):
    with open(DATA_FILE, "w") as f:
        json.dump(routes, f, indent=2)
      
