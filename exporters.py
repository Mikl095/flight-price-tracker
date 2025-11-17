import pandas as pd
from reportlab.pdfgen import canvas
from datetime import datetime

def export_csv(routes, path="export.csv"):
    rows = []
    for r in routes:
        last_price = r.get("history")[-1]["price"] if r.get("history") else None
        rows.append({
            "origin": r.get("origin"),
            "destination": r.get("destination"),
            "departure": r.get("departure"),
            "return": r.get("return"),
            "last_price": last_price,
            "target_price": r.get("target_price"),
            "notifications": r.get("notifications"),
            "email": r.get("email")
        })
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    return path

def export_pdf(routes, path="export.pdf"):
    c = canvas.Canvas(path)
    c.setFont("Helvetica", 10)
    c.drawString(40, 810, f"Flight Tracker export - {datetime.now().isoformat()}")
    y = 790
    for r in routes:
        last_price = r.get("history")[-1]["price"] if r.get("history") else "-"
        line = f"{r.get('origin')} -> {r.get('destination')} | dep:{r.get('departure')} | price:{last_price} | target:{r.get('target_price')}"
        c.drawString(40, y, line)
        y -= 14
        if y < 60:
            c.showPage()
            y = 800
    c.save()
    return path
