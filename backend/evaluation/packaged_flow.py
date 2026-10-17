"""Actual packaged API workflow, with two explicitly enabled live agent runs."""
import json
import time
import uuid
from pathlib import Path
import httpx
from context_app.admin import create_user


def main():
    user, password = create_user(f'flow-{uuid.uuid4()}@example.test', f'Packaged flow {uuid.uuid4()}')
    report = {'transport': 'actual packaged HTTP API', 'steps': [], 'live_runs': []}
    with httpx.Client(base_url='http://127.0.0.1:8000', trust_env=False, timeout=15, headers={'Origin': 'http://localhost:8080'}) as client:
        def get(path):
            response = client.get(path); response.raise_for_status(); return response.json()
        def post(path, body=None, **kwargs):
            response = client.post(path, json=body, **kwargs); response.raise_for_status(); return response.json()
        def login():
            client.headers['X-CSRF-Token'] = get('/api/auth/csrf')['csrf_token']
            data = post('/api/auth/login', {'email': user['email'], 'password': password})
            client.headers['X-CSRF-Token'] = data['csrf_token']
        login(); report['steps'].append('real_login')
        sid = post('/api/demo/dossiers')['shipment_id']; base = f'/api/shipments/{sid}'
        def synced():
            deadline = time.monotonic() + 45
            while True:
                state = get(base + '/context-status')
                if state['status'] == 'synced': return state
                if time.monotonic() > deadline: raise RuntimeError('Graph synchronization timed out')
                time.sleep(0.2)
        synced()
        def investigate(question):
            run = post(base + '/agent-runs', {'question': question})
            deadline = time.monotonic() + 80
            while True:
                result = get(base + '/agent-runs/' + run['run_id'])
                if result['status'] != 'running': break
                if time.monotonic() > deadline: raise RuntimeError('Investigation did not finish within the test budget')
                time.sleep(0.25)
            report['live_runs'].append({'status': result['status'], 'model': result['result'].get('model'),
                'tools': [e['tool'] for e in result['result'].get('tool_events', [])], 'usage': result['result'].get('usage'),
                'citations': len(result['result'].get('citations', [])), 'proposed_action': bool(result['result'].get('proposed_action'))})
            if result['status'] != 'completed' or not result['result'].get('proposed_action'):
                raise RuntimeError('Live model did not complete a cited proposal: ' + str(result['result'].get('error', 'proposal absent')))
            synced(); return result
        investigate('Investigate the gross weight conflict using the graph, retrieve its evidence, and propose a review task. Do not approve it.')
        report['steps'].append('live_model_selected_graph_tools_and_proposed')
        def approve(field, kind):
            fid = f'shipment:{sid}:field:{field}'
            evidence = get(base + '/context-evidence?field_id=' + fid)['evidence']
            source = next(e for e in evidence if e['document_type'] == kind)
            pdf = client.get(f"/api/documents/{source['document_id']}/content"); assert pdf.status_code == 200 and pdf.content.startswith(b'%PDF-')
            state = synced()
            task = post(base + '/review-tasks', {'field_id': fid, 'evidence_ids': [source['assertion_id']], 'reason': 'Automated test exercised the reviewer API against a synthetic source.', 'expected_revision': state['source_revision']})
            state = synced()
            decision = post(base + f"/review-tasks/{task['id']}/decision", {'field_id': fid, 'assertion_id': source['assertion_id'],
                'reason': 'Automated reviewer API test selected this synthetic source.', 'expected_revision': state['source_revision'], 'request_id': str(uuid.uuid4())})
            synced(); return decision
        weight = approve('GROSS_WEIGHT', 'packing_list')
        package = approve('PACKAGE_COUNT', 'commercial_invoice')
        report['steps'].append('private_PDF_delivery_and_two_reviewer_API_approvals')
        response = client.post(base + '/demo-correction', params={'expected_revision': synced()['source_revision']}); response.raise_for_status()
        state = synced(); decisions = {d['id']: d for d in state['decisions']}
        assert decisions[weight['id']]['validity_state'] == 'stale'
        assert decisions[package['id']]['validity_state'] == 'current'
        blockers = get(base + '/cusdec-readiness')['blockers']; assert any(b['code'] == 'STALE_APPROVAL' for b in blockers)
        report['steps'].append('source_correction_stales_weight_preserves_packages_blocks_export')
        investigate('The packing list was corrected. Read the graph issues, inspect the old source change impact and current evidence, then propose a gross weight re-review task. Explain that the earlier weight approval is stale while package count remains current. Do not approve anything.')
        assert 'get_change_impact' in report['live_runs'][-1]['tools']
        report['steps'].append('live_graph_change_impact_and_rereview_proposal')
        post('/api/auth/logout'); login()
        memories = get(base + '/context-memory')['memory']
        assert package['id'] in {m['decision_id'] for m in memories}
        assert weight['id'] not in {m['decision_id'] for m in memories}
        report['steps'].append('new_session_recalls_current_memory_excludes_stale')
        report.update(status='passed', shipment_id=sid, tenant_id=user['tenant_id'], actor_id=user['id'],
            estimated_usd=sum(r['usage']['estimated_usd'] for r in report['live_runs']))
        Path('/data/uploads/packaged-validation.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report))


if __name__ == '__main__': main()
