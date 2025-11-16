import json
import os

ROUTE_FILE = "routes.json"

# Vérifier si le fichier existe
if not os.path.exists(ROUTE_FILE):
    print(f"Fichier {ROUTE_FILE} introuvable.")
    exit()

# Charger les routes existantes
with open(ROUTE_FILE, "r") as f:
    routes = json.load(f)

# Nettoyer chaque route
for route in routes:
    # Ajouter last_tracked si absent
    if 'last_tracked' not in route:
        route['last_tracked'] = None
    # Ajouter history si absent
    if 'history' not in route:
        route['history'] = []

# Sauvegarder les routes corrigées
with open(ROUTE_FILE, "w") as f:
    json.dump(routes, f, indent=4)

print("✅ routes.json nettoyé avec succès !")
