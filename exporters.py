# exporters.py
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from fpdf import FPDF
from datetime import datetime
import xlsxwriter  # utilisé implicitement par pandas ExcelWriter

# -----------------------------
# EXPORT CSV -> retourne (bytes, filename)
# -----------------------------
def export_csv(routes, filename=None):
    """
    Retourne (bytes_content, filename)
    - routes : list de dict
    - filename : optionnel, si None on génère un nom
    """
    if filename is None:
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    # construire dataframe "long" : 1 ligne par entrée d'historique
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
    csv_str = df.to_csv(index=False)
    return csv_str.encode("utf-8"), filename

# -----------------------------
# EXPORT XLSX -> retourne (bytes, filename)
# -----------------------------
def export_xlsx(routes, filename=None):
    if filename is None:
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    output = BytesIO()
    # pandas + xlsxwriter to BytesIO
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book
        for r in routes:
            sheet_name = f"{r.get('origin','X')}-{r.get('destination','Y')}"
            # sheet names must be <=31 chars
            sheet_name = sheet_name[:31]
            hist = pd.DataFrame(r.get("history", []))
            if hist.empty:
                hist = pd.DataFrame(columns=["date", "price"])
            # write history table
            hist.to_excel(writer, sheet_name=sheet_name, index=False)

            # add a chart for this sheet
            worksheet = writer.sheets[sheet_name]
            chart = workbook.add_chart({'type': 'line'})

            # compute range bounds: header row + data rows
            nrows = len(hist)
            if nrows >= 1:
                # categories: col A (date), values: col B (price)
                chart.add_series({
                    'name':       'Price',
                    'categories': [sheet_name, 1, 0, nrows, 0],
                    'values':     [sheet_name, 1, 1, nrows, 1],
                })
                chart.set_title({'name': 'Historique prix'})
                worksheet.insert_chart('D2', chart)

    # get bytes
    output.seek(0)
    data = output.read()
    return data, filename

# -----------------------------
# EXPORT PDF -> retourne (bytes, filename)
# -----------------------------
def export_pdf(routes, filename=None):
    if filename is None:
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    # Nous allons créer un PDF en mémoire puis renvoyer ses bytes
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
        # écrire le texte descriptif
        pdf.multi_cell(0, 6, txt)
        pdf.ln(4)

        # Graphique historique : si on a des points
        hist = r.get("history", [])
        if hist:
            dates = []
            prices = []
            for h in hist:
                try:
                    # robust to iso-like strings
                    from datetime import datetime as _dt
                    dates.append(_dt.fromisoformat(h.get("date")))
                    prices.append(h.get("price"))
                except Exception:
                    continue
            if dates and prices:
                # tracer avec matplotlib et insérer l'image
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
                # FPDF.image accepte un path ou un object file-like si on convertit en temporary file.
                # FPDF.image does not accept BytesIO directly reliably, donc on insère via temporary file in-memory:
                # FPDF has image() that can accept a file-like if pillow is used, but for compatibilité on écrira l'image en mémoire temporaire:
                # On peut utiliser image from BytesIO with Pillow to get a temp file path. Simpler : use pdf.image with BytesIO via pillow is not guaranteed.
                # Ici on use FPDF.image with argument as BytesIO by saving to a temp file-like via NamedTemporaryFile.
                try:
                    # write bytes to a temporary in-memory file using Python tempfile
                    import tempfile, os
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpf:
                        tmpf.write(buf.getvalue())
                        tmp_path = tmpf.name
                    # insert image and remove temp file afterwards
                    pdf.image(tmp_path, x=10, w=pdf.w - 20)
                    os.unlink(tmp_path)
                except Exception:
                    # fallback: ignore image if insertion échoue
                    pass
                pdf.ln(6)

    # produce PDF bytes via output(dest='S')
    try:
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
    except TypeError:
        # some versions already return bytes/str
        out = pdf.output(dest='S')
        if isinstance(out, bytes):
            pdf_bytes = out
        else:
            pdf_bytes = out.encode('latin-1')

    return pdf_bytes, filename
