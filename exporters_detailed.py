# exporters_detailed.py
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# -----------------------------
# XLSX détaillé (avec historique)
# -----------------------------
def export_xlsx_detailed(routes, path="export_detailed.xlsx"):
    rows = []
    for r in routes:
        history = r.get("history", [])
        if not history:
            rows.append({
                "ID": r.get("id"),
                "Origin": r.get("origin"),
                "Destination": r.get("destination"),
                "Departure": r.get("departure"),
                "Return": r.get("return"),
                "Stay Min": r.get("stay_min"),
                "Stay Max": r.get("stay_max"),
                "Target Price": r.get("target_price"),
                "Price": None,
                "Price Date": None,
                "Notifications": r.get("notifications"),
                "Email": r.get("email"),
                "Travel Class": r.get("travel_class","Economy"),
                "Min Bags": r.get("min_bags"),
                "Direct Only": r.get("direct_only"),
                "Max Stops": r.get("max_stops"),
                "Avoid Airlines": ",".join(r.get("avoid_airlines", [])),
                "Preferred Airlines": ",".join(r.get("preferred_airlines", [])),
                "Last Tracked": r.get("last_tracked")
            })
        else:
            for h in history:
                rows.append({
                    "ID": r.get("id"),
                    "Origin": r.get("origin"),
                    "Destination": r.get("destination"),
                    "Departure": r.get("departure"),
                    "Return": r.get("return"),
                    "Stay Min": r.get("stay_min"),
                    "Stay Max": r.get("stay_max"),
                    "Target Price": r.get("target_price"),
                    "Price": h.get("price"),
                    "Price Date": h.get("date"),
                    "Notifications": r.get("notifications"),
                    "Email": r.get("email"),
                    "Travel Class": r.get("travel_class","Economy"),
                    "Min Bags": r.get("min_bags"),
                    "Direct Only": r.get("direct_only"),
                    "Max Stops": r.get("max_stops"),
                    "Avoid Airlines": ",".join(r.get("avoid_airlines", [])),
                    "Preferred Airlines": ",".join(r.get("preferred_airlines", [])),
                    "Last Tracked": r.get("last_tracked")
                })
    df = pd.DataFrame(rows)
    df.to_excel(path, index=False)
    return path

# -----------------------------
# PDF détaillé (avec historique)
# -----------------------------
def export_pdf_detailed(routes, path="export_detailed.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Flight Price Tracker - Détails Historique", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", "", 10)
    for r in routes:
        pdf.multi_cell(0, 5, (
            f"ID: {r.get('id')}\n"
            f"Origin → Destination: {r.get('origin')} → {r.get('destination')}\n"
            f"Departure: {r.get('departure')} | Return: {r.get('return')}\n"
            f"Stay: {r.get('stay_min')}–{r.get('stay_max')} days\n"
            f"Target Price: {r.get('target_price')}\n"
            f"Notifications: {r.get('notifications')} | Email: {r.get('email')}\n"
            f"Class: {r.get('travel_class','Economy')} | Min Bags: {r.get('min_bags')}\n"
            f"Direct Only: {r.get('direct_only')} | Max Stops: {r.get('max_stops')}\n"
            f"Avoid Airlines: {','.join(r.get('avoid_airlines',[]))}\n"
            f"Preferred Airlines: {','.join(r.get('preferred_airlines',[]))}\n"
            f"Last Tracked: {r.get('last_tracked')}\n"
            "Price History:"
        ))
        history = r.get("history", [])
        if history:
            for h in history:
                pdf.cell(0, 5, f" - {h.get('date')}: {h.get('price')}€", ln=True)
        else:
            pdf.cell(0, 5, " - Aucun historique", ln=True)
        pdf.cell(0, 5, "-------------------------------", ln=True)
    pdf.output(path)
    return path
