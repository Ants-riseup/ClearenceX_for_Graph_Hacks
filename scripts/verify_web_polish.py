"""Read-only running-service checks for graph preview and existing login boundaries."""
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import httpx


def main():
    origin = 'http://localhost:8080'
    admin = json.loads(Path('tmp/admin-access.json').read_text(encoding='utf-8-sig'))
    text = Path('tmp/local-access.txt').read_text(encoding='utf-8-sig')
    customer = {field.lower(): re.search(r'^' + field + r':\s*(.+)$', text, re.M).group(1).strip() for field in ['Email', 'Password']}
    checks, counts = [], {}

    def expect(response, code, description):
        assert response.status_code == code, f'{description}: HTTP {response.status_code}'
        checks.append(description)
        return response

    for credentials, role in [(admin, 'platform_admin'), (customer, 'reviewer')]:
        with httpx.Client(base_url=origin, headers={'Origin': origin}, timeout=20) as client:
            csrf = client.get('/api/auth/csrf').json()['csrf_token']
            result = expect(client.post('/api/auth/login', json={field: credentials[field] for field in ['email', 'password']}, headers={'X-CSRF-Token': csrf}), 200, 'Existing local login preserved').json()
            assert result['user']['role'] == role and result['user']['requires_password_change'] is False
            client.headers['X-CSRF-Token'] = result['csrf_token']
            if role == 'platform_admin':
                listing = expect(client.get('/api/platform/companies', params={'status': 'active'}), 200, 'Active customer filter available').json()
                assert all(company['status'] == 'active' for company in listing['companies'])
                expect(client.get('/api/dossiers'), 403, 'Platform account denied customer shipment data')
                expect(client.get('/api/platform/events'), 200, 'Administration history available')
            else:
                expect(client.get('/api/platform/companies'), 403, 'Customer denied platform administration')
                dossiers = expect(client.get('/api/dossiers', params={'limit': 50}), 200, 'Customer shipment list available').json()['dossiers']
                ready = next(row for row in dossiers if row['export_allowed'])
                path = f"/api/shipments/{ready['dossier_id']}"
                context = expect(client.get(path + '/context-status'), 200, 'Reviewed shipment context loads').json()
                source = next(doc for doc in context['documents'] if doc['document_type'] == 'packing_list')
                params = {'document_id': source['document_id'], 'expected_revision': context['source_revision']}
                impact = expect(client.get(path + '/change-impact', params=params), 200, 'Actual graph dependencies previewed').json()['impact']
                assert impact, 'Reviewed packing list must have graph dependencies.'
                counts = dict(Counter(record['type'] for record in impact))
                expect(client.get(path + '/change-impact', params={**params, 'expected_revision': context['source_revision'] + 1}), 409, 'Stale graph preview rejected')
                assert client.get(path + '/context-status').json()['source_revision'] == context['source_revision']
                checks.append('Graph preview leaves source revision unchanged')
            expect(client.post('/api/auth/logout'), 200, 'Verification session signed out')
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'scope': 'Actual HTTP/data checks; no browser visual verification or paid calls', 'passed': len(checks), 'checks': checks, 'graph_dependency_types': counts}
    Path('output/verification/web-polish-runtime.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'Passed {len(checks)} read-only web/API checks; graph dependency types: {counts}; no credentials logged.')


if __name__ == '__main__':
    main()
