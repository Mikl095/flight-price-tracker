# utils/simulation.py
import random
import math
from datetime import datetime

def _seed_from_route(route: dict) -> int:
    """Produce a stable-ish seed from route id/origin/destination to get reproducible simulation across runs."""
    s = f"{route.get('id','')}-{route.get('origin','')}-{route.get('destination','')}"
    return abs(hash(s)) % (2**31)

def simulate_price(route: dict) -> int:
    """
    Simulate a price (int, €) for the given route.
    - If route has history, vary around the last price.
    - Otherwise produce a base price depending on pseudo-distance (origin/destination hash).
    """
    # Try to base on last price if available
    history = route.get("history", [])
    if history:
        try:
            last = int(history[-1].get("price"))
        except Exception:
            last = None
    else:
        last = None

    # seed randomness for reproducibility per route + day
    seed = _seed_from_route(route) + int(datetime.now().timestamp() // 3600)  # changes every hour
    rnd = random.Random(seed)

    if last and isinstance(last, int):
        # small percent change ±0-12%
        pct = rnd.uniform(-0.12, 0.12)
        new_price = max(30, int(round(last * (1 + pct))))
    else:
        # generate a base price using hashed pseudo-distance
        h = _seed_from_route(route)
        # normalized pseudo-distance factor
        factor = (h % 5000) / 5000  # 0..1
        base = 200 + int(factor * 1000)  # 200..1200
        # add some noise
        new_price = base + rnd.randint(-50, 120)

    # clamp to reasonable range
    new_price = max(20, min(new_price, 5000))
    return int(new_price)
