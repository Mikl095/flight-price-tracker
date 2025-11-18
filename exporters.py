# exporters.py
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from fpdf import FPDF
from datetime import datetime
import tempfile
import os

# -----------------------------
# EXPORT CSV -> retourne (bytes, filename)
# -----------------------------
def export_csv(routes, filename=None):
    if filename is None:
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

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
                "Price": h.get("price"),
                "DateTracked": h.get("date")
            })
    df = pd.DataFrame(rows)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    return csv_bytes, filename

# -----------------------------
# EXPORT XLSX -> retourne (bytes, filename)
# -----------------------------
def export_xlsx(routes, filename=None):
    if filename is None:
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    output = BytesIO()
    # Use pandas + xlsxwriter to write to BytesIO
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book
        for r in routes:
            sheet_name = f"{r.get('origin','X')}-{r.get('destination','Y')}"
            sheet_name = sheet_name[:31]  # sheet name limit
            hist = pd.DataFrame(r.get("history", []))
            if hist.empty:
                hist = pd.DataFrame(columns=["date", "price"])
            hist.to_excel(writer, sheet_name=sheet_name, index=False)

            # Add chart
            worksheet = writer.sheets[sheet_name]
            chart = workbook.add_chart({'type': 'line'})
            nrows = len(hist)
            if nrows >= 1:
                chart.add_series({
                    'name': 'Price',
                    'categories': [sheet_name, 1, 0, nrows, 0],
                    'values':     [sheet_name, 1, 1, nrows, 1],
                })
                chart.set_title({'name': 'Historique prix'})
                worksheet.insert_chart('D2', chart)

    output.seek(0)
    data = output.read()
    return data, filename

# -----------------------------
# EXPORT PDF -> retourne (bytes, filename)
# -----------------------------
def export_pdf(routes, filename=None):
    if filename is None:
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for r in routes:
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"Suivi {r.get('origin')} → {r.get('destination')} (ID {r.get('id')[:8]})", ln=True)
        pdf.set_font("Arial", "", 11)
        txt = (
            f"Dates: {r.get('departure')} → {r.get('return')}\n"
            f"Aéroport retour: {r.get('return_airport') or '—'}\n"
            f"Classe: {r.get('cabin_class')}\n"
            f"Direct only: {r.get('direct_only')}\n"
            f"Min bags: {r.get('min_bags')}\n"
            f"Target price: {r.get('target_price')} €\n"
            f"Email: {r.get('email') or '—'}\n"
        )
        pdf.multi_cell(0, 6, txt)
        pdf.ln(4)

        # Graphique historique (matplotlib -> image temporaire -> insert)
        hist = r.get("history", [])
        if hist:
            dates = []
            prices = []
            for h in hist:
                try:
                    from datetime import datetime as _dt
                    dates.append(_dt.fromisoformat(h.get("date")))
                    prices.append(h.get("price"))
                except Exception:
                    continue
            if dates and prices:
                fig, ax = plt.subplots(figsize=(6,2.5))
                ax.plot(dates, prices, marker='o', linewidth=1)
                ax.set_title(f"Historique prix {r.get('origin')}→{r.get('destination')}")
                ax.set_xlabel("Date")
                ax.set_ylabel("Prix (€)")
                fig.autofmt_xdate()
                plt.tight_layout()

                buf = BytesIO()
                fig.savefig(buf, format="PNG")
                plt.close(fig)
                buf.seek(0)

                # write to temp file because FPDF.image expects a file path for reliability
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpf:
                    tmpf.write(buf.getvalue())
                    tmp_path = tmpf.name
                try:
                    pdf.image(tmp_path, x=10, w=pdf.w - 20)
                except Exception:
                    # ignore image errors
                    pass
                finally:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
                pdf.ln(6)

    # get PDF bytes (S mode)
    try:
        out = pdf.output(dest='S')
        if isinstance(out, bytes):
            pdf_bytes = out
        else:
            # output may return str in some versions
            pdf_bytes = out.encode('latin-1')
    except TypeError:
        # older/newer variants
        out = pdf.output(dest='S')
        pdf_bytes = out.encode('latin-1') if isinstance(out, str) else out

    return pdf_bytes, filename
