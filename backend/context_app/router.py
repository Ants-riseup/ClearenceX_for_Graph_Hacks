import copy
import hashlib
import io
import time
import uuid
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form, BackgroundTasks, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ConfigDict
from pypdf import PdfReader
from database.connection import SessionLocal
from .models import ContextDossier, AgentRun, Outbox
from .security import authorize_dossier
from .config import DATA_ROOT, MAX_FILE_BYTES, MAX_PAGES
from .service import context_view, graph_tool, propose, decide, replace_document, create_dossier, require_current, enqueue
from .fixtures import hero_documents, fixture_document
from .graph import GraphRepository, fields

router = APIRouter(prefix="/api", tags=["context"])


@router.post("/demo/dossiers", status_code=201)
def create_demo(request: Request):
    if request.state.user["role"] not in {"user", "reviewer", "admin"}:
        raise HTTPException(403, "Reviewer permission required.")
    sid = create_dossier(request.state.user, hero_documents(), "Synthetic evidence-change demonstration")
    return {"shipment_id": sid, "status": "context_pending", "fixture": True}


@router.get("/shipments/{shipment_id}/context-status")
def status(shipment_id: str, request: Request):
    return context_view(shipment_id, request.state.user)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EvidenceQuestion(StrictModel):
    field_id: str = Field(min_length=1, max_length=255)


@router.get("/shipments/{shipment_id}/context-evidence")
def evidence(shipment_id: str, field_id: str, request: Request):
    return {"evidence": graph_tool(shipment_id, request.state.user, "get_field_evidence", field_id=field_id)}


@router.get("/shipments/{shipment_id}/context-issues")
def issues(shipment_id: str, request: Request):
    return {"fields": graph_tool(shipment_id, request.state.user, "list_dossier_issues")}


@router.get("/shipments/{shipment_id}/change-impact")
def impact(shipment_id: str, document_id: str, request: Request, expected_revision: int | None = Query(default=None, ge=1)):
    return {"impact": graph_tool(shipment_id, request.state.user, "get_change_impact", expected=expected_revision, document_id=document_id)}


@router.get("/shipments/{shipment_id}/context-memory")
def memory(shipment_id: str, request: Request):
    return {"memory": graph_tool(shipment_id, request.state.user, "recall_approved_decisions")}


@router.get("/shipments/{shipment_id}/context-rules")
def rules(shipment_id: str, field_id: str, request: Request):
    return {"rules": graph_tool(shipment_id, request.state.user, "get_rule_explanation", field_id=field_id)}


class Proposal(StrictModel):
    field_id: str = Field(max_length=255)
    evidence_ids: list[str] = Field(min_length=1, max_length=50)
    reason: str = Field(min_length=1, max_length=1000)
    expected_revision: int = Field(ge=1)


@router.post("/shipments/{shipment_id}/review-tasks")
def proposal(shipment_id: str, payload: Proposal, request: Request):
    return propose(shipment_id, request.state.user, payload.field_id, payload.evidence_ids,
        payload.reason, payload.expected_revision)


class DecisionInput(StrictModel):
    field_id: str = Field(max_length=255)
    assertion_id: str = Field(max_length=255)
    reason: str = Field(min_length=1, max_length=1000)
    expected_revision: int = Field(ge=1)
    request_id: str = Field(min_length=8, max_length=100)
    reject: bool = False


@router.post("/shipments/{shipment_id}/review-tasks/{task_id}/decision")
def decision(shipment_id: str, task_id: str, payload: DecisionInput, request: Request):
    return decide(shipment_id, request.state.user, payload.field_id, payload.assertion_id, payload.reason,
        payload.expected_revision, task_id=task_id, request_id=payload.request_id, reject=payload.reject)


