"""Local operator -> customer login -> product -> access revocation smoke.

Creates two labeled QA customers and leaves both access-disabled. No paid calls.
Credentials are read from an ignored private JSON file, never logged.
"""
import argparse
import json
import uuid
import time
import secrets
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--credentials', default='tmp/admin-access.json')
    parser.add_argument('--pdf-folder', help='Optional authorized digital PDFs to upload through the new customer account')
    args = parser.parse_args()
    private = json.loads(Path(args.credentials).read_text(encoding='utf-8-sig'))
    origin, checks = 'http://localhost:8080', []

    def expect(response, code, label):
        assert response.status_code == code, f'{label}: expected {code}, received {response.status_code}'
        checks.append(label)
        return response

    def login(email, password):
        client = httpx.Client(base_url=origin, headers={'Origin': origin}, timeout=30)
        csrf = client.get('/api/auth/csrf').json()['csrf_token']
        response = client.post('/api/auth/login', json={'email': email, 'password': password}, headers={'X-CSRF-Token': csrf})
        expect(response, 200, 'Account can sign in')
        client.headers['X-CSRF-Token'] = response.json()['csrf_token']
        return client, response.json()['user']

    def choose_private_password(client, temporary):
        expect(client.get('/api/dossiers'), 403, 'Temporary login cannot open shipment workspace')
        changed = expect(client.post('/api/auth/change-password', json={'current_password': temporary, 'new_password': secrets.token_urlsafe(24)}), 200, 'Customer chooses a private password before continuing')
        assert changed.json()['user']['requires_password_change'] is False
        client.headers['X-CSRF-Token'] = changed.json()['csrf_token']
        expect(client.get('/api/auth/me'), 200, 'Rotated session remains signed in after password setup')

    admin, identity = login(private['email'], private['password'])
    assert identity['role'] == 'platform_admin'
    created, clients = [], []
    try:
        expect(admin.get('/api/platform/companies'), 200, 'Operator dashboard data loads')
        expect(admin.get('/api/dossiers'), 403, 'Operator cannot enter customer shipment APIs')
        with httpx.Client(base_url=origin, timeout=20) as anonymous:
            expect(anonymous.get('/api/platform/companies'), 401, 'Anonymous customer management denied')
            expect(anonymous.post('/api/auth/signup', json={}), 403, 'Public signup restricted')
        for number in range(2):
            email = f'qa-customer-{uuid.uuid4().hex[:10]}@example.test'
            result = expect(admin.post('/api/platform/companies', json={'name': f'QA Export Company {number + 1}', 'email': email, 'admin_password': private['password']}), 201, 'Operator creates customer user').json()
            created.append(result)
            client, customer = login(email, result['initial_password']); clients.append(client)
            assert customer['role'] == 'user'
            assert customer['requires_password_change'] is True
            choose_private_password(client, result['initial_password'])
            expect(client.get('/api/dossiers'), 200, 'Customer can open shipment product')
            expect(client.get('/api/platform/companies'), 403, 'Customer cannot enter administration')
        first = created[0]['company']
        sid = expect(clients[0].post('/api/demo/dossiers'), 201, 'Customer creates labeled test shipment').json()['shipment_id']
        expect(clients[1].get(f'/api/shipments/{sid}/context-status'), 404, 'Other company cannot read shipment')
        uid = first['users'][0]['id']
        result = expect(admin.post(f"/api/platform/companies/{first['id']}/users/{uid}/reset-password", json={'expected_version': first['version'], 'admin_password': private['password']}), 200, 'Operator resets customer password').json()
        expect(clients[0].get('/api/auth/me'), 401, 'Reset revokes customer session')
        replacement, _ = login(created[0]['email'], result['initial_password']); clients.append(replacement)
        choose_private_password(replacement, result['initial_password'])
        expect(replacement.get(f'/api/shipments/{sid}/context-status'), 200, 'Customer retains own shipment after reset')
        if args.pdf_folder:
            pdfs = sorted(Path(args.pdf_folder).glob('*.pdf'))
            assert 1 <= len(pdfs) <= 10, 'Select a folder with 1–10 PDFs.'
            with ExitStack() as stack:
                files = [('files', (path.name, stack.enter_context(path.open('rb')), 'application/pdf')) for path in pdfs]
                upload = expect(replacement.post('/api/upload', files=files), 202, 'New customer uploads actual input PDFs').json()
            shipment_id = upload['shipment_id']
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline:
                progress = replacement.get(f'/api/upload/{shipment_id}/status').json()
                if progress['status'] == 'done':
                    assert progress['completed_documents'] == len(pdfs)
                    checks.append('All actual input PDFs extracted for newly added customer')
                    break
                assert progress['status'] not in {'error', 'failed'}, 'Customer PDF processing failed.'
                time.sleep(2)
            else:
                raise AssertionError('Customer PDF processing exceeded the verification deadline.')
            expect(clients[1].get(f'/api/shipments/{shipment_id}/status'), 404, 'Other company cannot read uploaded PDF job')
        expect(admin.get('/api/platform/events'), 200, 'Operator activity loads')
        literal = expect(admin.get('/api/platform/companies', params={'search': "' OR 1=1 --"}), 200, 'SQL-shaped search treated as data')
        assert literal.json()['total'] == 0
    finally:
        for entry in created:
            listing = admin.get('/api/platform/companies', params={'search': entry['email']}).json()['companies']
            company = next(row for row in listing if row['id'] == entry['company']['id'])
            expect(admin.post(f"/api/platform/companies/{company['id']}/status", json={'status': 'suspended', 'expected_version': company['version'], 'admin_password': private['password']}), 200, 'QA customer access disabled; records preserved')
        for client in clients:
            expect(client.get('/api/auth/me'), 401, 'Disabled QA sessions denied'); client.close()
        admin.post('/api/auth/logout').raise_for_status(); admin.close()
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'scope': 'Running local operator/customer HTTP flow; no browser or paid inference', 'passed': len(checks), 'checks': checks, 'qa_customers_left_disabled': True}
    Path('output/verification/customer-runtime.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'Passed {len(checks)} running customer access checks; QA access disabled; no credentials logged.')


if __name__ == '__main__':
    main()
