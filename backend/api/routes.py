# backend/api/routes.py
#
# Existing dossier screens backed by authorized persisted context.
# Historical fixture helpers below are unreachable from the active resolver.

from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import Response
from typing import List
import uuid, os, dataclasses, logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


# ══════════════════════════════════════════════════════════════════
# HELPERS — Data Resolution (DB vs Demo)
# ══════════════════════════════════════════════════════════════════

DEMO_IDS = {"demo-shipment", "demo"}

DOCUMENT_LABELS = {
    "commercial_invoice": "Commercial Invoice",
    "packing_list": "Packing List",
    "awb": "Air Waybill",
    "bl": "Bill of Lading",
    "freight_invoice": "Freight Invoice",
    "delivery_order": "Delivery Order",
}


def _document_label(document_type: str) -> str:
    return DOCUMENT_LABELS.get(document_type, document_type.replace("_", " ").title())


def _is_demo(shipment_id: str) -> bool:
    """Return True for known demo/test fixture IDs."""
    return shipment_id in DEMO_IDS


def _fetch_dossier_documents(shipment_id: str):
    """
    Query PostgreSQL for completed extraction results for a real dossier.

    Returns:
        list[dict] — pipeline result dicts (one per document), or
        None       — if dossier not found, not yet done, or DB unavailable.
    """
    try:
        from database.connection import SessionLocal
        from database.models import DossierDocument, Dossier
        import uuid as _uuid

        try:
            dossier_uuid = _uuid.UUID(shipment_id)
        except ValueError:
            return None

        db = SessionLocal()
        try:
            dossier = db.query(Dossier).filter(Dossier.id == dossier_uuid).first()
            if dossier is None:
                return None

            docs = (
                db.query(DossierDocument)
                .filter(
                    DossierDocument.dossier_id == dossier_uuid,
                    DossierDocument.status == "done",
                )
                .order_by(DossierDocument.created_at)
                .all()
            )
            if not docs:
                return None

            results = []
            for doc in docs:
                extraction = doc.extraction_json
                if extraction is None:
                    continue
                if isinstance(extraction, str):
                    import json as _json
                    extraction = _json.loads(extraction)
                if not isinstance(extraction, dict):
                    continue
                if "document_id" not in extraction:
                    extraction["document_id"] = str(doc.id)
                extraction["document_type"] = (
                    doc.document_type or extraction.get("document_type", "unknown")
                )
                extraction["source_filename"] = doc.original_name
                type_label = _document_label(extraction["document_type"])
                extraction["source_label"] = f"{type_label} — {doc.original_name}"
                results.append(extraction)

            return results if results else None
        finally:
            db.close()
    except Exception as exc:
        logger.warning("_fetch_dossier_documents(%s): %s", shipment_id, exc)
        return None


def _get_demo_documents() -> list:
    """Run MockPipeline on the three demo PDFs."""
    from ai_pipeline.mock_pipeline import MockPipeline

    mp = MockPipeline()
    demo_docs = [
        ("demo/commercial_invoice.pdf", "doc_001"),
        ("demo/packing_list.pdf",       "doc_002"),
        ("demo/awb.pdf",                "doc_003"),
    ]
    results = []
    for path, doc_id in demo_docs:
        document = mp.process_document(path, doc_id)
        document["source_filename"] = os.path.basename(path)
        document["source_label"] = _document_label(document["document_type"])
        results.append(document)
    return results


def _get_documents_for_shipment(shipment_id: str) -> list:
    from database.connection import SessionLocal
    from context_app.models import ContextDossier
    with SessionLocal() as db:
        context = db.get(ContextDossier, shipment_id)
        return context.state.get("documents", []) if context else []


def _get_field_resolutions(shipment_id: str) -> dict:
    from database.connection import SessionLocal
    from context_app.models import ContextDossier
    with SessionLocal() as db:
        row = db.get(ContextDossier, shipment_id)
        return {d["field_id"]: {"resolved_value": d["value"], "source_assertion_id": d["assertion_id"],
            "reason": d["reason"], "resolved_by": d["actor_id"]} for d in row.state.get("decisions", [])
            if d["status"] == "approved" and d["validity_state"] == "current"} if row else {}


