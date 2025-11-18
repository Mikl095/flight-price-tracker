# utils/forms.py
from datetime import date, datetime, timedelta

def route_form_empty():
    """Return a dict with values read from Streamlit inputs (called inside a form)."""
    # NOTE: called inside st.form in app.py
    origin = st.text_input("Origine (IATA)", value="PAR").upper()
    destination = st.text_input("Destination (IATA)", value="TYO").upper()
    departure_date = st.date_input("Date départ (approx.)", date.today() + timedelta(days=90))
    dep_flex = st.number_input("Plage départ ± jours", min_value=0, max_value=30, value=1)
    target_price = st.number_input("Seuil alerte (€)", min_value=1.0, value=450.0)
    tracking_per_day = st.number_input("Trackings par jour", min_value=1, max_value=24, value=2)
    notifications = st.checkbox("Activer notifications pour ce suivi", value=True)
    email = st.text_input("Email pour ce suivi (laisser vide = global)", value="")
    # pack minimal fields for quick add
    return {
        "origin": origin,
        "destination": destination,
        "departure": departure_date.isoformat(),
        "departure_flex_days": int(dep_flex),
        "target_price": float(target_price),
        "tracking_per_day": int(tracking_per_day),
        "notifications": bool(notifications),
        "email": email.strip()
    }

def route_form_from_row(row):
    """Return the editable form elements for an existing route (used in edit)."""
    # For completeness - not used directly in compact app but available if needed.
    origin = st.text_input("Origine (IATA)", value=row.get("origin","")).upper()
    # ... similar to route_form_empty but with defaults taken from row
    return {}
