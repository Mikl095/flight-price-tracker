from utils.storage import load_routes, save_routes
from utils.tracking import simulate_auto_tracking

routes = load_routes()

for route in routes:
    simulate_auto_tracking(route)

save_routes(routes)
