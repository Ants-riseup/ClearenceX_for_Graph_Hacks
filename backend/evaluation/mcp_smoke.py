"""Packaged Linux MCP smoke: real stdio client, authenticated HTTP and graph."""
import asyncio
import json
import os
import sys
import time
import uuid
import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from context_app.admin import create_user


async def main():
    user, password = create_user(f'mcp-smoke-{uuid.uuid4()}@example.test', f'MCP smoke {uuid.uuid4()}')
    with httpx.Client(base_url='http://127.0.0.1:8000', trust_env=False, timeout=10, headers={'Origin': 'http://localhost:8080'}) as client:
        csrf = client.get('/api/auth/csrf').json()['csrf_token']
        result = client.post('/api/auth/login', json={'email': user['email'], 'password': password}, headers={'X-CSRF-Token': csrf})
        result.raise_for_status()
        client.headers['X-CSRF-Token'] = result.json()['csrf_token']
        result = client.post('/api/demo/dossiers'); result.raise_for_status(); sid = result.json()['shipment_id']
        deadline = time.monotonic() + 30
        while client.get(f'/api/shipments/{sid}/context-status').json()['status'] != 'synced':
            if time.monotonic() > deadline: raise RuntimeError('MCP fixture projection timed out')
            await asyncio.sleep(0.2)
        env = {k: v for k, v in os.environ.items() if k in {'PATH', 'HOME', 'LANG'}}
        env.update(CLEARANCEX_MCP_API='http://127.0.0.1:8000', CLEARANCEX_MCP_SESSION=client.cookies.get('clearancex_dev_session'), CLEARANCEX_MCP_ORIGIN='http://localhost:8080')
        async with stdio_client(StdioServerParameters(command=sys.executable, args=['-m', 'context_app.mcp_server'], env=env, cwd='/app')) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                assert len(tools.tools) == 6
                result = await session.call_tool('get_field_evidence', {'shipment_id': sid, 'field_id': f'shipment:{sid}:field:GROSS_WEIGHT'})
                assert not result.isError
                evidence = json.loads(result.content[0].text)['evidence']; assert len(evidence) == 3
                result = await session.call_tool('propose_review_task', {'shipment_id': sid, 'field_id': f'shipment:{sid}:field:GROSS_WEIGHT',
                    'evidence_ids': [evidence[0]['assertion_id']], 'reason': 'Actual packaged MCP client reviewed synthetic evidence.', 'expected_revision': 1})
                assert not result.isError
                task = json.loads(result.content[0].text); assert task['status'] == 'pending'
                # Logout revokes the same cookie at the actual API boundary.
                result = client.post('/api/auth/logout'); result.raise_for_status()
                denied = await session.call_tool('list_dossier_issues', {'shipment_id': sid})
                assert denied.isError
        print(json.dumps({'status': 'passed', 'transport': 'real stdio MCP -> authenticated HTTP -> real FalkorDB',
            'tools': len(tools.tools), 'assertions': len(evidence), 'task_status': task['status'], 'logout_replay': 'denied', 'paid_calls': 0}))


if __name__ == '__main__':
    asyncio.run(main())
