from pathlib import Path
import pytest
from fastapi import HTTPException
from conftest import account, demo
from database.connection import SessionLocal
from context_app.config import DATA_ROOT
from context_app.models import ContextDossier, PrivatePdf
from context_app.pdf_storage import persist_pdf, restore_pdf


def test_originals_survive_cache_loss_and_remain_tenant_private(monkeypatch):
    monkeypatch.setenv('PDF_STORAGE', 'postgres')
    client, owner = account()
    stranger, other = account()
    sid = demo(client)
    with SessionLocal() as db:
        document = db.get(ContextDossier, sid).state['documents'][0]
        path = Path(document['file_path'])
        original = path.read_bytes()
        path.unlink()
        with pytest.raises(HTTPException) as denied:
            restore_pdf(db, other['tenant_id'], path)
        assert denied.value.status_code == 404
        assert not path.exists()
    assert stranger.get(f"/api/documents/{document['document_id']}/content").status_code == 404
    result = client.get(f"/api/documents/{document['document_id']}/content")
    assert result.status_code == 200
    assert result.content == original == path.read_bytes()
    with SessionLocal() as db:
        key = path.relative_to(DATA_ROOT).as_posix()
        stored = db.get(PrivatePdf, key)
        stored.content = b'corrupted'
        db.commit()
    assert client.get(f"/api/documents/{document['document_id']}/content").status_code == 503


def test_storage_quota_rejects_without_partial_blob(monkeypatch):
    monkeypatch.setenv('PDF_STORAGE', 'postgres')
    monkeypatch.setenv('PDF_STORAGE_TENANT_MB', '0')
    _, owner = account()
    from context_app.fixtures import fixture_document
    path = Path(fixture_document('packing_list', 440)['file_path'])
    key = path.relative_to(DATA_ROOT).as_posix()
    with SessionLocal() as db:
        with pytest.raises(HTTPException) as denied:
            persist_pdf(db, owner['tenant_id'], path)
        assert denied.value.status_code == 507
        db.rollback()
        assert db.get(PrivatePdf, key) is None
        with pytest.raises(HTTPException):
            restore_pdf(db, owner['tenant_id'], DATA_ROOT.parent / 'outside.pdf')


def test_pending_upload_extracts_after_host_cache_is_lost(monkeypatch):
    monkeypatch.setenv('PDF_STORAGE', 'postgres')
    client, _ = account()
    from context_app.fixtures import hero_documents
    from context_app.upload import process_one_upload
    from database.models import DossierDocument
    import uuid
    source = Path(hero_documents()[0]['file_path']).read_bytes()
    response = client.post('/api/upload', files={'files': ('invoice.pdf', source, 'application/pdf')})
    assert response.status_code == 202, response.text
    sid = response.json()['shipment_id']
    with SessionLocal() as db:
        pending = db.query(DossierDocument).filter_by(dossier_id=uuid.UUID(sid)).one()
        path = Path(pending.file_path)
        path.unlink()
    assert process_one_upload()
    assert client.get(f'/api/upload/{sid}/status').json()['status'] == 'done'
    assert path.read_bytes() == source