def _get_declaration_metadata(shipment_id: str) -> dict:
    """Load reviewer-supplied Customs/profile details for the active dossier."""
    try:
        from database.connection import SessionLocal
        from database.models import DeclarationMetadata

        db = SessionLocal()
        try:
            rows = db.query(DeclarationMetadata).filter(
                DeclarationMetadata.shipment_id == shipment_id
            ).all()
            return {row.field_name: row.value for row in rows if row.value not in (None, "")}
        finally:
            db.close()
    except Exception as exc:
        logger.warning("Could not load declaration metadata for %s: %s", shipment_id, exc)
        return {}


def _get_verified_line_items(shipment_id: str) -> list[dict]:
    """Load reviewer-entered goods rows and their source references."""
    try:
        from database.connection import SessionLocal
        from database.models import CusdecLineItem

        db = SessionLocal()
        try:
            rows = db.query(CusdecLineItem).filter(
                CusdecLineItem.shipment_id == shipment_id
            ).order_by(CusdecLineItem.row_index).all()
            return [{
                "row_index": row.row_index,
                "description": row.description,
                "quantity": row.quantity,
                "unit": row.unit,
                "unit_price": row.unit_price,
                "total_price": row.total_price,
                "source_reference": row.source_reference,
                "verified_by": row.verified_by,
            } for row in rows]
        finally:
            db.close()
    except Exception as exc:
        logger.warning("Could not load verified line items for %s: %s", shipment_id, exc)
        return []


def _resolve_shipment_fields(shipment_id: str, documents: list) -> list:
    """Resolve source assertions, then apply persisted reviewer decisions."""
    from context_app.models import ContextDossier
    from context_app.graph import fields
    from database.connection import SessionLocal
    with SessionLocal() as db:
        row = db.get(ContextDossier, shipment_id)
        if not row:
            raise HTTPException(404, 'Dossier not found.')
        return fields(row.state, shipment_id)


# ══════════════════════════════════════════════════════════════════
# HELPERS — Knowledge Graph Building
# ══════════════════════════════════════════════════════════════════

def _build_graph_from_documents(shipment_id: str, documents: list):
    """
    Generic graph builder: works with any list of pipeline result dicts.
    Resolves source entities into canonical shipment fields. Each raw value is
    retained as a source assertion, rather than being overwritten by a merge.

    Returns (KnowledgeBuilder, documents).
    """
    from reasoning.knowledge_builder import KnowledgeBuilder

    kb = KnowledgeBuilder()
    kb.add_shipment_node(shipment_id)

    for doc in documents:
        kb.add_document_node(doc["document_id"], doc.get("document_type", "unknown"))

    for field in _resolve_shipment_fields(shipment_id, documents):
        kb.add_canonical_field_node(field, shipment_id)
        for assertion in field["assertions"]:
            kb.add_source_assertion_node(assertion)

    return kb, documents


