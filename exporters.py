# exporters.py
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import io
from datetime import datetime
from utils.storage import json_safe
import os

# -----------------------------
# EXPORT CSV
# -----------------------------
def export_csv(routes, path="export.csv", route_id=None):
    """Export CSV pour tous les suivis ou un suivi spécifique."""
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
                "price": h.get("price"),
                "date": h.get("date")
            })
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path

# -----------------------------
# EXPORT XLSX
# -----------------------------
def export_xlsx(routes, path="export.xlsx", route_id=None):
    """Export XLSX pour tous les suivis ou un suivi spécifique."""
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
                "price": h.get("price"),
                "date": h.get("date")
            })
    df = pd.DataFrame(rows)
    df.to_excel(path, index=False)
    return path

# -----------------------------
# EXPORT PDF
# -----------------------------
def export_pdf(routes, path="export.pdf", route_id=None):
    """Export PDF avec graphiques pour tous les suivis ou un suivi spécifique."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    for r in routes:
        if route_id and r["id"] != route_id:
            continue
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"{r['origin']} → {r['destination']}", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, f"Départ: {r.get('departure')}  Retour: {r.get('return')}", ln=True)
        pdf.cell(0, 8, f"Seuil: {r.get('target_price')}€  Notifications: {'ON' if r.get('notifications') else 'OFF'}", ln=True)
        pdf.cell(0, 8, f"Min/Max séjour: {r.get('stay_min')}-{r.get('stay_max')} jours", ln=True)
        pdf.cell(0, 8, f"Classe: {r.get('travel_class','')}, Bagages: {r.get('min_bags',0)}, Direct only: {r.get('direct_only', False)}", ln=True)

        # Graphique historique
        history = r.get("history", [])
        if history:
            dates = [datetime.fromisoformat(h["date"]) for h in history]
            prices = [h["price"] for h in history]
            fig, ax = plt.subplots()
            ax.plot(dates, prices, marker='o')
            ax.set_title(f"{r['origin']} → {r['destination']} prix historique")
            ax.set_ylabel("Prix (€)")
            ax.set_xlabel("Date")
            fig.tight_layout()
            img_bytes = io.BytesIO()
            fig.savefig(img_bytes, format='png')
            plt.close(fig)
            img_bytes.seek(0)
            pdf.image(img_bytes, x=10, w=pdf.w - 20)

    pdf.output(path)
    return path
