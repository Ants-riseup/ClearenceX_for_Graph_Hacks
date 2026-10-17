import asyncio
import json
import uuid
import pytest
from fastapi import HTTPException
from main import BodyLimitMiddleware
from database.connection import SessionLocal
from context_app.models import Membership, AgentRun, ContextDossier
from context_app.service import graph_tool, decide
from conftest import account, demo, sync


def test_streaming_json_limit_without_content_length():
    async def downstream(scope, receive, send):
        await receive()
    middleware = BodyLimitMiddleware(downstream)
    async def receive():
        return {"type": "http.request", "body": b"x" * 65537, "more_body": False}
    async def send(_):
        pass
    with pytest.raises(HTTPException) as exc:
        asyncio.run(middleware({"type": "http", "path": "/api/auth/login", "headers": []}, receive, send))
    assert exc.value.status_code == 413


def test_membership_revocation_rechecked_at_tool_boundary(reviewer):
    client, user = reviewer
    sid = demo(client)
    with SessionLocal() as db:
        db.query(Membership).filter_by(user_id=user['id'], tenant_id=user['tenant_id']).delete()
        db.commit()
    with pytest.raises(HTTPException) as exc:
        graph_tool(sid, user, 'list_dossier_issues')
    assert exc.value.status_code == 401


def test_viewer_cannot_export_and_rules_are_honest():
    client, user = account(role='viewer')
    # Create trusted fixture through the internal administration helper, not
    # an unauthorized API mutation, to test the GET export permission itself.
    from context_app.fixtures import hero_documents
    from context_app.service import create_dossier
    sid = create_dossier(user, hero_documents())
    sync(sid)
    assert client.get(f'/api/shipments/{sid}/asycuda-export').status_code == 403
    rules = client.get('/api/rules/active').json()
    assert len(rules) == 1 and rules[0]['status'] == 'Prototype'


def test_existing_review_endpoints_accept_real_context(reviewer):
    client, _ = reviewer
    sid = demo(client)
    for endpoint in ['extraction', 'key-fields', 'discrepancies', 'graph', 'cusdec-readiness', 'audit-trail']:
        result = client.get(f'/api/shipments/{sid}/{endpoint}')
        assert result.status_code == 200, (endpoint, result.text)


def test_mcp_registration_has_no_approval_or_arbitrary_query_tool():
    pytest.importorskip('mcp')
    from context_app.mcp_server import mcp
    tools = asyncio.run(mcp.list_tools())
    names = {tool.name for tool in tools}
    assert names == {'list_dossier_issues', 'get_field_evidence', 'get_rule_explanation',
        'recall_approved_decisions', 'get_change_impact', 'propose_review_task'}