def _build_demo_graph(shipment_id: str):
    """
    Demo-specific graph builder: runs MockPipeline on demo PDFs and builds
    a curated knowledge graph with specific MUST_MATCH edges.
    Preserved for backward compatibility with the demo scenario.
    """
    from ai_pipeline.mock_pipeline import MockPipeline
    from reasoning.knowledge_builder import KnowledgeBuilder
    from xai_types import ExtractedEntity

    mp = MockPipeline()
    demo_docs = [
        ("demo/commercial_invoice.pdf", "doc_001"),
        ("demo/packing_list.pdf",       "doc_002"),
        ("demo/awb.pdf",                "doc_003"),
    ]
    documents = [mp.process_document(path, doc_id) for path, doc_id in demo_docs]

    kb = KnowledgeBuilder()
    for doc in documents:
        kb.add_document_node(doc["document_id"], doc["document_type"])

    def to_entity(e: dict) -> ExtractedEntity:
        return ExtractedEntity(
            entity_type=e["entity_type"],
            value=e["value"],
            normalized_value=e.get("normalized_value", e["value"]),
            unit=e.get("unit"),
            page=e.get("page", 1),
            bbox=e.get("bbox", []),
            extraction_confidence=e.get("extraction_confidence", 0.9),
            ocr_text=e.get("value", ""),
        )

    # GROSS_WEIGHT: invoice vs packing list vs AWB
    inv_gw = next((e for e in documents[0]["entities"] if e["entity_type"] == "GROSS_WEIGHT"), None)
    awb_gw = next((e for e in documents[2]["entities"] if e["entity_type"] == "GROSS_WEIGHT"), None)
    pl_gw  = next((e for e in documents[1]["entities"] if e["entity_type"] == "GROSS_WEIGHT"), None)

    if inv_gw:
        kb.add_entity_node("n_inv_gw", to_entity(inv_gw), "doc_001")
    if awb_gw:
        kb.add_entity_node("n_awb_gw", to_entity(awb_gw), "doc_003")
    if pl_gw:
        kb.add_entity_node("n_pl_gw",  to_entity(pl_gw),  "doc_002")

    if inv_gw and awb_gw:
        kb.add_relationship("n_inv_gw", "n_awb_gw", "MUST_MATCH")
    if inv_gw and pl_gw:
        kb.add_relationship("n_inv_gw", "n_pl_gw", "MUST_MATCH")

    # CONSIGNEE_NAME: invoice vs AWB
    inv_cn = next((e for e in documents[0]["entities"] if e["entity_type"] == "CONSIGNEE_NAME"), None)
    awb_cn = next((e for e in documents[2]["entities"] if e["entity_type"] == "CONSIGNEE_NAME"), None)

    if inv_cn:
        kb.add_entity_node("n_inv_cn", to_entity(inv_cn), "doc_001")
    if awb_cn:
        kb.add_entity_node("n_awb_cn", to_entity(awb_cn), "doc_003")
    if inv_cn and awb_cn:
        kb.add_relationship("n_inv_cn", "n_awb_cn", "MUST_MATCH")

    return kb, documents


def _get_graph_for_shipment(shipment_id: str):
    """
    Smart graph router:
    Always uses real DB data. Never falls back to demo.
    """
    return _build_graph_from_documents(shipment_id, _get_documents_for_shipment(shipment_id))


# ══════════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════════


@router.post("/shipments/upload")
async def upload_shipment(files: List[UploadFile] = File(...)):
    raise HTTPException(410, "Use POST /api/upload; legacy uploads are disabled.")


@router.get("/shipments/{shipment_id}/status")
async def get_shipment_status(shipment_id: str):
    from database.connection import SessionLocal
    from database.models import Dossier, DossierDocument
    documents = _get_documents_for_shipment(shipment_id)
    if documents:
        return {"shipment_id": shipment_id, "status": "completed", "progress": 100,
            "documents": [{"document_id": d["document_id"], "filename": d.get("source_filename", "document.pdf"),
                "document_type": d["document_type"], "status": "done"} for d in documents]}
    with SessionLocal() as db:
        row = db.get(Dossier, uuid.UUID(shipment_id))
        if not row:
            raise HTTPException(404, "Dossier not found.")
        docs = db.query(DossierDocument).filter_by(dossier_id=row.id).all()
        return {"shipment_id": shipment_id, "status": row.status,
            "progress": round(100 * sum(d.status == "done" for d in docs) / max(1, len(docs))),
            "documents": [{"document_id": str(d.id), "filename": d.original_name,
                "status": d.status, "error_message": d.error_message} for d in docs]}


@router.get("/shipments/{shipment_id}/extraction")
async def get_extraction(shipment_id: str):
    documents = _get_documents_for_shipment(shipment_id)
    return {"shipment_id": shipment_id, "documents": documents}