@router.post("/shipments/{shipment_id}/demo-correction")
def demo_correction(shipment_id: str, request: Request, expected_revision: int):
    with SessionLocal() as db:
        row = authorize_dossier(db, shipment_id, request.state.user, write=True)
        old = next((d for d in row.state["documents"] if d["document_type"] == "packing_list" and d.get("fixture")), None)
        if not old:
            raise HTTPException(409, "Correction shortcut is only available on the synthetic packing list.")
    return replace_document(shipment_id, request.state.user, old["document_id"],
        fixture_document("packing_list", 440), expected_revision)


async def save_pdf(upload: UploadFile):
    name = upload.filename or ""
    if not name.lower().endswith(".pdf") or Path(name).name != name or "/" in name or "\\" in name or ":" in name:
        raise HTTPException(422, "Use a plain PDF filename without paths.")
    content = bytearray()
    while chunk := await upload.read(64 * 1024):
        content.extend(chunk)
        if len(content) > MAX_FILE_BYTES:
            raise HTTPException(413, "PDF exceeds the 20 MB limit.")
    if not content.startswith(b'%PDF-'):
        raise HTTPException(422, 'PDF signature is invalid.')
    path = DATA_ROOT / "private" / (str(uuid.uuid4()) + ".pdf")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    try:
        import asyncio, subprocess, sys, os
        environment = {k: v for k, v in os.environ.items() if k.upper() in {'PATH', 'SYSTEMROOT', 'WINDIR', 'HOME', 'USERPROFILE', 'TEMP', 'TMP', 'LD_LIBRARY_PATH'}}
        await asyncio.to_thread(subprocess.run, [sys.executable, '-m', 'context_app.validate_pdf', str(path)],
            env=environment, cwd=Path(__file__).resolve().parents[1], timeout=10, check=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as exc:
        path.unlink(missing_ok=True)
        raise HTTPException(422, 'PDF must parse within limits, be unencrypted and have at most 25 pages.') from exc
    return {"original_name": name, "file_path": str(path), "size": len(content), "content_hash": hashlib.sha256(content).hexdigest()}


@router.post("/shipments/{shipment_id}/documents/{document_id}/replacement")
async def replace_pdf(shipment_id: str, document_id: str, request: Request,
    file: UploadFile = File(...), expected_revision: int = Form(...)):
    with SessionLocal() as db:
        row = authorize_dossier(db, shipment_id, request.state.user, write=True)
        require_current(row, expected_revision)
    saved = await save_pdf(file)
    try:
        # Use the same bounded process and credential isolation as initial uploads.
        import subprocess
        import sys
        import os
        import asyncio
        did = str(uuid.uuid4())
        output = DATA_ROOT / "private" / (str(uuid.uuid4()) + ".json")
        env = {k: v for k, v in os.environ.items() if k.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "HOME", "USERPROFILE", "TEMP", "TMP", "LD_LIBRARY_PATH"}}
        env["CLEARANCEX_LOCAL_EXTRACTION"] = "true"
        try:
            await asyncio.to_thread(subprocess.run, [sys.executable, "-m", "context_app.extract_file", saved["file_path"], did, str(output)],
                env=env, cwd=Path(__file__).resolve().parents[1], timeout=120, check=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            import json
            result = json.loads(output.read_text(encoding="utf-8"))
        finally:
            output.unlink(missing_ok=True)
        if result.get("errors") or not result.get("entities"):
            raise HTTPException(422, "Replacement needs successful extraction. Original evidence was preserved.")
        result.update(document_id=did, source_filename=saved["original_name"],
            file_path=saved["file_path"], content_hash=saved["content_hash"], fixture=False)
        return replace_document(shipment_id, request.state.user, document_id, result, expected_revision)
    except HTTPException:
        Path(saved["file_path"]).unlink(missing_ok=True)
        raise
    except Exception as exc:
        Path(saved["file_path"]).unlink(missing_ok=True)
        raise HTTPException(503, "Local OCR is unavailable; original evidence was preserved.") from exc


@router.get("/documents/{document_id}/content")
def content(document_id: str, request: Request):
    with SessionLocal() as db:
        rows = db.query(ContextDossier).filter_by(tenant_id=request.state.user["tenant_id"]).all()
        found = next((d for row in rows for d in row.state.get("documents", []) + row.state.get("archived_documents", []) if d["document_id"] == document_id), None)
        if not found:
            raise HTTPException(404, "Document not found.")
        path = Path(found.get("file_path", "")).resolve()
        if not path.is_relative_to(DATA_ROOT) or not path.is_file():
            raise HTTPException(404, "Document file not available.")
        return FileResponse(path, media_type="application/pdf", filename=found.get("source_filename", "document.pdf"),
            content_disposition_type="inline", headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})


