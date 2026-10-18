import copy
import io
import uuid
import pytest
from sqlalchemy import text
from database.connection import SessionLocal, init_db, engine
from database.models import Dossier, DossierDocument
from context_app.models import ContextDossier, Tenant, Outbox, ExportArtifact
from context_app.fixtures import hero_documents
from context_app.service import create_dossier
from context_app import upload as ingestion
from context_app.graph import GraphRepository
from reasoning.comparison import numeric_equal
from conftest import account, demo, sync


def test_migrations_are_recorded_and_repeatable():
    init_db()
    with engine.connect() as db:
        before = db.execute(text('SELECT version, name FROM cx_schema_migrations ORDER BY version')).all()
    init_db()
    with engine.connect() as db:
        after = db.execute(text('SELECT version, name FROM cx_schema_migrations ORDER BY version')).all()
    assert before == after and [r[0] for r in after] == [1, 2, 3, 4, 5]


def test_failed_publication_is_retryable_and_does_not_finish_job(reviewer, monkeypatch):
    client, user = reviewer
    sid = create_dossier(user)
    doc = hero_documents()[0]
    with SessionLocal() as db:
        db.add(Dossier(id=uuid.UUID(sid), status='pending'))
        db.flush()
        db.add(DossierDocument(id=uuid.UUID(doc['document_id']), dossier_id=uuid.UUID(sid), original_name=doc['source_filename'],
            file_path=doc['file_path'], status='done', extraction_json=doc))
        db.commit()
    original = ingestion.publish_extraction
    def fail(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError('Injected transaction failure after context update')
    monkeypatch.setattr(ingestion, 'publish_extraction', fail)
    with pytest.raises(RuntimeError): ingestion.process_one_upload()
    with SessionLocal() as db:
        assert db.get(Dossier, uuid.UUID(sid)).status == 'error'
        assert not db.get(ContextDossier, sid).state['documents']
        assert db.get(ContextDossier, sid).revision == 1
    assert client.post(f'/api/upload/{sid}/retry').status_code == 200
    monkeypatch.setattr(ingestion, 'publish_extraction', original)
    assert ingestion.process_one_upload()
    with SessionLocal() as db:
        assert db.get(Dossier, uuid.UUID(sid)).status == 'done'
        assert len(db.get(ContextDossier, sid).state['documents']) == 1
        assert db.get(ContextDossier, sid).revision == 2


def test_decimal_policy_boundary_counts_and_custom_weights():
    assert numeric_equal('450', '450.01', 'GROSS_WEIGHT')
    assert not numeric_equal('450', '450.0101', 'GROSS_WEIGHT')
    assert not numeric_equal(12, 12.001, 'PACKAGE_COUNT')
    assert numeric_equal(450, 450.5, 'GROSS_WEIGHT', {'weight_absolute_tolerance': '0.5'})
    assert not numeric_equal('NaN', 1, 'TOTAL_AMOUNT')


def test_dossier_filter_precedes_pagination_and_is_tenant_scoped(reviewer):
    client, user = reviewer
    for title, docs in [('ZZZ ready A', hero_documents()), ('ZZZ pending', []), ('ZZZ ready B', hero_documents())]:
        create_dossier(user, docs, title)
    other_client, other = account()
    create_dossier(other, hero_documents(), 'ZZZ foreign')
    first = client.get('/api/dossiers', params={'search': 'ZZZ', 'status': 'done', 'limit': 1, 'sort': 'title'}).json()
    second = client.get('/api/dossiers', params={'search': 'ZZZ', 'status': 'done', 'limit': 1, 'sort': 'title', 'offset': 1}).json()
    assert first['total'] == 2 and first['has_more']
    assert first['dossiers'][0]['title'] == 'ZZZ ready A'
    assert second['dossiers'][0]['title'] == 'ZZZ ready B' and not second['has_more']


def test_private_drafts_and_reference_revision(reviewer):
    client, user = reviewer
    sid = demo(client)
    url = f'/api/shipments/{sid}'
    draft = {'field_id': f'shipment:{sid}:field:GROSS_WEIGHT', 'reason': 'My private unfinished note', 'expected_revision': 1}
    assert client.post(url + '/review-draft', json=draft).status_code == 200
    assert client.get(url + '/review-draft').json()['draft']['reason'] == draft['reason']
    with SessionLocal() as db: tenant_name = db.get(Tenant, user['tenant_id']).name
    teammate, _ = account(tenant=tenant_name)
    assert teammate.get(url + '/review-draft').json()['draft'] is None
    assert client.post(url + '/reference', json={'title': 'Reviewed reference', 'expected_revision': 1}).status_code == 200
    assert client.post(url + '/review-draft', json=draft).status_code == 409
    sync(sid)
    assert client.get(url + '/context-status').json()['title'] == 'Reviewed reference'


def test_settings_are_versioned_admin_only_and_recompute():
    admin, user = account(role='admin')
    sid = demo(admin)
    payload = {'expected_version': 0, 'weight_absolute_tolerance': 0.5, 'retention_days': 60, 'notifications_enabled': False}
    result = admin.post('/api/workspace/settings', json=payload)
    assert result.status_code == 200, result.text
    assert result.json()['settings']['comparison_policy']['weight_absolute_tolerance'] == '0.5'
    assert admin.post('/api/workspace/settings', json=payload).status_code == 409
    sync(sid)
    assert admin.get(f'/api/shipments/{sid}/context-issues').json()['fields'][0]['comparison_policy']['weight_absolute_tolerance'] == '0.5'
    reviewer, _ = account()
    assert reviewer.post('/api/workspace/settings', json=payload).status_code == 403


def test_actual_pdf_text_is_processed_without_mock_or_model(reviewer):
    client, user = reviewer
    doc = hero_documents()[0]
    with open(doc['file_path'], 'rb') as file:
        response = client.post('/api/upload', files={'files': ('real_digital_invoice.pdf', file.read(), 'application/pdf')})
    assert response.status_code == 202, response.text
    sid = response.json()['shipment_id']
    assert ingestion.process_one_upload()
    with SessionLocal() as db:
        row = db.get(ContextDossier, sid)
        assert row.state['documents'][0]['fixture'] is False
        assert row.state['documents'][0]['extraction_method'] == 'digital_pdf_text'
        assert any(e['entity_type'] == 'GROSS_WEIGHT' and e['normalized_value'] == 450 for e in row.state['documents'][0]['entities'])
    sync(sid)
    assert client.get(f'/api/upload/{sid}/status').json()['status'] == 'done'


def test_batch_blocks_unready_dossier_and_disallows_cross_tenant(reviewer):
    client, _ = reviewer
    sid = demo(client)
    payload = {'request_id': str(uuid.uuid4()), 'dossiers': {sid: 1}}
    result = client.post('/api/batch-exports', json=payload)
    assert result.status_code == 201, result.text
    assert result.json()['status'] == 'blocked' and result.json()['items'][0]['status'] == 'blocked'
    assert client.post('/api/batch-exports', json=payload).json() == result.json()
    other, _ = account()
    assert other.post('/api/batch-exports', json={'request_id': str(uuid.uuid4()), 'dossiers': {sid: 1}}).status_code == 404
    assert other.get(f"/api/batch-exports/{result.json()['batch_id']}/content").status_code == 404
