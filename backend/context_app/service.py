import copy
import time
import uuid
from fastapi import HTTPException
from sqlalchemy import select
from database.connection import SessionLocal
from .models import ContextDossier, Outbox, AgentRun, Tenant, ExportArtifact
from .security import authorize_dossier
from .graph import GraphRepository, fields, all_assertions


def now():
    return int(time.time())


def event(state, actor, action, details=None):
    state.setdefault("events", []).append({"id": str(uuid.uuid4()), "timestamp": now(),
        "actor_id": actor, "module": "context", "action": action, "outcome": "recorded", "details": details or {}})


def enqueue(db, row, state, actor, action, details=None):
    if action in {'source_replaced', 'decision_approved', 'declarationmetadata_saved', 'cusdeclineitem_saved', 'workspace_settings_changed', 'extraction_completed'}:
        db.query(ExportArtifact).filter_by(dossier_id=row.id, validity_state='current').update({'validity_state': 'stale'})
    event(state, actor, action, details)
    row.state = state
    row.revision += 1
    db.add(Outbox(id=str(uuid.uuid4()), dossier_id=row.id, revision=row.revision,
        status="pending", attempts=0, next_attempt=0))


def create_dossier(user, documents=None, title="Shipment dossier", shipment_id=None):
    sid = shipment_id or str(uuid.uuid4())
    state = {"documents": documents or [], "archived_documents": [], "tasks": [], "decisions": [], "events": []}
    event(state, user["id"], "dossier_created", {"source": "synthetic_fixture" if documents else "upload"})
    with SessionLocal() as db:
        tenant = db.get(Tenant, user['tenant_id'])
        state['comparison_policy'] = dict((tenant.settings or {}).get('comparison_policy', {}))
        db.add(ContextDossier(id=sid, tenant_id=user["tenant_id"], title=title, revision=1,
            graph_revision=0, state=state, created_at=now()))
        db.flush()
        db.add(Outbox(id=str(uuid.uuid4()), dossier_id=sid, revision=1, status="pending", attempts=0, next_attempt=0))
        db.commit()
    return sid


def publish_extraction(sid, documents, db=None):
    """Accept a caller transaction so job completion and publication are atomic."""
    if db is None:
        with SessionLocal() as session:
            publish_extraction(sid, documents, db=session)
            session.commit()
        return
    row = db.query(ContextDossier).filter_by(id=sid).with_for_update().one()
    state = copy.deepcopy(row.state)
    state["documents"] = documents
    enqueue(db, row, state, "pipeline", "extraction_completed")


def sync_one():
    """Row locks serialize writers across API and worker processes; retry is durable."""
    with SessionLocal() as db:
        pending = db.execute(select(Outbox).where(Outbox.status.in_(["pending", "retry"]),
            Outbox.next_attempt <= now()).order_by(Outbox.next_attempt, Outbox.id)
            .with_for_update(skip_locked=True).limit(1)).scalar_one_or_none()
        if not pending:
            return False
        row = db.query(ContextDossier).filter_by(id=pending.dossier_id).with_for_update().one()
        try:
            GraphRepository(row.tenant_id).project(row)
            row.graph_revision = row.revision
            pending.status, pending.error = "done", None
        except Exception:
            pending.attempts += 1
            pending.status = "retry" if pending.attempts < 8 else "failed"
            pending.next_attempt = now() + min(2 ** pending.attempts, 60)
            pending.error = "Graph projection failed; check database connectivity."
        db.commit()
    return True


def reconcile_graph_projections(shipment_id=None):
    """PostgreSQL revisions recover a missing/older graph snapshot after restart."""
    queued = 0
    with SessionLocal() as db:
        query = db.query(ContextDossier)
        if shipment_id is not None:
            query = query.filter(ContextDossier.id == shipment_id)
        for row in query.order_by(ContextDossier.id).with_for_update():
            if not row.state.get('documents'):
                continue
            try:
                result = GraphRepository(row.tenant_id).graph.ro_query(
                    'MATCH (s:Shipment {id:$sid, revision:$revision}) RETURN s.id LIMIT 1',
                    params={'sid': row.id, 'revision': row.revision}, timeout=3000).result_set
                intact = bool(result)
            except Exception:
                intact = False
            if not intact:
                row.graph_revision = 0
                pending = db.query(Outbox).filter(Outbox.dossier_id == row.id, Outbox.status.in_(['pending', 'retry'])).first()
                if not pending:
                    db.add(Outbox(id=str(uuid.uuid4()), dossier_id=row.id, revision=row.revision, status='pending', attempts=0, next_attempt=0))
                queued += 1
        db.commit()
    return queued


def require_current(row, expected=None):
    if expected is not None and row.revision != expected:
        raise HTTPException(409, "The dossier changed. Refresh context and investigate again.")
    if row.graph_revision != row.revision:
        raise HTTPException(409, "Graph context is pending. Wait for synchronization.")


def context_view(sid, user):
    with SessionLocal() as db:
        row = authorize_dossier(db, sid, user)
        return {"shipment_id": sid, "title": row.title, "source_revision": row.revision,
            "graph_revision": row.graph_revision, "status": "synced" if row.revision == row.graph_revision else "context_pending",
            "tasks": row.state.get("tasks", []), "decisions": row.state.get("decisions", []),
            "events": row.state.get("events", []),
            'archived_documents': [{k: d.get(k) for k in ('document_id', 'source_filename', 'document_type', 'revision')} for d in row.state.get('archived_documents', [])],
            "documents": [{k: d.get(k) for k in ("document_id", "source_filename", "document_type", "revision", "fixture", 'warnings', 'extraction_method', 'line_items')} for d in row.state.get("documents", [])]}