class Investigation(StrictModel):
    question: str = Field(min_length=5, max_length=2000)


@router.post("/shipments/{shipment_id}/agent-runs", status_code=202)
def investigate(shipment_id: str, payload: Investigation, request: Request, background: BackgroundTasks):
    from .agent import run_agent
    with SessionLocal() as db:
        row = authorize_dossier(db, shipment_id, request.state.user, write=True, lock=True)
        require_current(row)
        active = db.query(AgentRun).filter_by(dossier_id=shipment_id, status="running").count()
        if active:
            raise HTTPException(409, "An investigation is already running for this dossier.")
        rid = str(uuid.uuid4())
        db.add(AgentRun(id=rid, dossier_id=shipment_id, actor_id=request.state.user["id"], revision=row.revision,
            status="running", question=payload.question, result={}, created_at=int(time.time()), updated_at=int(time.time())))
        db.commit()
    background.add_task(run_agent, rid, dict(request.state.user))
    return {"run_id": rid, "status": "running"}


@router.get("/shipments/{shipment_id}/agent-runs")
def runs(shipment_id: str, request: Request):
    with SessionLocal() as db:
        authorize_dossier(db, shipment_id, request.state.user)
        rows = db.query(AgentRun).filter_by(dossier_id=shipment_id).order_by(AgentRun.created_at.desc()).limit(20).all()
        return {"runs": [{"run_id": r.id, "status": r.status, "question": r.question,
            "graph_revision": r.revision, "result": r.result} for r in rows]}


@router.get("/shipments/{shipment_id}/agent-runs/{run_id}")
def run_status(shipment_id: str, run_id: str, request: Request):
    with SessionLocal() as db:
        authorize_dossier(db, shipment_id, request.state.user)
        r = db.get(AgentRun, run_id)
        if not r or r.dossier_id != shipment_id:
            raise HTTPException(404, "Investigation not found.")
        return {"run_id": r.id, "status": r.status, "question": r.question, "graph_revision": r.revision, "result": r.result}


@router.post("/shipments/{shipment_id}/agent-runs/{run_id}/cancel")
def cancel(shipment_id: str, run_id: str, request: Request):
    with SessionLocal() as db:
        authorize_dossier(db, shipment_id, request.state.user, write=True)
        run = db.query(AgentRun).filter_by(id=run_id, dossier_id=shipment_id).with_for_update().first()
        if not run:
            raise HTTPException(404, "Investigation not found.")
        if run.actor_id != request.state.user["id"] and request.state.user["role"] != "admin":
            raise HTTPException(403, "Only the initiating user or administrator can cancel this run.")
        if run.status == "running":
            run.status = "cancelled"
            run.result = {"error": "Cancellation requested; an in-flight model request may finish and remain billable."}
            db.commit()
        return {"status": run.status}


@router.post("/shipments/{shipment_id}/context-retry")
def retry(shipment_id: str, request: Request):
    with SessionLocal() as db:
        row = authorize_dossier(db, shipment_id, request.state.user, write=True, lock=True)
        db.add(Outbox(id=str(uuid.uuid4()), dossier_id=row.id, revision=row.revision,
            status="pending", attempts=0, next_attempt=0))
        db.commit()
    return {"status": "context_pending"}
