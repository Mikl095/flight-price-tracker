# exporters.py
import os
import pandas as pd
from fpdf import FPDF
import matplotlib.pyplot as plt
from io import BytesIO
from utils.storage import sanitize_dict
from utils.plotting import plot_price_history

# -----------------------------
# EXPORT CSV
# -----------------------------
def export_csv(routes, path="export.csv", route_ids=None):
    """Export CSV : tous les suivis ou un sous-ensemble par route_ids."""
    data = []
    for r in routes:
        if route_ids and r["id"] not in route_ids:
            continue
        for h in r.get("history", []):
            data.append({
                "id": r["id"],
                "origin": r["origin"],
                "destination": r["destination"],
                "departure": r["departure"],
                "return": r.get("return"),
                "stay_min": r.get("stay_min"),
                "stay_max": r.get("stay_max"),
                "target_price": r.get("target_price"),
                "price": h.get("price"),
                "date": h.get("date")
            })
    df = pd.DataFrame(data)
    df.to_csv(path, index=False, encoding="utf-8")
    return path

# -----------------------------
# EXPORT XLSX
# -----------------------------
def export_xlsx(routes, path="export.xlsx", route_ids=None):
    """Export XLSX avec historique et graphiques."""
    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        for r in routes:
            if route_ids and r["id"] not in route_ids:
                continue
            df = pd.DataFrame(r.get("history", []))
            if df.empty:
                df = pd.DataFrame(columns=["date", "price"])
            df.to_excel(writer, sheet_name=r["id"][:31], index=False)

            # Ajouter un graphique
            fig = plot_price_history(r.get("history", []))
            imgdata = BytesIO()
            fig.savefig(imgdata, format='png')
            imgdata.seek(0)
            workbook = writer.book
            worksheet = writer.sheets[r["id"][:31]]
            worksheet.insert_image('E2', '', {'image_data': imgdata})
            plt.close(fig)
    return path

# -----------------------------
# EXPORT PDF
# -----------------------------
def export_pdf(routes, path="export.pdf", route_ids=None):
    """Export PDF avec historique et graphiques."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    for r in routes:
        if route_ids and r["id"] not in route_ids:
            continue
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, f"Suivi: {r['origin']} → {r['destination']}", ln=True)
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 8, f"Départ: {r.get('departure')}, Retour: {r.get('return')}", ln=True)
        pdf.cell(0, 8, f"Séjour: {r.get('stay_min')}-{r.get('stay_max')} j", ln=True)
        pdf.cell(0, 8, f"Prix cible: {r.get('target_price')}€", ln=True)
        pdf.cell(0, 8, f"Notifications: {'ON' if r.get('notifications') else 'OFF'}", ln=True)

        # Ajouter un graphique
        fig = plot_price_history(r.get("history", []))
        imgdata = BytesIO()
        fig.savefig(imgdata, format='png')
        imgdata.seek(0)
        pdf.image(imgdata, x=10, y=None, w=180)
        plt.close(fig)

    pdf.output(path)
    return path