@router.get("/shipments/{shipment_id}/graph")
async def get_knowledge_graph(shipment_id: str):
    from context_app.graph import GraphRepository
    from context_app.models import ContextDossier
    from context_app.service import require_current
    from database.connection import SessionLocal
    import json
    with SessionLocal() as db:
        row = db.query(ContextDossier).filter_by(id=shipment_id).with_for_update().one()
        require_current(row)
        rows = GraphRepository(row.tenant_id).query("visual", shipment_id, row.revision)
        if len(rows) > 2000:
            raise HTTPException(409, "Graph too large; use focused field evidence.")
        nodes, edges, seen = {}, [], set()
        for nid, label, payload, relation, target in rows:
            data = json.loads(payload)
            nodes[nid] = {"id": nid, "label": str(data.get("label", data.get("source_filename", data.get("reason", label))))[:100],
                "type": label.lower(), "status": data.get("status", "match"), "shape": "box", "color": "#c7d2fe"}
            if relation and (nid, relation, target) not in seen:
                seen.add((nid, relation, target))
                edges.append({"from": nid, "to": target, "label": relation, "confidence": 1.0})
        return {"nodes": list(nodes.values()), "edges": edges}


@router.get("/shipments/{shipment_id}/key-fields")
async def get_key_fields(shipment_id: str):
    """Return canonical shipment fields with every document assertion."""
    fields = _resolve_shipment_fields(shipment_id, _get_documents_for_shipment(shipment_id))
    counts = {status: sum(field["status"] == status for field in fields)
              for status in ("match", "conflict", "warning", "pending", "resolved")}
    return {
        "shipment_id": shipment_id,
        "summary": {"total_fields": len(fields), **counts},
        "fields": fields,
    }


@router.post("/shipments/{shipment_id}/field-resolutions")
async def save_field_resolution(shipment_id: str, resolution: dict, request: Request):
    from context_app.service import decide
    if not resolution.get("source_assertion_id") or not isinstance(resolution.get("expected_revision"), int):
        raise HTTPException(422, "Select source evidence and supply the current expected_revision.")
    decide(shipment_id, request.state.user, str(resolution.get("canonical_field_id", "")),
        resolution["source_assertion_id"], str(resolution.get("reason", "")), resolution["expected_revision"],
        request_id=resolution.get("request_id"))
    field = next(f for f in _resolve_shipment_fields(shipment_id, _get_documents_for_shipment(shipment_id))
        if f["canonical_field_id"] == resolution["canonical_field_id"])
    return {"status": "resolved", "field": field}


@router.post("/shipments/{shipment_id}/declaration-metadata")
async def save_declaration_metadata(shipment_id: str, payload: dict, request: Request):
    """Save verified Customs/profile fields supplied by the declarant or reviewer."""
    documents = _get_documents_for_shipment(shipment_id)
    if not documents:
        raise HTTPException(status_code=404, detail="No processed documents were found for this dossier.")

    from reasoning.cusdec_readiness import PROFILE_REQUIREMENTS, build_cusdec_readiness

    values = payload.get("values")
    if not isinstance(values, dict):
        raise HTTPException(status_code=400, detail="values must be an object of declaration fields.")

    invalid = set(values) - set(PROFILE_REQUIREMENTS)
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported declaration field(s): {', '.join(sorted(invalid))}.",
        )

    cleaned = {
        key: str(value).strip()
        for key, value in values.items()
        if value is not None and str(value).strip()
    }
    if not cleaned:
        raise HTTPException(status_code=400, detail="Enter at least one declaration value to save.")
    if any(len(value) > 200 for value in cleaned.values()):
        raise HTTPException(status_code=400, detail="Declaration values must be 200 characters or fewer.")

    try:
        from database.connection import SessionLocal
        from database.models import DeclarationMetadata

        db = SessionLocal()
        try:
            from context_app.security import authorize_dossier
            from context_app.service import enqueue
            import copy
            context = authorize_dossier(db, shipment_id, request.state.user, write=True, lock=True)
            for field_name, value in cleaned.items():
                row = db.query(DeclarationMetadata).filter(
                    DeclarationMetadata.shipment_id == shipment_id,
                    DeclarationMetadata.field_name == field_name,
                ).first()
                if row is None:
                    row = DeclarationMetadata(shipment_id=shipment_id, field_name=field_name)
                    db.add(row)
                row.value = value
                row.updated_by = request.state.user["id"]
            enqueue(db, context, copy.deepcopy(context.state), request.state.user["id"], "declarationmetadata_saved")
            db.commit()
        finally:
            db.close()
    except Exception as exc:
        logger.exception("Could not save declaration metadata for %s", shipment_id)
        raise HTTPException(status_code=503, detail="The declaration details could not be saved.") from exc

    fields = _resolve_shipment_fields(shipment_id, documents)
    metadata = _get_declaration_metadata(shipment_id)
    return {
        "status": "saved",
        "profile": metadata,
        "readiness": build_cusdec_readiness(documents, fields, metadata),
    }


