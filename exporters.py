# exporters.py
import pandas as pd
from fpdf import FPDF
import xlsxwriter
from datetime import datetime

# -----------------------------
# CSV
# -----------------------------
def export_csv(routes, path="export.csv"):
    rows = []
    for r in routes:
        last_price = r.get("history")[-1]["price"] if r.get("history") else None
        rows.append({
            "ID": r.get("id"),
            "Origin": r.get("origin"),
            "Destination": r.get("destination"),
            "Departure": r.get("departure"),
            "Return": r.get("return"),
            "Stay Min": r.get("stay_min"),
            "Stay Max": r.get("stay_max"),
            "Target Price": r.get("target_price"),
            "Last Price": last_price,
            "Notifications": r.get("notifications"),
            "Email": r.get("email"),
            "Travel Class": r.get("travel_class", "Economy"),
            "Min Bags": r.get("min_bags"),
            "Direct Only": r.get("direct_only"),
            "Max Stops": r.get("max_stops"),
            "Avoid Airlines": ",".join(r.get("avoid_airlines", [])),
            "Preferred Airlines": ",".join(r.get("preferred_airlines", [])),
            "Last Tracked": r.get("last_tracked")
        })
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    return path

# -----------------------------
# XLSX
# -----------------------------
def export_xlsx(routes, path="export.xlsx"):
    rows = []
    for r in routes:
        last_price = r.get("history")[-1]["price"] if r.get("history") else None
        rows.append({
            "ID": r.get("id"),
            "Origin": r.get("origin"),
            "Destination": r.get("destination"),
            "Departure": r.get("departure"),
            "Return": r.get("return"),
            "Stay Min": r.get("stay_min"),
            "Stay Max": r.get("stay_max"),
            "Target Price": r.get("target_price"),
            "Last Price": last_price,
            "Notifications": r.get("notifications"),
            "Email": r.get("email"),
            "Travel Class": r.get("travel_class", "Economy"),
            "Min Bags": r.get("min_bags"),
            "Direct Only": r.get("direct_only"),
            "Max Stops": r.get("max_stops"),
            "Avoid Airlines": ",".join(r.get("avoid_airlines", [])),
            "Preferred Airlines": ",".join(r.get("preferred_airlines", [])),
            "Last Tracked": r.get("last_tracked")
        })
    df = pd.DataFrame(rows)
    writer = pd.ExcelWriter(path, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Routes')
    writer.save()
    return path

# -----------------------------
# PDF
# -----------------------------
def export_pdf(routes, path="export.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Flight Price Tracker Export", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", "", 10)
    for r in routes:
        pdf.multi_cell(0, 5, (
            f"ID: {r.get('id')}\n"
            f"Origin → Destination: {r.get('origin')} → {r.get('destination')}\n"
            f"Departure: {r.get('departure')} | Return: {r.get('return')}\n"
            f"Stay: {r.get('stay_min')}–{r.get('stay_max')} days\n"
            f"Target Price: {r.get('target_price')} | Last Price: {r.get('history')[-1]['price'] if r.get('history') else 'N/A'}\n"
            f"Notifications: {r.get('notifications')} | Email: {r.get('email')}\n"
            f"Class: {r.get('travel_class','Economy')} | Min Bags: {r.get('min_bags')}\n"
            f"Direct Only: {r.get('direct_only')} | Max Stops: {r.get('max_stops')}\n"
            f"Avoid Airlines: {','.join(r.get('avoid_airlines',[]))}\n"
            f"Preferred Airlines: {','.join(r.get('preferred_airlines',[]))}\n"
            f"Last Tracked: {r.get('last_tracked')}\n"
            "-------------------------------"
        ))
    pdf.output(path)
    return path
