from datetime import datetime
import random

def simulate_auto_tracking(route):
    now = datetime.now()

    last_tracked_str = route.get('last_tracked')
    route.setdefault('history', [])

    last = datetime.fromisoformat(last_tracked_str) if last_tracked_str else None
    interval = 24 / max(route.get('tracking_per_day', 1), 1)  # heures

    updates_needed = 0
    if last:
        hours_passed = (now - last).total_seconds() / 3600
        updates_needed = int(hours_passed // interval)
    else:
        updates_needed = 1

    for _ in range(updates_needed):
        price = random.randint(200, 800)  # simulation prix
        route['history'].append({
            "date": str(now),
            "price": price
        })
        route['last_tracked'] = str(now)
        
