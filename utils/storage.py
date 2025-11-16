import json
import os

DATA_FILE = "data/routes.json"

def ensure_data_file():
    """Créer le dossier et fichier data si absents."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.isfile(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump([], f)

def load_routes():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_routes(routes):
    with open(DATA_FILE, 'w') as f:
        json.dump(routes, f, indent=2)
        