@router.post("/shipments/{shipment_id}/cusdec-line-items")
async def save_cusdec_line_item(shipment_id: str, item: dict, request: Request):
    """Save one source-referenced goods row when automatic table extraction is unavailable."""
    documents = _get_documents_for_shipment(shipment_id)
    if not documents:
        raise HTTPException(status_code=404, detail="No processed documents were found for this dossier.")

    description = str(item.get("description", "")).strip()
    unit = str(item.get("unit", "")).strip()
    source_reference = str(item.get("source_reference", "")).strip()
    if not description or not unit or not source_reference:
        raise HTTPException(
            status_code=400,
            detail="Description, unit, and source document reference are required.",
        )
    if len(description) > 1000 or len(unit) > 50 or len(source_reference) > 500:
        raise HTTPException(status_code=400, detail="One or more line-item values are too long.")
    try:
        quantity = float(item.get("quantity"))
        unit_price = float(item.get("unit_price"))
        total_price = float(item.get("total_price"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Quantity, unit price, and total price must be numbers.")
    import math
    if not all(math.isfinite(v) for v in (quantity, unit_price, total_price)) or quantity <= 0 or unit_price < 0 or total_price <= 0:
        raise HTTPException(status_code=400, detail="Quantity and total price must be positive; unit price cannot be negative.")
    from decimal import Decimal, ROUND_HALF_UP
    expected_total = (Decimal(str(item['quantity'])) * Decimal(str(item['unit_price']))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    supplied_total = Decimal(str(item['total_price'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    if expected_total != supplied_total:
        raise HTTPException(status_code=400, detail="Total price must equal quantity × unit price rounded to two decimals (half up).")

    try:
        from database.connection import SessionLocal
        from database.models import CusdecLineItem

        db = SessionLocal()
        try:
            from context_app.security import authorize_dossier
            from context_app.service import enqueue
            import copy
            context = authorize_dossier(db, shipment_id, request.state.user, write=True, lock=True)
            last_row = db.query(CusdecLineItem.row_index).filter(
                CusdecLineItem.shipment_id == shipment_id
            ).order_by(CusdecLineItem.row_index.desc()).first()
            row = CusdecLineItem(
                shipment_id=shipment_id,
                row_index=(last_row[0] if last_row else 0) + 1,
                description=description,
                quantity=quantity,
                unit=unit,
                unit_price=unit_price,
                total_price=total_price,
                source_reference=source_reference,
                verified_by=request.state.user["id"],
            )
            db.add(row)
            enqueue(db, context, copy.deepcopy(context.state), request.state.user["id"], "cusdeclineitem_saved")
            db.commit()
        finally:
            db.close()
    except Exception as exc:
        logger.exception("Could not save CUSDEC line item for %s", shipment_id)
        raise HTTPException(status_code=503, detail="The goods line item could not be saved.") from exc

    from reasoning.cusdec_readiness import build_cusdec_readiness
    fields = _resolve_shipment_fields(shipment_id, documents)
    return {
        "status": "saved",
        "line_items": _get_verified_line_items(shipment_id),
        "readiness": build_cusdec_readiness(
            documents,
            fields,
            _get_declaration_metadata(shipment_id),
            _get_verified_line_items(shipment_id),
        ),
    }


@router.get("/shipments/{shipment_id}/discrepancies")
async def get_discrepancies(shipment_id: str):
    from reasoning.rule_evaluator import RuleEvaluator
    from reasoning.xai_compiler import XAICompiler

    kb, documents = _get_graph_for_shipment(shipment_id)
    graph = kb.get_graph()


    evaluator = RuleEvaluator(graph)
    failures = evaluator.evaluate()

    compiler = XAICompiler(graph)
    discrepancies = []
    for f in failures:
        xai_block = compiler.compile(f)
        discrepancies.append({
            "discrepancy_id": f"{f.rule_id}_{f.node_a_id}_{f.node_b_id}",
            "field": f.entity_type,
            "field_label": f.entity_type.replace("_", " ").title(),
            "canonical_field_id": f.canonical_field_id,
            "rule_id": f.rule_id,
            "severity": "high" if "NUMERIC" in f.rule_id else "medium",
            "severity_score": round(1.0 - xai_block.layer3.overall_confidence, 4),
            "status": "open",
            "value_a": str(f.value_a),
            "value_b": str(f.value_b),
            "delta": f.delta,
            "sources": [
                {
                    "document_id": graph.nodes[node_id].get("source_doc", ""),
                    "document_label": graph.nodes[node_id].get("source_doc_label", "Unknown document"),
                    "document_type": graph.nodes[node_id].get("source_doc_type", "unknown"),
                    "raw_value": graph.nodes[node_id].get("raw_value", ""),
                    "normalized_value": graph.nodes[node_id].get("value", ""),
                    "page": graph.nodes[node_id].get("page", 1),
                    "bbox": graph.nodes[node_id].get("bbox", []),
                    "extraction_confidence": graph.nodes[node_id].get("extraction_confidence", 0.0),
                }
                for node_id in (f.node_a_id, f.node_b_id)
            ],
            "xai_block": dataclasses.asdict(xai_block),
        })

    return {
        "shipment_id": shipment_id,
        "total_discrepancies": len(discrepancies),
        "discrepancies": discrepancies,
    }


@router.get("/shipments/{shipment_id}/audit-trail")
async def get_audit_trail(shipment_id: str):
    from context_app.models import ContextDossier
    from database.connection import SessionLocal
    from datetime import datetime, timezone
    with SessionLocal() as db:
        row = db.get(ContextDossier, shipment_id)
        entries = [{**e, "timestamp": datetime.fromtimestamp(e["timestamp"], timezone.utc).isoformat(),
            "confidence": None, "reasoning": None} for e in row.state.get("events", [])]
        return {"shipment_id": shipment_id, "total_events": len(entries), "entries": entries}


@router.get("/shipments/{shipment_id}/asycuda-export")
async def export_asycuda(shipment_id: str, request: Request):
    """Read-only compatibility endpoint; creation now requires POST and CSRF."""
    from context_app.security import authorize_dossier
    from database.connection import SessionLocal
    with SessionLocal() as db:
        authorize_dossier(db, shipment_id, request.state.user, write=True)
    raise HTTPException(410, 'Use POST /api/shipments/{id}/exports for a versioned private snapshot.')


@router.get("/shipments/{shipment_id}/cusdec-readiness")
async def get_cusdec_readiness(shipment_id: str, request: Request):
    from context_app.exporting import readiness
    from context_app.security import authorize_dossier
    from database.connection import SessionLocal
    with SessionLocal() as db:
        row = authorize_dossier(db, shipment_id, request.state.user, lock=True)
        return {"shipment_id": shipment_id, **readiness(db, row)}


# ══════════════════════════════════════════════════════════════════
# GET /api/dossiers — overview dashboard: list all dossiers
# ══════════════════════════════════════════════════════════════════

@router.get("/dossiers")
async def list_dossiers(request: Request, search: str = "", status: str = "", offset: int = 0, limit: int = 20, sort: str = "newest"):
    from context_app.models import ContextDossier
    from database.connection import SessionLocal
    from datetime import datetime, timezone
    from sqlalchemy import case, func, String
    from database.models import Dossier, DossierDocument
    with SessionLocal() as db:
        actual = case((Dossier.id.is_not(None), Dossier.status), else_=case(
            (func.json_array_length(ContextDossier.state['documents']) > 0, 'done'), else_='pending'))
        query = db.query(ContextDossier, actual.label('processing_status')).outerjoin(
            Dossier, ContextDossier.id == Dossier.id.cast(String)).filter(ContextDossier.tenant_id == request.state.user['tenant_id'])
        if search:
            query = query.filter(ContextDossier.title.ilike("%" + search[:100] + "%"))
        if status:
            if status not in {'done', 'pending', 'processing', 'error', 'interrupted'}:
                raise HTTPException(422, 'Unknown processing status.')
            query = query.filter(actual == status)
        ordering = {'newest': ContextDossier.created_at.desc(), 'oldest': ContextDossier.created_at.asc(), 'title': ContextDossier.title.asc()}
        if sort not in ordering:
            raise HTTPException(422, 'Unknown dossier sort order.')
        total = query.count()
        limit, offset = max(1, min(50, limit)), max(0, offset)
        result = []
        for row, actual_status in query.order_by(ordering[sort], ContextDossier.id).offset(offset).limit(limit):
            docs = row.state.get("documents", [])
            if not docs:
                docs = [{'document_id': str(d.id), 'source_filename': d.original_name, 'document_type': d.document_type or 'unknown', 'status': d.status}
                    for d in db.query(DossierDocument).filter_by(dossier_id=uuid.UUID(row.id))]
            result.append({"dossier_id": row.id, "title": row.title, "status": actual_status,
                "created_at": datetime.fromtimestamp(row.created_at, timezone.utc).isoformat(), "document_count": len(docs),
                "documents": [{"document_id": d["document_id"], "original_name": d.get("source_filename", "document.pdf"),
                    "document_type": d["document_type"], "status": d.get('status', 'done')} for d in docs],
                'revision': row.revision, 'graph_revision': row.graph_revision})
        return {"dossiers": result, 'total': total, 'offset': offset, 'limit': limit, 'has_more': offset + len(result) < total}


# ══════════════════════════════════════════════════════════════════
# GET /api/rules/active — return dynamic rules for Pre-Check Matrix
# ══════════════════════════════════════════════════════════════════

from pydantic import BaseModel

class RuleMetadata(BaseModel):
    id: str
    label: str
    description: str
    status: str = "Ready"

ACTIVE_RULES = [
    RuleMetadata(
        id="RULE_HS_CODE",
        label="HS Code Concordance",
        description="Cotton apparel harmonized between Commercial Invoice and AWB cargo description."
    ),
    RuleMetadata(
        id="RULE_INCOTERMS",
        label="Incoterms & Apportionment",
        description="Ocean freight breakdown mapped without duty base variance (CIF Colombo)."
    ),
    RuleMetadata(
        id="RULE_TIN_REGISTRY",
        label="TIN/EORI Registry",
        description="Declarant TIN validated with Inland Revenue Department."
    ),
    RuleMetadata(
        id="RULE_WEIGHT_TOL",
        label="Weight Tolerance Check",
        description="Cross-document weight comparison queued for Rule Evaluator."
    ),
]

@router.get("/rules/active", response_model=List[dict])
async def get_active_rules(request: Request):
    from context_app.models import Tenant
    from database.connection import SessionLocal
    from reasoning.comparison import describe
    with SessionLocal() as db:
        policy = describe((db.get(Tenant, request.state.user['tenant_id']).settings or {}).get('comparison_policy'))
    return [{"id": policy['version'], "label": "Prototype field comparison", "status": "Prototype",
        "description": f"Absolute weight tolerance {policy['weight_absolute_tolerance']}; integer counts; decimal amounts; mixed units require review. Not a customs regulation."}]

@router.post('/shipments/{shipment_id}/discrepancies/{discrepancy_id}/resolve')
async def resolve_discrepancy(shipment_id: str, discrepancy_id: str, decision: dict):
    del shipment_id, discrepancy_id, decision
    raise HTTPException(
        status_code=410,
        detail="Use the field-resolution workflow to select source evidence or enter a corrected value.",
    )

