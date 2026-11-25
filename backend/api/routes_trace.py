"""Contamination trace endpoints + PDF recall report + supply-chain graph."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from utils import db, trace as trace_util
from utils.pdf_report import build_recall_pdf

router = APIRouter(prefix="/api", tags=["trace"])


class TraceRequest(BaseModel):
    lot_id: str


@router.post("/trace")
def trace(req: TraceRequest):
    """Run the deterministic contamination trace for a lot id."""
    result = trace_util.trace_lot(req.lot_id)
    if not result.get("found"):
        raise HTTPException(status_code=404, detail=result.get("message", "Not found"))
    return result


@router.get("/trace/{lot_id}/report")
def download_report(lot_id: str):
    """Generate and return a recall report PDF for a lot."""
    result = trace_util.trace_lot(lot_id)
    if not result.get("found"):
        raise HTTPException(status_code=404, detail=f"Lot {lot_id} not found.")
    pdf_bytes = build_recall_pdf(result)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="recall_{lot_id.upper()}.pdf"'
        },
    )


@router.get("/graph/{lot_id}")
def supply_chain_graph(lot_id: str):
    """
    Return nodes + edges for the React Flow supply-chain visualization:
        Supplier -> Lot -> Batch -> Shipment
    """
    result = trace_util.trace_lot(lot_id)
    if not result.get("found"):
        raise HTTPException(status_code=404, detail=f"Lot {lot_id} not found.")

    supplier = result["supplier"]
    lot = result["lot"]
    batches = result["batches"]
    shipments = result["shipments"]

    nodes = []
    edges = []

    # Supplier node
    sup_id = f"sup-{supplier.get('supplier_id', 'unknown')}"
    nodes.append({
        "id": sup_id,
        "type": "supplier",
        "label": supplier.get("name", "Supplier"),
        "sublabel": supplier.get("supplier_id", ""),
    })

    # Lot node
    lot_node_id = f"lot-{lot['lot_id']}"
    nodes.append({
        "id": lot_node_id,
        "type": "lot",
        "label": lot["lot_id"],
        "sublabel": lot["ingredient"],
    })
    edges.append({"id": f"{sup_id}-{lot_node_id}", "source": sup_id, "target": lot_node_id})

    # Batch + shipment nodes
    shipments_by_batch = {}
    for s in shipments:
        shipments_by_batch.setdefault(s["batch_id"], []).append(s)

    for b in batches:
        b_id = f"batch-{b['batch_id']}"
        nodes.append({
            "id": b_id,
            "type": "batch",
            "label": b["batch_id"],
            "sublabel": b["product_name"],
        })
        edges.append({"id": f"{lot_node_id}-{b_id}", "source": lot_node_id, "target": b_id})

        for s in shipments_by_batch.get(b["batch_id"], []):
            s_id = f"ship-{s['shipment_id']}"
            nodes.append({
                "id": s_id,
                "type": "shipment",
                "label": s["shipment_id"],
                "sublabel": s["destination"],
            })
            edges.append({"id": f"{b_id}-{s_id}", "source": b_id, "target": s_id})

    return {"lot_id": lot["lot_id"], "contaminated": result["contaminated"],
            "nodes": nodes, "edges": edges}
