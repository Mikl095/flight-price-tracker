from datetime import datetime

def tracking_needed(route):
    """Retourne True si un tracking doit être effectué."""
    last = route.get("last_tracked")
    if not last:
        return True

    last_dt = datetime.fromisoformat(last)
    interval_hours = 24 / max(route.get("tracking_per_day", 1), 1)

    hours_passed = (datetime.now() - last_dt).total_seconds() / 3600
    return hours_passed >= interval_hours
  
