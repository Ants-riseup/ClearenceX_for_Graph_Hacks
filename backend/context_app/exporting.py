from database.models import DeclarationMetadata, CusdecLineItem
from reasoning.cusdec_readiness import build_cusdec_readiness
from .graph import fields


def metadata(db, sid):
    return {r.field_name: r.value for r in db.query(DeclarationMetadata).filter_by(shipment_id=sid)}


def line_items(db, sid):
    return [{"row_index": r.row_index, "description": r.description, "quantity": r.quantity,
        "unit": r.unit, "unit_price": r.unit_price, "total_price": r.total_price,
        "source_reference": r.source_reference, "verified_by": r.verified_by}
        for r in db.query(CusdecLineItem).filter_by(shipment_id=sid).order_by(CusdecLineItem.row_index)]


def readiness(db, row):
    result = build_cusdec_readiness(row.state.get("documents", []), fields(row.state, row.id),
        metadata(db, row.id), line_items(db, row.id))
    extra = []
    if row.revision != row.graph_revision:
        extra.append({"code": "CONTEXT_PENDING", "field": "context", "message": "Wait for graph synchronization.", "source": "context"})
    current = {d["field_id"] for d in row.state["decisions"] if d["validity_state"] == "current" and d["status"] == "approved"}
    stale = {d["field_id"] for d in row.state["decisions"] if d["validity_state"] == "stale"} - current
    for field_id in stale:
        extra.append({"code": "STALE_APPROVAL", "field": field_id, "message": "A supporting source changed. Review again.", "source": "context"})
    result["blockers"].extend(extra)
    result["blocker_count"] = len(result["blockers"])
    result["export_allowed"] = not result["blockers"]
    result["status"] = "ready" if result["export_allowed"] else "blocked"
    result["revision"] = row.revision
    result["notice"] = "Template-based XML preparation; official ASYCUDA acceptance has not been verified."
    return result
