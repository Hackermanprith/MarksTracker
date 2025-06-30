import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def df_to_pdf(df, path='export.pdf'):
    c = canvas.Canvas(path, pagesize=letter)
    w, h = letter; x=50; y=h-50
    rows = [df.columns.tolist()] + df.values.tolist()
    line_height = 14
    for row in rows:
        txt = "".join(str(v).ljust(15) for v in row)
        c.drawString(x, y, txt)
        y -= line_height
        if y < 50:
            c.showPage(); y = h - 50
    c.save()
