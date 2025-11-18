# exporters.py
import pandas as pd
from fpdf import FPDF
import matplotlib.pyplot as plt
from io import BytesIO
import os
from datetime import datetime

# -----------------------------
# EXPORT CSV
# -----------------------------
def export_csv(routes, filename="export.csv"):
    rows = []
    for r in routes:
        for h in r.get("history", []):
            rows.append({
                "ID": r.get("id"),
                "Origin": r.get("origin"),
                "Destination": r.get("destination"),
                "Departure": r.get("departure"),
                "Return": r.get("return"),
                "Cabin": r.get("cabin_class"),
                "DirectOnly": r.get("direct_only"),
                "MinBags": r.get("min_bags"),
                "Price": h["price"],
                "DateTracked": h["date"]
            })
    df = pd.DataFrame(rows)
    df.to_csv(filename, index=False)

# -----------------------------
# EXPORT XLSX
# -----------------------------
def export_xlsx(routes, filename="export.xlsx"):
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        for r in routes:
            hist = pd.DataFrame(r.get("history", []))
            if hist.empty:
                hist = pd.DataFrame(columns=["date","price"])
            hist.to_excel(writer, sheet_name=f"{r['origin']}_{r['destination']}", index=False)
            # Ajouter graphique
            workbook  = writer.book
            worksheet = writer.sheets[f"{r['origin']}_{r['destination']}"]
            chart = workbook.add_chart({'type': 'line'})
            chart.add_series({
                'categories': [f"{r['origin']}_{r['destination']}", 1, 0, len(hist), 0],
                'values':     [f"{r['origin']}_{r['destination']}", 1, 1, len(hist), 1],
                'name': f"Price"
            })
            chart.set_title({'name': 'Historique prix'})
            worksheet.insert_chart('D2', chart)

# -----------------------------
# EXPORT PDF
# -----------------------------
def export_pdf(routes, filename="export.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for r in routes:
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"Suivi {r['origin']} → {r['destination']} (ID {r['id'][:8]})", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 6,
            f"Dates: {r.get('departure')} → {r.get('return')}\n"
            f"Classe: {r.get('cabin_class')}\n"
            f"Direct only: {r.get('direct_only')}\n"
            f"Min bags: {r.get('min_bags')}\n"
            f"Target price: {r.get('target_price')} €\n"
            f"Email: {r.get('email') or '—'}"
        )
        pdf.ln(5)

        # Graphique historique
        hist = r.get("history", [])
        if hist:
            dates = [datetime.fromisoformat(h["date"]) for h in hist]
            prices = [h["price"] for h in hist]
            fig, ax = plt.subplots()
            ax.plot(dates, prices, marker='o')
            ax.set_title(f"Historique prix {r['origin']}→{r['destination']}")
            ax.set_xlabel("Date")
            ax.set_ylabel("Prix (€)")
            plt.tight_layout()
            # Sauvegarde dans buffer
            buf = BytesIO()
            plt.savefig(buf, format='png')
            plt.close(fig)
            buf.seek(0)
            pdf.image(buf, x=10, w=pdf.w - 20)
        pdf.ln(10)

    pdf.output(filename)