def graph_tool(sid, user, name, expected=None, **arguments):
    with SessionLocal() as db:
        row = authorize_dossier(db, sid, user, lock=True)
        require_current(row, expected)
        graph = GraphRepository(row.tenant_id)
        if name == "list_dossier_issues":
            result = graph.issues(sid, row.revision)
        elif name == "get_field_evidence":
            result = graph.evidence(sid, row.revision, arguments["field_id"])
        elif name == "recall_approved_decisions":
            result = graph.memory(sid, row.revision, now())
        elif name == "get_change_impact":
            result = graph.impact(sid, row.revision, arguments["document_id"])
        elif name == "get_rule_explanation":
            import json
            result = [{"evaluation": json.loads(e), "rule": json.loads(r)} for e, r in graph.query("rules", sid, row.revision, field_id=arguments["field_id"])]
        else:
            raise HTTPException(422, "Unknown context tool.")
        if len(result) > 100:
            raise HTTPException(409, "Context exceeds the supported result budget. Narrow the investigation.")
        return result


def propose(sid, user, field_id, evidence_ids, reason, expected, run_id=None):
    if not reason.strip() or len(reason) > 1000:
        raise HTTPException(422, "A concise review reason is required.")
    with SessionLocal() as db:
        row = authorize_dossier(db, sid, user, write=True, lock=True)
        require_current(row, expected)
        evidence = GraphRepository(row.tenant_id).evidence(sid, row.revision, field_id)
        valid = {a["assertion_id"] for a in evidence}
        if not evidence_ids or not set(evidence_ids).issubset(valid):
            raise HTTPException(422, "Proposal must cite current evidence from this field.")
        state = copy.deepcopy(row.state)
        existing = next((t for t in state["tasks"] if t["field_id"] == field_id and t["status"] == "pending" and set(t["evidence_ids"]) == set(evidence_ids)), None)
        if existing:
            return existing
        task = {"id": str(uuid.uuid4()), "field_id": field_id, "evidence_ids": sorted(set(evidence_ids)),
            "reason": reason, "status": "pending", "expected_revision": row.revision + 1,
            "actor_id": user["id"], "run_id": run_id, "created_at": now()}
        state["tasks"].append(task)
        enqueue(db, row, state, user["id"], "review_proposed", {"task_id": task["id"]})
        db.commit()
        return task


def decide(sid, user, field_id, assertion_id, reason, expected, task_id=None, request_id=None, reject=False):
    if not reason.strip() or len(reason) > 1000:
        raise HTTPException(422, "Enter a review reason (1–1000 characters).")
    with SessionLocal() as db:
        row = authorize_dossier(db, sid, user, write=True, lock=True)
        state = copy.deepcopy(row.state)
        duplicate = next((d for d in state["decisions"] if request_id and d.get("request_id") == request_id), None)
        if duplicate:
            if duplicate["field_id"] != field_id or duplicate["assertion_id"] != assertion_id or duplicate["status"] != ("rejected" if reject else "approved"):
                raise HTTPException(409, "Idempotency key belongs to a different decision.")
            return duplicate
        require_current(row, expected)
        evidence = GraphRepository(row.tenant_id).evidence(sid, row.revision, field_id)
        assertion = next((a for a in evidence if a["assertion_id"] == assertion_id), None)
        if not assertion:
            raise HTTPException(422, "Select current evidence for this field.")
        if task_id:
            task = next((t for t in state["tasks"] if t["id"] == task_id and t["field_id"] == field_id and t["status"] == "pending"), None)
            if not task or assertion_id not in task["evidence_ids"]:
                raise HTTPException(409, "Task is no longer current or does not cite this evidence.")
            task["status"] = "rejected" if reject else "approved"
        if not reject:
            for old_task in state["tasks"]:
                if old_task["field_id"] == field_id and old_task["status"] == "pending":
                    old_task["status"] = "superseded"
            for old in state["decisions"]:
                if old["field_id"] == field_id and old["validity_state"] == "current":
                    old["validity_state"] = "superseded"
        d = {"id": str(uuid.uuid4()), "field_id": field_id, "assertion_id": assertion_id,
            "value": assertion["normalized_value"], "status": "rejected" if reject else "approved",
            "validity_state": "current", "reason": reason.strip(), "actor_id": user["id"],
            "decided_at": now(), "revision": row.revision, "task_id": task_id, "request_id": request_id}
        state["decisions"].append(d)
        enqueue(db, row, state, user["id"], "decision_" + d["status"], {"decision_id": d["id"]})
        db.commit()
        return d


def replace_document(sid, user, document_id, replacement, expected):
    with SessionLocal() as db:
        row = authorize_dossier(db, sid, user, write=True, lock=True)
        require_current(row, expected)
        state = copy.deepcopy(row.state)
        old = next((d for d in state["documents"] if d["document_id"] == document_id), None)
        if not old:
            raise HTTPException(404, "Current document not found.")
        # Graph-derived impact is required: no SQL-based substitute.
        impact = GraphRepository(row.tenant_id).impact(sid, row.revision, document_id)
        affected = {i["id"] for i in impact}
        for decision in state["decisions"]:
            if decision["id"] in affected and decision["validity_state"] == "current":
                decision["validity_state"] = "stale"
        for task in state["tasks"]:
            if task["id"] in affected and task["status"] == "pending":
                task["status"] = "stale"
        state["documents"].remove(old)
        state["archived_documents"].append(old)
        replacement["revision"] = old.get("revision", 1) + 1
        state["documents"].append(replacement)
        enqueue(db, row, state, user["id"], "source_replaced", {"old_document_id": document_id,
            "new_document_id": replacement["document_id"], "impact": impact})
        db.commit()
        return {"impact": impact, "source_revision": row.revision}
