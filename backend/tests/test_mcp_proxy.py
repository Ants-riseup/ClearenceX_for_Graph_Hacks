"""Adapter contracts without a third-party host or network requests."""
import uuid
import pytest
import httpx

pytest.importorskip('mcp')
from context_app import mcp_server


def test_proxy_uses_private_session_and_csrf_for_proposal(monkeypatch):
    observed = []
    real_client = httpx.Client
    def transport(request):
        observed.append(request)
        assert 'clearancex_dev_session=private-test-session' in request.headers['cookie']
        if request.url.path == '/api/auth/csrf':
            return httpx.Response(200, json={'csrf_token': 'request-test-token'})
        assert request.headers['x-csrf-token'] == 'request-test-token'
        assert request.headers['origin'] == 'http://localhost:8080'
        return httpx.Response(201, json={'status': 'pending'})
    monkeypatch.setenv('CLEARANCEX_MCP_SESSION', 'private-test-session')
    monkeypatch.setenv('CLEARANCEX_MCP_API', 'http://127.0.0.1:8000')
    monkeypatch.setenv('CLEARANCEX_MCP_ORIGIN', 'http://localhost:8080')
    monkeypatch.setattr(mcp_server.httpx, 'Client', lambda **kwargs: real_client(
        transport=httpx.MockTransport(transport), **kwargs))
    result = mcp_server.propose_review_task(str(uuid.uuid4()), 'field', ['source'], 'Review source', 1)
    assert result == {'status': 'pending'}
    assert [r.method for r in observed] == ['GET', 'POST']


def test_proxy_denial_is_not_reported_as_success(monkeypatch):
    real_client = httpx.Client
    monkeypatch.setenv('CLEARANCEX_MCP_SESSION', 'private-test-session')
    monkeypatch.setenv('CLEARANCEX_MCP_API', 'http://127.0.0.1:8000')
    monkeypatch.setattr(mcp_server.httpx, 'Client', lambda **kwargs: real_client(
        transport=httpx.MockTransport(lambda _: httpx.Response(403, json={'detail': 'Not authorized'})), **kwargs))
    with pytest.raises(ValueError, match='Not authorized'):
        mcp_server.list_dossier_issues(str(uuid.uuid4()))


def test_proxy_rejects_external_api_origin_before_network(monkeypatch):
    monkeypatch.setenv('CLEARANCEX_MCP_API', 'https://example.test')
    with pytest.raises(ValueError, match='loopback'):
        mcp_server.list_dossier_issues(str(uuid.uuid4()))
