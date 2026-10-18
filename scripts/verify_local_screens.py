"""Exercise local QA dossiers through the frontend proxy, without model calls.

Requires the existing private tmp/local-access.txt account. Creates one local
test batch containing a reviewed QA dossier and an intentionally blocked one.
"""
from pathlib import Path
import hashlib
import io
import json
import time
import uuid
import zipfile
from xml.etree import ElementTree as ET
import httpx

ROOT = Path(__file__).resolve().parents[1]
READY = '04c681ac-cbf6-444a-8dbc-8a0c1998566c'
BLOCKED = '70228036-5821-4401-a0f5-b64ad5056c0f'


def main():
    credentials = dict(line.split(':', 1) for line in (ROOT / 'tmp/local-access.txt').read_text().splitlines() if ':' in line)
    credentials = {k.strip(): v.strip() for k, v in credentials.items()}
    report = {'date': '2026-10-18', 'paid_model_calls': 0, 'browser_verified': False, 'checks': {}}
    with httpx.Client(base_url='http://localhost:8080', trust_env=False, timeout=40, headers={'Origin': 'http://localhost:8080'}) as c:
        def get(path):
            response = c.get('/api' + path)
            response.raise_for_status()
            return response.json()

        def post(path, payload):
            response = c.post('/api' + path, json=payload)
            response.raise_for_status()
            return response.json()

        def synced(sid):
            for _ in range(100):
                state = get(f'/shipments/{sid}/context-status')
                if state['status'] == 'synced':
                    return state['source_revision']
                time.sleep(.2)
            raise AssertionError('Graph synchronization timed out')

        c.headers['X-CSRF-Token'] = get('/auth/csrf')['csrf_token']
        login = post('/auth/login', {'email': credentials['Email'], 'password': credentials['Password']})
        c.headers['X-CSRF-Token'] = login['csrf_token']
        synced(READY)
        graph = get(f'/shipments/{READY}/graph')
        ids = {n['id'] for n in graph['nodes']}
        assert len(ids) == len(graph['nodes']) and len(ids) > 20 and graph['edges']
        assert all(e['from'] in ids and e['to'] in ids for e in graph['edges'])
        assert {'shipment', 'document', 'canonicalfield', 'assertion', 'goodsreview'} <= {n['type'] for n in graph['nodes']}
        report['checks']['graph'] = {'nodes': len(ids), 'edges': len(graph['edges']), 'all_edge_targets_exist': True}

        audit = get(f'/shipments/{BLOCKED}/audit-trail')
        assert audit['total_events'] == len(audit['entries']) > 0
        assert any(e['action'] == 'decision_approved' for e in audit['entries'])
        assert any(e['action'] == 'cusdeclineitem_saved' for e in audit['entries'])
        assert all(e['timestamp'] and e['module'] and e['outcome'] for e in audit['entries'])
        report['checks']['audit'] = {'events': len(audit['entries']), 'browser_review_decision_and_goods_saves_present': True}

        assert get(f'/shipments/{READY}/cusdec-readiness')['export_allowed']
        assert not get(f'/shipments/{BLOCKED}/cusdec-readiness')['export_allowed']
        payload = {'request_id': str(uuid.uuid4()), 'dossiers': {READY: synced(READY), BLOCKED: synced(BLOCKED)}}
        batch = post('/batch-exports', payload)
        assert batch['status'] == 'partial'
        assert {i['shipment_id']: i['status'] for i in batch['items']} == {READY: 'prepared', BLOCKED: 'blocked'}
        assert post('/batch-exports', payload) == batch
        response = c.get(f"/api/batch-exports/{batch['batch_id']}/content")
        response.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            manifest = json.loads(archive.read('manifest.json'))
            xml_names = [n for n in archive.namelist() if n.endswith('.xml')]
            assert manifest == batch and len(xml_names) == 1
            assert len(ET.fromstring(archive.read(xml_names[0])).findall('Item')) == 2
        report['checks']['batch'] = {'id': batch['batch_id'], 'status': batch['status'], 'prepared': READY, 'blocked': BLOCKED, 'xml_count': 1, 'manifest_matches': True, 'repeat_request_idempotent': True, 'sha256': hashlib.sha256(response.content).hexdigest()}
        empty = c.post('/api/upload', files=[])
        malformed = c.post('/api/upload', files=[('files', ('invalid.pdf', b'not a PDF', 'application/pdf'))])
        assert empty.status_code == 422 and malformed.status_code in {400, 422}
        report['checks']['upload_invalid_inputs'] = {'empty_status': empty.status_code, 'malformed_status': malformed.status_code}
        report['checks']['routes'] = {}
        for path in ['/dossiers', '/knowledge-graph', '/batch-filing', '/audit-trail', '/tariff-directory']:
            response = c.get(path)
            response.raise_for_status()
            assert '<div id="root">' in response.text
            report['checks']['routes'][path] = response.status_code
        c.post('/api/auth/logout')
    report['status'] = 'passed'
    target = ROOT / 'output/verification/local-screens-runtime.json'
    target.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
