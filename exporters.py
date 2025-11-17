import pandas as pd
from reportlab.pdfgen import canvas

def export_csv(routes):
    df = pd.DataFrame(routes)
    df.to_csv("export.csv", index=False)
    return "export.csv"

def export_pdf(routes):
    file = "export.pdf"
    c = canvas.Canvas(file)
    c.drawString(50, 800, "Flight Tracker Export")
    y = 760
    for r in routes:
        txt = f"{r['origin']} -> {r['destination']} | {r['departure']} | prix: {r['history'][-1]['price'] if r['history'] else '-'}"
        c.drawString(50, y, txt)
        y -= 20
    c.save()
    return file
