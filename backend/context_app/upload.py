"""Private bounded uploads with durable pending status and explicit OCR failures."""
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from sqlalchemy import String
from fastapi import APIRouter, File, UploadFile, Request, HTTPException
from database.connection import SessionLocal
from database.models import Dossier, DossierDocument
from .models import ContextDossier, Tenant
from .router import save_pdf
from .config import MAX_FILES, MAX_REQUEST_BYTES, DATA_ROOT
from .service import event, now, publish_extraction

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("", status_code=202)
async def upload(request: Request, files: list[UploadFile] = File(...)):
    if not 1 <= len(files) <= MAX_FILES:
        raise HTTPException(422, "Upload 1–10 PDF files.")
    saved = []
    try:
        for file in files:
            saved.append(await save_pdf(file))
            if sum(d["size"] for d in saved) > MAX_REQUEST_BYTES:
                raise HTTPException(413, "Dossier exceeds the 80 MB limit.")
        sid = str(uuid.uuid4())
        state = {"documents": [], "archived_documents": [], "decisions": [], "tasks": [], "events": []}
        event(state, request.state.user["id"], "upload_accepted", {"document_count": len(saved)})
        with SessionLocal() as db:
            state['comparison_policy'] = dict((db.get(Tenant, request.state.user['tenant_id']).settings or {}).get('comparison_policy', {}))
            db.add(ContextDossier(id=sid, tenant_id=request.state.user["tenant_id"], title="Uploaded dossier",
                revision=1, graph_revision=0, created_at=now(), state=state))
            db.add(Dossier(id=uuid.UUID(sid), status="pending"))
            db.flush()
            ids = []
            for doc in saved:
                did = uuid.uuid4()
                ids.append(str(did))
                db.add(DossierDocument(id=did, dossier_id=uuid.UUID(sid), original_name=doc["original_name"],
                    file_path=doc["file_path"], status="pending"))
            db.commit()
        return {"shipment_id": sid, "document_count": len(ids), "document_ids": ids,
            "status": "pending", "status_url": f"/api/upload/{sid}/status"}
    except Exception:
        for doc in saved:
            Path(doc["file_path"]).unlink(missing_ok=True)
        raise


@router.get("/{dossier_id}/status")
def status(dossier_id: str):
    with SessionLocal() as db:
        row = db.get(Dossier, uuid.UUID(dossier_id))
        if not row:
            raise HTTPException(404, "Upload not found.")
        docs = db.query(DossierDocument).filter_by(dossier_id=row.id).all()
        return {"dossier_id": dossier_id, "status": row.status,
            "completed_documents": sum(d.status == "done" for d in docs), "total_documents": len(docs),
            "documents": [{"document_id": str(d.id), "original_name": d.original_name,
                "document_type": d.document_type, "status": d.status, "error_message": d.error_message,
                "quality_status": (d.extraction_json or {}).get('quality_status'),
                "missing_fields": (d.extraction_json or {}).get('missing_fields', [])} for d in docs]}


@router.post("/{dossier_id}/retry")
def retry(dossier_id: str):
    with SessionLocal() as db:
        row = db.query(Dossier).filter_by(id=uuid.UUID(dossier_id)).with_for_update().first()
        if not row or row.status not in {"error", "interrupted"}:
            raise HTTPException(409, "Only failed/interrupted uploads can be retried.")
        row.status = "pending"
        db.query(DossierDocument).filter(DossierDocument.dossier_id == row.id, DossierDocument.status != "done").update({"status": "pending", "error_message": None})
        db.commit()
    return {"status": "pending"}


def process_one_upload():
    with SessionLocal() as db:
        row = db.query(Dossier).join(ContextDossier, ContextDossier.id == Dossier.id.cast(String)).filter(Dossier.status == "pending").order_by(Dossier.created_at).with_for_update(skip_locked=True).first()
        if not row:
            return False
        row.status = "processing"
        sid = row.id
        jobs = [{"id": d.id, "path": d.file_path, "name": d.original_name, "status": d.status}
            for d in db.query(DossierDocument).filter_by(dossier_id=sid).all()]
        db.commit()
    successful, errors = [], False
    for job in jobs:
        output = DATA_ROOT / "private" / (str(uuid.uuid4()) + ".json")
        try:
            if job["status"] == "done":
                with SessionLocal() as db:
                    successful.append(db.get(DossierDocument, job["id"]).extraction_json)
                continue
            with SessionLocal() as db:
                db.get(DossierDocument, job["id"]).status = "processing"
                db.commit()
            env = {k: v for k, v in os.environ.items() if k.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "HOME", "USERPROFILE", "TEMP", "TMP", "LD_LIBRARY_PATH"}}
            env["CLEARANCEX_LOCAL_EXTRACTION"] = "true"
            subprocess.run([sys.executable, "-m", "context_app.extract_file", job["path"], str(job["id"]), str(output)],
                env=env, cwd=Path(__file__).resolve().parents[1], timeout=120, check=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            data = json.loads(output.read_text(encoding="utf-8"))
            if data.get("errors") or not data.get("entities") or data.get("document_type") == "unknown":
                raise ValueError("Local extraction failed or needs manual review.")
            data.update(file_path=job["path"], source_filename=job["name"], revision=1, fixture=False)
            with SessionLocal() as db:
                doc = db.get(DossierDocument, job["id"])
                doc.status, doc.document_type, doc.extraction_json = "done", data["document_type"], data
                db.commit()
            successful.append(data)
        except Exception:
            errors = True
            with SessionLocal() as db:
                doc = db.get(DossierDocument, job["id"])
                doc.status, doc.error_message = "error", "Local OCR failed, timed out or is unavailable. Install the OCR profile and retry."
                db.commit()
        finally:
            output.unlink(missing_ok=True)
    try:
        with SessionLocal() as db:
            row = db.query(Dossier).filter_by(id=sid).with_for_update().one()
            if not errors and successful:
                publish_extraction(str(sid), successful, db=db)
                row.status = "done"
            else:
                row.status = "error"
            db.commit()
    except Exception:
        # Extraction results stay private and reusable. A publication failure
        # must be retryable, never a false terminal success or stuck job.
        with SessionLocal() as db:
            db.get(Dossier, sid).status = "error"
            db.commit()
        raise
    return True
