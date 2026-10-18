"""Durable private originals for small hosts whose local disk is only a cache."""
import hashlib
import os
from pathlib import Path
from fastapi import HTTPException
from sqlalchemy import func, text
from .config import DATA_ROOT, MAX_FILE_BYTES
from .models import PrivatePdf


def storage_path(path):
    resolved = Path(path).resolve()
    if not resolved.is_relative_to(DATA_ROOT) or resolved.suffix.lower() != '.pdf':
        raise HTTPException(404, 'Document file not available.')
    return resolved, resolved.relative_to(DATA_ROOT).as_posix()


def persist_pdf(db, tenant_id, path):
    if os.getenv('PDF_STORAGE', 'local') != 'postgres':
        return
    resolved, key = storage_path(path)
    db.execute(text('SELECT pg_advisory_xact_lock(467831210)'))
    existing = db.get(PrivatePdf, key)
    if existing:
        if existing.tenant_id != tenant_id:
            raise HTTPException(404, 'Document file not available.')
        return
    if not resolved.is_file() or resolved.stat().st_size > MAX_FILE_BYTES:
        raise HTTPException(422, 'PDF is missing or exceeds the file limit.')
    content = resolved.read_bytes()
    total = db.query(func.coalesce(func.sum(PrivatePdf.size), 0)).scalar()
    tenant_total = db.query(func.coalesce(func.sum(PrivatePdf.size), 0)).filter_by(tenant_id=tenant_id).scalar()
    if total + len(content) > int(os.getenv('PDF_STORAGE_TOTAL_MB', '500')) * 1024 * 1024 or tenant_total + len(content) > int(os.getenv('PDF_STORAGE_TENANT_MB', '100')) * 1024 * 1024:
        raise HTTPException(507, 'PDF storage capacity reached. Ask your administrator for more capacity.')
    db.add(PrivatePdf(storage_key=key, tenant_id=tenant_id, size=len(content),
        sha256=hashlib.sha256(content).hexdigest(), content=content))
    db.flush()


def restore_pdf(db, tenant_id, path):
    resolved, key = storage_path(path)
    if os.getenv('PDF_STORAGE', 'local') == 'postgres':
        stored = db.get(PrivatePdf, key)
        if not stored or stored.tenant_id != tenant_id:
            raise HTTPException(404, 'Document file not available.')
        if hashlib.sha256(stored.content).hexdigest() != stored.sha256:
            raise HTTPException(503, 'Stored document integrity check failed.')
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_bytes(stored.content)
    if not resolved.is_file():
        raise HTTPException(404, 'Document file not available.')
    return resolved
