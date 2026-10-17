"""Real MCP stdio client -> authenticated test HTTP API -> real FalkorDB."""
import asyncio
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import httpx
import pytest
pytest.importorskip('mcp')
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from conftest import demo


@pytest.mark.skipif(sys.platform == 'win32', reason='Windows host loopback test API timed out despite startup; packaged Linux MCP smoke is required separately.')
def test_real_stdio_mcp_reads_and_proposes_with_session(reviewer, tmp_path):
    client, _ = reviewer
    sid = demo(client)
    token = client.cookies.get('clearancex_dev_session')
    backend = Path(__file__).resolve().parents[1]
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
    environment = dict(os.environ, OPENAI_API_KEY='', ENABLE_LIVE_AGENT='false')
    log = open(tmp_path / 'test-api.log', 'w', encoding='utf-8')
    process = subprocess.Popen([sys.executable, '-u', '-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', str(port), '--log-level', 'info'],
        cwd=backend, env=environment, stdout=log, stderr=log,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
    try:
        with httpx.Client(base_url=f'http://127.0.0.1:{port}', timeout=10, trust_env=False) as health:
            deadline = time.monotonic() + 30
            last_result = 'No response'
            while True:
                try:
                    response = health.get('/health/live')
                    last_result = f'HTTP {response.status_code}'
                    if response.status_code == 200: break
                except httpx.RequestError as exc: last_result = type(exc).__name__
                if time.monotonic() >= deadline or process.poll() is not None:
                    log.flush()
                    pytest.fail(f'Isolated MCP test API did not start ({last_result}, exit={process.poll()}): ' + (tmp_path / 'test-api.log').read_text(encoding='utf-8')[-2500:])
                time.sleep(0.2)
        async def conversation():
            minimal = {key: value for key, value in os.environ.items() if key.upper() in {'PATH', 'SYSTEMROOT', 'WINDIR', 'HOME', 'USERPROFILE', 'TEMP', 'TMP', 'PYTHONPATH'}}
            minimal.update(CLEARANCEX_MCP_API=f'http://127.0.0.1:{port}', CLEARANCEX_MCP_SESSION=token, CLEARANCEX_MCP_ORIGIN='http://localhost:5173')
            params = StdioServerParameters(command=sys.executable, args=['-m', 'context_app.mcp_server'], env=minimal, cwd=str(backend))
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    assert len(tools.tools) == 6
                    result = await session.call_tool('get_field_evidence', {'shipment_id': sid, 'field_id': f'shipment:{sid}:field:GROSS_WEIGHT'})
                    assert not result.isError
                    data = json.loads(result.content[0].text)
                    assert len(data['evidence']) == 3
                    result = await session.call_tool('propose_review_task', {'shipment_id': sid, 'field_id': f'shipment:{sid}:field:GROSS_WEIGHT',
                        'evidence_ids': [data['evidence'][0]['assertion_id']], 'reason': 'Actual MCP client reviewed synthetic evidence.', 'expected_revision': 1})
                    assert not result.isError
                    task = json.loads(result.content[0].text)
                    assert task['status'] == 'pending'
        asyncio.run(conversation())
        tasks = client.get(f'/api/shipments/{sid}/context-status').json()['tasks']
        assert len(tasks) == 1 and tasks[0]['reason'].startswith('Actual MCP')
    finally:
        process.terminate()
        try: process.wait(timeout=10)
        except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=5)
        log.close()
