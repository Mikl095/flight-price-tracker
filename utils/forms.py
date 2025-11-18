# utils/forms.py
from datetime import datetime, date, timedelta
import uuid
import streamlit as st

def add_route_form(routes, save_routes, append_log):
    """Render the Add-route form and handle submission."""
    st.header("➕ Ajouter un suivi")

    with st.form("form_add_new"):
        origins = st.text_area("Origines (IATA, séparées par ,)", value="PAR")
        destinations = st.text_area("Destinations (IATA, séparées par ,)", value="TYO")

        departure_date = st.date_input("Date départ (approx.)", date.today() + timedelta(days=90))
        dep_flex = st.number_input("Plage départ ± jours", min_value=0, max_value=30, value=1)

        return_date = st.date_input("Date retour (optionnelle)", value=None)
        return_flex = st.number_input("Plage retour ± jours", min_value=0, max_value=30, value=1)
        return_airport = st.text_input("Aéroport retour (IATA) — vide = même", "")

        priority_stay = st.checkbox("Priorité durée de séjour si pas de date de retour", value=False)

        stay_min = st.number_input("Séjour min (jours)", min_value=1, max_value=365, value=6)
        stay_max = st.number_input("Séjour max (jours)", min_value=1, max_value=365, value=10)

        target_price = st.number_input("Seuil alerte (€)", min_value=1.0, value=450.0)
        tracking_per_day = st.number_input("Trackings par jour", min_value=1, max_value=24, value=2)
        notifications_on = st.checkbox("Activer notifications pour ce suivi", value=True)

        min_bags = st.number_input("Min bagages (préférence)", min_value=0, max_value=5, value=0)
        direct_only = st.checkbox("Vol direct uniquement (préférence)", value=False)
        max_stops = st.selectbox("Max escales (préférence)", ["any", 0, 1, 2])
        avoid_airlines = st.text_input("Compagnies à éviter (IATA, séparées par ,)", value="")
        preferred_airlines = st.text_input("Compagnies préférées (IATA, séparées par ,)", value="")

        route_email = st.text_input("Email pour ce suivi (vide = email global)", value="")

        add_submit = st.form_submit_button("Ajouter ce suivi")

    if add_submit:
        created = 0
        for origin in [o.strip().upper() for o in origins.split(",") if o.strip()]:
            for destination in [d.strip().upper() for d in destinations.split(",") if d.strip()]:
                new = {
                    "id": str(uuid.uuid4()),
                    "origin": origin,
                    "destination": destination,
                    "departure": departure_date.isoformat(),
                    "departure_flex_days": int(dep_flex),
                    "return": return_date.isoformat() if return_date else None,
                    "return_flex_days": int(return_flex),
                    "priority_stay": bool(priority_stay),
                    "return_airport": return_airport.upper().strip() if return_airport else None,
                    "stay_min": int(stay_min),
                    "stay_max": int(stay_max),
                    "target_price": float(target_price),
                    "tracking_per_day": int(tracking_per_day),
                    "notifications": bool(notifications_on),
                    "email": route_email.strip(),
                    "min_bags": int(min_bags),
                    "direct_only": bool(direct_only),
                    "max_stops": max_stops,
                    "avoid_airlines": [a.strip().upper() for a in avoid_airlines.split(",") if a.strip()],
                    "preferred_airlines": [a.strip().upper() for a in preferred_airlines.split(",") if a.strip()],
                    "history": [],
                    "last_tracked": None,
                    "stats": {}
                }
                routes.append(new)
                append_log(f"{datetime.now().isoformat()} - Added route {new['id']}")
                created += 1

        save_routes(routes)
        st.success(f"Suivi(s) ajouté(s) ✔ ({created})")
        st.rerun()


