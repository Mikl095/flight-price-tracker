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

    def _sanitize_for_fpdf(s: str) -> str:
        """Replace known unicode chars by safe ascii/latin1 equivalents, then
           ensure resulting str is encodable in latin-1 by replacing remaining
           non-encodable chars."""
        if s is None:
            return ""
        # common replacements
        repl = {
            "→": "->",
            "–": "-",
            "—": "-",
            "…": "...",
            "€": "EUR",
            "“": '"',
            "”": '"',
            "‘": "'",
            "’": "'",
            "\u2014": "-",
        }
        for k, v in repl.items():
            s = s.replace(k, v)
        # finally, force latin-1 encoding with replacement for any remaining char
        try:
            s.encode("latin-1")
            return s
        except UnicodeEncodeError:
            # replace non-latin1 with '?'
            return s.encode("latin-1", errors="replace").decode("latin-1")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for r in routes:
        pdf.add_page()
        # title
        title = f"Suivi {r.get('origin')} -> {r.get('destination')} (ID {r.get('id')[:8]})"
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, _sanitize_for_fpdf(title), ln=True)

        pdf.set_font("Arial", "", 11)
        txt = (
            f"Dates: {r.get('departure')} -> {r.get('return')}\n"
            f"Aéroport retour: {r.get('return_airport') or '—'}\n"
            f"Classe: {r.get('cabin_class')}\n"
            f"Direct only: {r.get('direct_only')}\n"
            f"Min bags: {r.get('min_bags')}\n"
            f"Target price: {r.get('target_price')} EUR\n"
            f"Email: {r.get('email') or '—'}\n"
        )
        pdf.multi_cell(0, 6, _sanitize_for_fpdf(txt))
        pdf.ln(4)

        # Graphique historique
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
                ax.set_title(_sanitize_for_fpdf(f"Historique prix {r.get('origin')}->{r.get('destination')}"))
                ax.set_xlabel("Date")
                ax.set_ylabel("Prix (EUR)")
                fig.autofmt_xdate()
                plt.tight_layout()

                buf = BytesIO()
                fig.savefig(buf, format="PNG")
                plt.close(fig)
                buf.seek(0)

                # write to temp file because FPDF.image expects a file path reliably
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpf:
                        tmpf.write(buf.getvalue())
                        tmp_path = tmpf.name
                    pdf.image(tmp_path, x=10, w=pdf.w - 20)
                except Exception:
                    # ignore image insertion errors
                    pass
                finally:
                    try:
                        if 'tmp_path' in locals() and os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                    except Exception:
                        pass
                pdf.ln(6)

    # output bytes (S)
    try:
        out = pdf.output(dest='S')
        if isinstance(out, bytes):
            pdf_bytes = out
        else:
            # out is str -> encode safely using latin-1 with replacement
            pdf_bytes = out.encode('latin-1', errors='replace')
    except Exception:
        # fallback: try to get str and encode
        out = pdf.output(dest='S')
        pdf_bytes = out.encode('latin-1', errors='replace') if isinstance(out, str) else out

    return pdf_bytes, filename

