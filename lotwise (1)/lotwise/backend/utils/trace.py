"""
Contamination trace.

Given a contaminated lot, walk the supply chain deterministically using SQLite:

    Lot -> Supplier -> Ingredient -> Batches -> Shipments -> Recall Summary

This is a *structured* traversal (not RAG) because we want exact, reproducible
relationships. The LLM is only used to phrase the final recall summary nicely.
"""

from typing import Any, Dict

from utils import db
from utils.llm import complete


def trace_lot(lot_id: str) -> Dict[str, Any]:
    """Run the full trace for a lot id and return a structured result."""
    lot_id = lot_id.strip().upper()
    lot = db.get_lot(lot_id)
    if not lot:
        return {"found": False, "lot_id": lot_id, "message": f"Lot {lot_id} not found."}

    supplier = db.get_supplier(lot["supplier_id"]) or {}
    batches = db.get_batches_for_lot(lot_id)
    batch_ids = [b["batch_id"] for b in batches]
    shipments = db.get_shipments_for_batches(batch_ids)
    lab_reports = db.get_lab_reports_for_lot(lot_id)
    contaminated = any(r["status"] == "Contaminated" for r in lab_reports)

    # Ordered steps shown in the UI as text + a flowchart
    steps = [
        {"step": "Contaminated Lot", "detail": f"{lot_id} ({lot['ingredient']})"},
        {
            "step": "Supplier",
            "detail": f"{supplier.get('name', 'Unknown')} "
            f"({supplier.get('supplier_id', '?')}, "
            f"{supplier.get('city', '?')})",
        },
        {"step": "Ingredient", "detail": lot["ingredient"]},
        {
            "step": "Batches",
            "detail": ", ".join(batch_ids) if batch_ids else "None",
        },
        {
            "step": "Shipments",
            "detail": ", ".join(s["shipment_id"] for s in shipments)
            if shipments
            else "None",
        },
    ]

    summary = _generate_summary(
        lot, supplier, batches, shipments, lab_reports, contaminated
    )

    return {
        "found": True,
        "lot_id": lot_id,
        "contaminated": contaminated,
        "lot": lot,
        "supplier": supplier,
        "ingredient": lot["ingredient"],
        "batches": batches,
        "shipments": shipments,
        "lab_reports": lab_reports,
        "steps": steps,
        "summary": summary,
    }


def _generate_summary(lot, supplier, batches, shipments, lab_reports, contaminated) -> str:
    """Use the LLM to write a short recall summary from the traced facts."""
    facts = (
        f"Lot: {lot['lot_id']} | Ingredient: {lot['ingredient']} | "
        f"Supplier: {supplier.get('name', 'Unknown')} "
        f"({supplier.get('city', '?')}, {supplier.get('country', '?')}) | "
        f"Affected batches: {', '.join(b['batch_id'] for b in batches) or 'none'} | "
        f"Shipments to recall: {', '.join(s['shipment_id'] for s in shipments) or 'none'} | "
        f"Destinations: {', '.join(sorted({s['destination'] for s in shipments})) or 'none'} | "
        f"Lab status: {'CONTAMINATED' if contaminated else 'no positive result on record'}"
    )
    prompt = (
        "Write a short (4-6 sentence) food recall summary for a traceability "
        "officer. Be factual and use ONLY these traced facts. Mention the lot, "
        "supplier, affected batches, and where the product was shipped.\n\n"
        f"Facts:\n{facts}\n\nRecall summary:"
    )
    return complete(prompt)
