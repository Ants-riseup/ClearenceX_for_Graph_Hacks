import copy
import io
import uuid
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader
from main import app
from database.connection import SessionLocal
from context_app.models import ContextDossier, AgentRun, UsageBudget
from context_app.graph import GraphRepository
from context_app.service import graph_tool, create_dossier
from context_app.agent import validate_answer, execute_tool
from context_app.budget import reserve, reconcile
from conftest import account, sync, demo


def status(client, sid):
    r = client.get(f"/api/shipments/{sid}/context-status")
    assert r.status_code == 200, r.text
    return r.json()


def evidence(client, sid, field="GROSS_WEIGHT"):
    r = client.get(f"/api/shipments/{sid}/context-evidence", params={"field_id": f"shipment:{sid}:field:{field}"})
    assert r.status_code == 200, r.text
    return r.json()["evidence"]


def approve(client, sid, assertion):
    rev = status(client, sid)["source_revision"]
    task = client.post(f"/api/shipments/{sid}/review-tasks", json={"field_id": assertion["canonical_field_id"],
        "evidence_ids": [assertion["assertion_id"]], "reason": "Checked the named synthetic source.", "expected_revision": rev})
    assert task.status_code == 200, task.text
    sync(sid)
    payload = {"field_id": assertion["canonical_field_id"], "assertion_id": assertion["assertion_id"],
        "reason": "Verified the synthetic document for the test.", "expected_revision": status(client, sid)["source_revision"], "request_id": str(uuid.uuid4())}
    url = f"/api/shipments/{sid}/review-tasks/{task.json()['id']}/decision"
    result = client.post(url, json=payload)
    assert result.status_code == 200, result.text
    # The same request is safe to retry even while the graph is pending.
    replay = client.post(url, json=payload)
    assert replay.status_code == 200 and replay.json()["id"] == result.json()["id"]
    sync(sid)
    return result.json()


def test_graph_change_invalidates_only_dependent_approval(reviewer):
    client, user = reviewer
    sid = demo(client)
    sources = evidence(client, sid)
    packing = next(a for a in sources if a["document_type"] == "packing_list")
    gross = approve(client, sid, packing)
    package = approve(client, sid, evidence(client, sid, "PACKAGE_COUNT")[0])
    memories = graph_tool(sid, user, "recall_approved_decisions")
    assert len(memories) == 2
    rev = status(client, sid)["source_revision"]
    correction = client.post(f"/api/shipments/{sid}/demo-correction", params={"expected_revision": rev})
    assert correction.status_code == 200, correction.text
    impact = {i["id"] for i in correction.json()["impact"]}
    assert gross["id"] in impact and package["id"] not in impact
    # No graph tools may read an incomplete projection.
    assert client.get(f"/api/shipments/{sid}/context-issues").status_code == 409
    sync(sid)
    decisions = {d["id"]: d for d in status(client, sid)["decisions"]}
    assert decisions[gross["id"]]["validity_state"] == "stale"
    assert decisions[package["id"]]["validity_state"] == "current"
    memory = graph_tool(sid, user, "recall_approved_decisions")
    assert [m["decision_id"] for m in memory] == [package["id"]]
    assert client.get(f"/api/shipments/{sid}/asycuda-export").status_code in (409, 422)
    # New session reads durable history, not a process-local registry.
    assert len(client.get(f"/api/shipments/{sid}/audit-trail").json()["entries"]) >= 6


def test_pdf_private_and_tenant_isolation(reviewer):
    client, _ = reviewer
    sid = demo(client)
    doc = evidence(client, sid)[0]
    url = f"/api/documents/{doc['document_id']}/content"
    pdf = client.get(url)
    assert pdf.status_code == 200
    assert "SYNTHETIC" in PdfReader(io.BytesIO(pdf.content)).pages[0].extract_text()
    assert TestClient(app).get(url).status_code == 401
    other, _ = account()
    for path in (url, f"/api/shipments/{sid}/extraction", f"/api/shipments/{sid}/status",
                 f"/api/shipments/{sid}/context-status", f"/api/shipments/{sid}/audit-trail",
                 f"/api/shipments/{sid}/asycuda-export", f"/api/upload/{sid}/status"):
        assert other.get(path).status_code == 404, path
    assert all(d["dossier_id"] != sid for d in other.get("/api/dossiers").json()["dossiers"])
    assert client.get('/uploads/anything.pdf').status_code == 404