def edit_route_form(r, idx, routes, save_routes, append_log, email_cfg):
    """
    Render the edit form for a single route.
    - Allows omitting the return date (priority on stay duration) like in creation.
    - Provides same fields/features as creation (priority_stay, return_airport, etc).
    """
    with st.expander("✏️ Éditer ce suivi"):
        with st.form(key=f"dash_form_{r['id']}"):
            # ROUTE BASE
            origin_e = st.text_input("Origine (IATA)", value=r.get("origin", ""))
            dest_e = st.text_input("Destination (IATA)", value=r.get("destination", ""))

            # DÉPART
            try:
                dep_default = (datetime.fromisoformat(r.get("departure")).date() if r.get("departure") else date.today())
            except Exception:
                dep_default = date.today()

            departure_e = st.date_input("Date départ", value=dep_default)
            depflex = st.number_input("Flex départ ± jours", min_value=0, max_value=30, value=int(r.get("departure_flex_days", 0)))

            # OPTIONNEL: Retour ou priorité durée de séjour (comme creation)
            priority_stay = st.checkbox(
                "Priorité durée de séjour (pas de date de retour définie)",
                value=bool(r.get("priority_stay", False))
            )

            # If priority_stay is False, allow editing a return date (optionally empty)
            if not priority_stay:
                # try to parse existing return date; if absent, default to dep + 7
                try:
                    ret_default = (datetime.fromisoformat(r.get("return")).date() if r.get("return") else (dep_default + timedelta(days=7)))
                except Exception:
                    ret_default = dep_default + timedelta(days=7)
                return_e = st.date_input("Date retour (optionnelle)", value=ret_default)
            else:
                # show a hint to user
                st.write("Aucun date de retour sera sauvegardée — la durée de séjour (stay_min/stay_max) sera priorisée.")

            return_flex_e = st.number_input("Flex retour ± jours", min_value=0, max_value=30, value=int(r.get("return_flex_days", 0)))
            return_airport_e = st.text_input("Aéroport retour (IATA) — vide = même", value=r.get("return_airport") or "")

            # SÉJOUR (identique à création)
            stay_min_e = st.number_input("Séjour min (jours)", min_value=1, max_value=365, value=int(r.get("stay_min", 1)))
            stay_max_e = st.number_input("Séjour max (jours)", min_value=1, max_value=365, value=int(r.get("stay_max", 1)))

            # PRIX / TRACKING
            target_e = st.number_input("Seuil alerte (€)", min_value=1.0, value=float(r.get("target_price", 100.0)))
            tracking_pd_e = st.number_input("Trackings par jour", min_value=1, max_value=24, value=int(r.get("tracking_per_day", 1)))
            notif_e = st.checkbox("Activer notifications pour ce vol", value=bool(r.get("notifications", False)))
            email_e = st.text_input("Email pour ce suivi (vide = global)", value=r.get("email", ""))

            # PREFERENCES
            min_bags_e = st.number_input("Min bagages", min_value=0, max_value=5, value=int(r.get("min_bags", 0)))
            direct_only_e = st.checkbox("Vol direct uniquement", value=r.get("direct_only", False))
            max_stops_e = st.selectbox("Max escales", ["any", 0, 1, 2], index=["any", 0, 1, 2].index(r.get("max_stops", "any")))
            avoid_e = st.text_input("Compagnies à éviter (IATA, séparées par ,)", value=",".join(r.get("avoid_airlines", [])))
            pref_e = st.text_input("Compagnies préférées (IATA, séparées par ,)", value=",".join(r.get("preferred_airlines", [])))

            submit_edit = st.form_submit_button("Enregistrer les modifications")

        if submit_edit:
            # apply edits (same keys as creation)
            r["origin"] = origin_e.upper().strip()
            r["destination"] = dest_e.upper().strip()
            r["departure"] = departure_e.isoformat()
            r["departure_flex_days"] = int(depflex)

            # return handling: if priority_stay -> clear return; else save return date
            r["priority_stay"] = bool(priority_stay)
            if priority_stay:
                r["return"] = None
            else:
                # return_e exists only when priority_stay is False
                r["return"] = return_e.isoformat() if return_e else None

            r["return_flex_days"] = int(return_flex_e)
            r["return_airport"] = return_airport_e.upper().strip() if return_airport_e else None

            r["stay_min"] = int(stay_min_e)
            r["stay_max"] = int(stay_max_e)

            r["target_price"] = float(target_e)
            r["tracking_per_day"] = int(tracking_pd_e)

            r["notifications"] = bool(notif_e)
            r["email"] = email_e.strip()

            r["min_bags"] = int(min_bags_e)
            r["direct_only"] = bool(direct_only_e)
            r["max_stops"] = max_stops_e

            r["avoid_airlines"] = [a.strip().upper() for a in avoid_e.split(",") if a.strip()]
            r["preferred_airlines"] = [a.strip().upper() for a in pref_e.split(",") if a.strip()]

            # persist and log
            save_routes(routes)
            append_log(f"{datetime.now().isoformat()} - Edited route {r['id']}")
            st.success("Modifications enregistrées.")
            st.rerun()
