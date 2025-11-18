# utils/db.py
import json
import os
from typing import Dict, Any

DATA_FILE = os.path.join(os.getcwd(), "data.json")


def _ensure_file():
    """Create data.json if missing."""
    if not os.path.exists(DATA_FILE):
        initial = {"routes": []}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(initial, f, indent=2, ensure_ascii=False)


def load_db() -> Dict[str, Any]:
    """Loads the DB and auto-converts old formats."""
    _ensure_file()

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            doc = json.load(f)
        except json.JSONDecodeError:
            # Corrupted JSON → reset
            return {"routes": []}

    # --- AUTO-CORRECT OLD FORMATS ---
    # Case 1 : file is a list => convert
    if isinstance(doc, list):
        return {"routes": doc}

    # Case 2 : file is not a dict => reset
    if not isinstance(doc, dict):
        return {"routes": []}

    # Case 3 : dict missing "routes"
    if "routes" not in doc or not isinstance(doc["routes"], list):
        doc["routes"] = []

    return doc


def save_db(db: Dict[str, Any]) -> None:
    """Overwrite data.json with db dict."""
    _ensure_file()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
