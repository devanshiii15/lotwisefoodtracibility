"""
Generate a simple downloadable recall report PDF using reportlab.

Contains: Contaminated Lot, Supplier, Affected Batches, Shipments, Summary,
and a Timestamp.
"""

import io
from datetime import datetime
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BLUE = colors.HexColor("#2563eb")
GREEN = colors.HexColor("#16a34a")
LIGHT = colors.HexColor("#eff6ff")


def build_recall_pdf(trace: Dict[str, Any]) -> bytes:
    """Return the PDF as raw bytes given a trace result from utils.trace."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm,
        leftMargin=18 * mm, rightMargin=18 * mm,
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "LWTitle", parent=styles["Title"], textColor=BLUE, fontSize=22
    )
    h2 = ParagraphStyle(
        "LWH2", parent=styles["Heading2"], textColor=GREEN, fontSize=13,
        spaceBefore=10, spaceAfter=4,
    )
    body = styles["BodyText"]

    lot = trace.get("lot", {})
    supplier = trace.get("supplier", {})
    batches = trace.get("batches", [])
    shipments = trace.get("shipments", [])

    story = []
    story.append(Paragraph("LotWise Recall Report", title))
    story.append(
        Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body
        )
    )
    story.append(Spacer(1, 8))

    # --- Key facts table ---
    story.append(Paragraph("Incident Overview", h2))
    fact_rows = [
        ["Contaminated Lot", trace.get("lot_id", "-")],
        ["Ingredient", trace.get("ingredient", "-")],
        ["Supplier", f"{supplier.get('name', '-')} ({supplier.get('supplier_id', '-')})"],
        ["Supplier Location", f"{supplier.get('city', '-')}, {supplier.get('country', '-')}"],
        ["Status", "CONTAMINATED" if trace.get("contaminated") else "Under review"],
        ["Affected Batches", str(len(batches))],
        ["Shipments to Recall", str(len(shipments))],
    ]
    t = Table(fact_rows, colWidths=[55 * mm, 110 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), LIGHT),
                ("TEXTCOLOR", (0, 0), (0, -1), BLUE),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t)

    # --- Affected batches ---
    story.append(Paragraph("Affected Batches", h2))
    if batches:
        rows = [["Batch", "Product", "Facility", "Produced"]]
        for b in batches:
            rows.append([
                b.get("batch_id", "-"),
                b.get("product_name", "-"),
                b.get("facility", "-"),
                b.get("production_date", "-"),
            ])
        story.append(_grid(rows))
    else:
        story.append(Paragraph("No batches found for this lot.", body))

    # --- Shipments ---
    story.append(Paragraph("Shipments to Recall", h2))
    if shipments:
        rows = [["Shipment", "Distributor", "Destination", "Shipped"]]
        for s in shipments:
            rows.append([
                s.get("shipment_id", "-"),
                s.get("distributor", "-"),
                s.get("destination", "-"),
                s.get("ship_date", "-"),
            ])
        story.append(_grid(rows))
    else:
        story.append(Paragraph("No shipments found for the affected batches.", body))

    # --- Summary ---
    story.append(Paragraph("Recall Summary", h2))
    story.append(Paragraph(trace.get("summary", "No summary available."), body))

    doc.build(story)
    buf.seek(0)
    return buf.read()


def _grid(rows):
    table = Table(rows, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table
