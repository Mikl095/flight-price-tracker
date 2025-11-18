# exporters.py
import csv
import pandas as pd
from fpdf import FPDF
import matplotlib.pyplot as plt
from io import BytesIO

def export_csv(routes, path="export.csv", route_id=None):
    """Export CSV pour tous les suivis ou un suivi spécifique"""
    rows = []
    for r in routes:
        if route_id and r["id"] != route_id:
            continue
        for h in r.get("history", []):
            rows.append({
                "id": r["id"],
                "origin": r["origin"],
                "destination": r["destination"],
                "departure": r["departure"],
                "return": r.get("return"),
                "price": h["price"],
                "date": h["date"]
            })
    keys = rows[0].keys() if rows else []
    with open(path, "w", newline='', encoding="utf-8") as f:
        dict_writer = csv.DictWriter(f, keys)
        dict_writer.writeheader()
        dict_writer.writerows(rows)
    return path

def export_xlsx(routes, path="export.xlsx", route_id=None):
    """Export XLSX pour tous les suivis ou un suivi spécifique"""
    all_rows = []
    for r in routes:
        if route_id and r["id"] != route_id:
            continue
        for h in r.get("history", []):
            all_rows.append({
                "ID": r["id"],
                "Origine": r["origin"],
                "Destination": r["destination"],
                "Départ": r["departure"],
                "Retour": r.get("return"),
                "Prix": h["price"],
                "Date": h["date"]
            })
    df = pd.DataFrame(all_rows)
    df.to_excel(path, index=False)
    return path

def export_pdf(routes, path="export.pdf", route_id=None):
    """Export PDF avec graph pour tous les suivis ou un suivi spécifique"""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    for r in routes:
        if route_id and r["id"] != route_id:
            continue
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, f"{r['origin']} → {r['destination']}", ln=True)
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 8, f"Départ: {r['departure']} | Retour: {r.get('return','—')}", ln=True)
        pdf.cell(0, 8, f"Seuil cible: {r.get('target_price')}€ | Notifications: {'ON' if r.get('notifications') else 'OFF'}", ln=True)
        pdf.cell(0, 8, f"Email: {r.get('email','—')}", ln=True)
        pdf.ln(4)

        # Graph historique prix
        history = r.get("history", [])
        if history:
            dates = [h["date"] for h in history]
            prices = [h["price"] for h in history]
            plt.figure(figsize=(6,3))
            plt.plot(dates, prices, marker='o')
            plt.xticks(rotation=45)
            plt.title(f"Historique prix {r['origin']}→{r['destination']}")
            plt.tight_layout()
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png')
            plt.close()
            img_buffer.seek(0)
            pdf.image(img_buffer, x=10, w=pdf.w - 20)
            pdf.ln(5)
    pdf.output(path)
    return path