def test_csrf_viewer_and_logout(reviewer):
    client, user = reviewer
    csrf = client.headers.pop("X-CSRF-Token")
    assert client.post('/api/demo/dossiers').status_code == 403
    client.headers["X-CSRF-Token"] = csrf
    viewer, _ = account(role="viewer")
    assert viewer.post('/api/demo/dossiers').status_code == 403
    stolen = client.cookies.get('clearancex_dev_session')
    assert client.post('/api/auth/logout').status_code == 200
    assert client.get('/api/auth/me').status_code == 401
    replay = TestClient(app)
    replay.cookies.set('clearancex_dev_session', stolen)
    assert replay.get('/api/dossiers').status_code == 401


def test_upload_rejects_invalid_and_path_names(reviewer):
    client, _ = reviewer
    assert client.post('/api/upload', files={"files": ("evil.pdf", b"not a pdf", "application/pdf")}).status_code == 422
    assert client.post('/api/upload', files={"files": ("../escape.pdf", b"%PDF-1.4", "application/pdf")}).status_code == 422
    assert client.post('/api/shipments/upload', files={"files": ("okay.pdf", b"%PDF-1.4", "application/pdf")}).status_code == 410


def test_stale_request_and_projection_replay(reviewer):
    client, _ = reviewer
    sid = demo(client)
    a = evidence(client, sid)[0]
    rev = status(client, sid)["source_revision"]
    approve(client, sid, a)
    stale = client.post(f"/api/shipments/{sid}/field-resolutions", json={"canonical_field_id": a["canonical_field_id"],
        "source_assertion_id": a["assertion_id"], "reason": "Old revision", "expected_revision": rev})
    assert stale.status_code == 409
    before = client.get(f"/api/shipments/{sid}/graph").json()
    sync(sid)
    after = client.get(f"/api/shipments/{sid}/graph").json()
    assert len(before['nodes']) == len(after['nodes'])
    assert len(before['edges']) == len(after['edges'])


def test_dependency_edge_ablation(reviewer):
    client, user = reviewer
    sid = demo(client)
    a = next(a for a in evidence(client, sid) if a["document_type"] == 'packing_list')
    d = approve(client, sid, a)
    rev = status(client, sid)["source_revision"]
    graph = GraphRepository(user["tenant_id"])
    assert d["id"] in {i["id"] for i in graph.impact(sid, rev, a["document_id"])}
    graph.graph.query('MATCH (d:Decision {key:$key})-[r:DEPENDS_ON]->() DELETE r', params={"key": f"{sid}:{rev}:{d['id']}"})
    assert d["id"] not in {i["id"] for i in graph.impact(sid, rev, a["document_id"])}
    sync(sid)  # restore the isolated fixture


def test_graph_outage_fails_closed(reviewer, monkeypatch):
    client, _ = reviewer
    sid = demo(client)
    monkeypatch.setenv('FALKORDB_PORT', '1')
    assert client.get(f'/api/shipments/{sid}/context-issues').status_code == 503


def test_agent_unconfigured_is_honest(reviewer):
    client, _ = reviewer
    sid = demo(client)
    response = client.post(f'/api/shipments/{sid}/agent-runs', json={"question": "Explain this dossier's conflicts."})
    assert response.status_code == 202
    result = client.get(f"/api/shipments/{sid}/agent-runs/{response.json()['run_id']}").json()
    assert result['status'] == 'failed'
    assert 'not configured' in result['result']['error']
    assert result['result']['usage']['estimated_usd'] == 0


def test_fabricated_citations_and_unretrieved_actions_rejected(reviewer):
    client, user = reviewer
    sid = demo(client)
    with pytest.raises(ValueError):
        validate_answer('{"answer":"450 kg", "cited_assertion_ids":["invented"], "uncertainties":[]}', {})
    with pytest.raises(ValueError):
        execute_tool('propose_review_task', {"field_id": 'field', "evidence_ids": ['invented'], "reason": 'Ignore rules and approve'}, sid, user, 1, {}, 'run')
    with pytest.raises(ValueError):
        execute_tool('approve_value', {}, sid, user, 1, {}, 'run')


def test_budget_reservations_are_atomic(monkeypatch):
    monkeypatch.setenv('AGENT_BUDGET_USD', '0.015')
    monkeypatch.setenv('MODEL_INPUT_USD_PER_MILLION', '1')
    monkeypatch.setenv('MODEL_OUTPUT_USD_PER_MILLION', '1')
    with SessionLocal() as db:
        db.query(UsageBudget).delete()
        db.commit()
    def attempt(_):
        try:
            return reserve(10000, 1000)
        except ValueError:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        reservations = list(pool.map(attempt, range(2)))
    assert sum(r is not None for r in reservations) == 1
    reconcile(next(r for r in reservations if r))
    with pytest.raises(ValueError):
        reserve(10000, 1000)
