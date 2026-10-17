from concurrent.futures import ThreadPoolExecutor
import io
from pathlib import Path
import time
import uuid
import pytest
from fastapi import HTTPException
from pypdf import PdfReader, PdfWriter
from context_app.fixtures import write_pdf
from context_app.text_extract import extract
from context_app.models import Session
from context_app.security import digest
from context_app.service import decide
from database.connection import SessionLocal
from conftest import demo, sync
from test_context_flow import evidence, status


def test_real_multipage_text_keeps_page_and_goods_identity(tmp_path):
    first, second = tmp_path / 'first.pdf', tmp_path / 'second.pdf'
    write_pdf(first, ['Commercial Invoice', 'Gross Weight: 450 kg', 'Package Count: 12', 'Shirts | 12 | PCS | 10.00 | 120.00'])
    write_pdf(second, ['Commercial Invoice continued', 'Net Weight: 420 kg', 'Shirts | 12 | PCS | 10.00 | 120.00'])
    writer = PdfWriter()
    for path in (first, second):
        for page in PdfReader(path).pages: writer.add_page(page)
    destination = tmp_path / 'multipage.pdf'
    writer.write(destination)
    result = extract(destination, 'multipage-test')
    assert any(e['entity_type'] == 'NET_WEIGHT' and e['page'] == 2 and e['normalized_value'] == 420 for e in result['entities'])
    assert len(result['line_items']) == 2
    assert {r['page'] for r in result['line_items']} == {1, 2}
    assert len({r['row_id'] for r in result['line_items']}) == 2
    assert all(r['arithmetic_matches'] and r['status'] == 'needs_review' for r in result['line_items'])


def test_concurrent_approvals_do_not_overwrite_each_other(reviewer):
    client, user = reviewer
    sid = demo(client)
    sources = evidence(client, sid)
    field = sources[0]['canonical_field_id']
    revision = status(client, sid)['source_revision']
    def attempt(source):
        try:
            return decide(sid, user, field, source['assertion_id'], 'Concurrent synthetic review', revision, request_id=str(uuid.uuid4()))
        except HTTPException as exc: return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, sources[:2]))
    assert sum(isinstance(r, dict) for r in results) == 1
    assert 409 in results
    sync(sid)
    assert len(status(client, sid)['decisions']) == 1


def test_expired_opaque_session_is_rejected(reviewer):
    client, user = reviewer
    token = client.cookies.get('clearancex_dev_session')
    with SessionLocal() as db:
        db.get(Session, digest(token)).expires_at = int(time.time()) - 1
        db.commit()
    assert client.get('/api/auth/me').status_code == 401


def test_incompatible_units_are_reviewed_not_treated_as_equal():
    from context_app.fixtures import fixture_document
    from reasoning.entity_resolution import resolve_documents
    docs = [fixture_document('commercial_invoice', 450), fixture_document('packing_list', 450)]
    docs[1]['entities'][0]['unit'] = 'lb'
    field = resolve_documents('unit-test', docs)[0]
    assert field['status'] == 'warning'


def test_csrf_is_stable_across_browser_and_mcp_clients(reviewer):
    client, _ = reviewer
    original = client.headers['X-CSRF-Token']
    renewed = client.get('/api/auth/csrf').json()['csrf_token']
    assert original == renewed
    assert client.post('/api/auth/logout', headers={'X-CSRF-Token': original}).status_code == 200


def test_lost_graph_snapshot_fails_closed_until_rebuilt(reviewer):
    from context_app.graph import GraphRepository
    client, user = reviewer
    sid = demo(client)
    graph = GraphRepository(user['tenant_id'])
    graph.graph.query('MATCH (s:Shipment {id:$sid}) DETACH DELETE s', params={'sid': sid})
    assert client.get(f'/api/shipments/{sid}/context-issues').status_code == 503
    from context_app.service import reconcile_graph_projections
    assert reconcile_graph_projections(sid) == 1
    assert client.get(f'/api/shipments/{sid}/context-issues').status_code == 409
    sync(sid)
    assert client.get(f'/api/shipments/{sid}/context-issues').status_code == 200
