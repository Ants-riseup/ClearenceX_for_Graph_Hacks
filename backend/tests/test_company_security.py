"""Customer onboarding, platform separation and real company isolation."""
import concurrent.futures
import uuid
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from main import app
from database.connection import SessionLocal
from context_app.admin import create_user
from context_app.graph import GraphRepository
from context_app.models import CompanyEvent, ContextDossier, Membership, Tenant, User
from context_app.security import passwords
from conftest import account, demo

PASSWORD = 'QA-only-admin-password-2026!'


def login(email, password=PASSWORD):
    client = TestClient(app, headers={'Origin': 'http://localhost:5173'}, client=(f'qa-{uuid.uuid4()}', 50000))
    csrf = client.get('/api/auth/csrf').json()['csrf_token']
    response = client.post('/api/auth/login', json={'email': email, 'password': password}, headers={'X-CSRF-Token': csrf})
    if response.status_code == 200:
        client.headers['X-CSRF-Token'] = response.json()['csrf_token']
    return client, response


@pytest.fixture
def operator():
    user, _ = create_user(f'{uuid.uuid4()}@example.test', str(uuid.uuid4()), 'admin', PASSWORD)
    with SessionLocal() as db:
        db.get(User, user['id']).platform_admin = 1; db.commit()
    client, response = login(user['email'])
    assert response.json()['user']['role'] == 'platform_admin'
    return client, user


def add(admin, activate=True, **values):
    response = admin.post('/api/platform/companies', json={'name': str(uuid.uuid4()), 'email': f'{uuid.uuid4()}@example.test', 'admin_password': PASSWORD, **values})
    assert response.status_code == 201, response.text
    result = response.json()
    result['password'] = result['initial_password']
    if activate:
        client, _ = login(result['email'], result['initial_password'])
        personal = 'Personal-test-password-' + uuid.uuid4().hex
        changed = client.post('/api/auth/change-password', json={'current_password': result['initial_password'], 'new_password': personal})
        assert changed.status_code == 200, changed.text
        result['password'] = personal
        client.close()
    return result


def action(admin, company, operation, **values):
    return admin.post(f"/api/platform/companies/{company['id']}/{operation}", json={'expected_version': company['version'], 'admin_password': PASSWORD, **values})


def test_operator_adds_customer_who_can_use_product_without_admin_access(operator):
    admin, _ = operator
    result = add(admin, name='Export Customer', email=f'CASE-{uuid.uuid4()}@EXAMPLE.TEST', password='customer-test-password')
    company, email = result['company'], result['email']
    assert email == email.lower() and result['initial_password'] == 'customer-test-password'
    client, response = login(email, result['password'])
    assert response.json()['user']['role'] == 'user' and response.json()['user']['company_name'] == 'Export Customer'
    assert client.get('/api/dossiers').json()['dossiers'] == []
    sid = demo(client)
    assert client.get(f'/api/shipments/{sid}/context-status').status_code == 200
    assert client.get('/api/platform/companies').status_code == 403
    assert client.post('/api/platform/companies', json={'name': 'escalate', 'email': 'escalate@example.test', 'admin_password': result['password']}).status_code == 403
    assert admin.get('/api/dossiers').status_code == 403
    assert admin.get(f'/api/shipments/{sid}/context-status').status_code == 403
    assert admin.post('/api/demo/dossiers').status_code == 403
    assert admin.get('/api/admin/accounts').status_code == 403
    with SessionLocal() as db:
        user = db.query(User).filter_by(email=email).one()
        assert not user.platform_admin and passwords.verify(user.password_hash, result['password'])
        assert db.get(Membership, (user.id, company['id'])).role == 'user'


def test_customer_roles_and_anonymous_cannot_become_platform_admin(operator):
    admin, _ = operator
    anonymous = TestClient(app)
    assert anonymous.get('/api/platform/companies').status_code == 401
    for role in ['user', 'reviewer', 'viewer', 'admin']:
        client, _ = account(role=role)
        assert client.get('/api/platform/companies').status_code == 403
        assert client.get('/api/platform/events').status_code == 403
        assert client.post('/api/platform/companies', json={}).status_code == 403
        assert client.get('/api/admin/accounts').status_code == 404
    for route in ['signup', 'register']:
        assert anonymous.post(f'/api/auth/{route}', json={'role': 'platform_admin'}).status_code == 403
    for field, value in [('role', 'admin'), ('platform_admin', True), ('tenant_id', 'forged')]:
        assert admin.post('/api/platform/companies', json={'name': 'Forgery', 'email': 'forgery@example.test', 'admin_password': PASSWORD, field: value}).status_code == 422


def test_company_isolation_and_no_secret_listing(operator):
    admin, _ = operator
    first, second = add(admin), add(admin)
    a, _ = login(first['email'], first['password']); b, _ = login(second['email'], second['password'])
    sid = demo(a)
    assert b.get(f'/api/shipments/{sid}/context-status').status_code == 404
    assert b.get('/api/dossiers').json()['dossiers'] == []
    listing = [admin.get('/api/platform/companies', params={'search': result['email']}).json() for result in [first, second]]
    assert first['company']['id'] in str(listing) and second['company']['id'] in str(listing)
    assert all(secret not in str(listing) for secret in [first['password'], second['password'], PASSWORD, 'password_hash'])
    assert action(admin, first['company'], f"users/{second['company']['users'][0]['id']}/reset-password").status_code == 404


def test_disable_restore_and_remove_access_preserve_shipments(operator):
    admin, _ = operator
    result = add(admin); company = result['company']
    customer, _ = login(result['email'], result['password']); sid = demo(customer)
    response = action(admin, company, 'status', status='suspended'); assert response.status_code == 200
    assert customer.get('/api/auth/me').status_code == 401
    assert login(result['email'], result['password'])[1].status_code == 401
    assert action(admin, company, 'status', status='active').status_code == 409
    company = response.json()['company']
    restored = action(admin, company, 'status', status='active'); assert restored.status_code == 200
    customer, _ = login(result['email'], result['password'])
    assert customer.get(f'/api/shipments/{sid}/context-status').status_code == 200
    removed = action(admin, restored.json()['company'], 'status', status='removed'); assert removed.status_code == 200
    assert customer.get('/api/dossiers').status_code == 401
    with SessionLocal() as db:
        assert db.get(ContextDossier, sid) is not None
        assert db.get(Tenant, company['id']).status == 'removed'


def test_reset_password_revokes_session_and_is_not_logged(operator):
    admin, _ = operator
    result = add(admin); company = result['company']; uid = company['users'][0]['id']
    client, _ = login(result['email'], result['password'])
    reset = action(admin, company, f'users/{uid}/reset-password'); assert reset.status_code == 200
    new = reset.json()['initial_password']; assert new != result['password']
    assert client.get('/api/auth/me').status_code == 401
    assert login(result['email'], result['password'])[1].status_code == 401
    assert login(result['email'], new)[1].status_code == 200
    events = admin.get('/api/platform/events').json()['events']
    assert {e['action'] for e in events} >= {'customer_added', 'customer_password_reset'}
    with SessionLocal() as db:
        details = str([event.details for event in db.query(CompanyEvent).filter_by(company_id=company['id'])])
        assert new not in details and result['password'] not in details and PASSWORD not in details


def test_duplicate_email_and_invalid_company_changes_are_atomic(operator):
    admin, _ = operator
    first = add(admin)
    before = admin.get('/api/platform/companies').json()['total']
    assert admin.post('/api/platform/companies', json={'name': 'Duplicate', 'email': first['email'], 'admin_password': PASSWORD}).status_code == 409
    assert admin.get('/api/platform/companies').json()['total'] == before
    assert action(admin, first['company'], 'profile', name='Updated exporter', contact_name='Contact').status_code == 200
    assert action(admin, first['company'], 'profile', name='Stale', contact_name='').status_code == 409
    assert admin.post('/api/platform/companies', json={'name': '  ', 'email': 'blank@example.test', 'admin_password': PASSWORD}).status_code == 422


def test_password_reentry_csrf_origin_and_rate_limits(operator):
    admin, _ = operator
    body = {'name': 'Customer', 'email': 'confirm@example.test', 'admin_password': PASSWORD}
    csrf = admin.headers.pop('X-CSRF-Token')
    assert admin.post('/api/platform/companies', json=body).status_code == 403
    admin.headers['X-CSRF-Token'] = csrf
    assert admin.post('/api/platform/companies', json=body, headers={'Origin': 'https://attacker.example'}).status_code == 403
    for _ in range(10):
        assert admin.post('/api/platform/companies', json={**body, 'admin_password': 'wrong'}).status_code == 403
    assert admin.post('/api/platform/companies', json=body).status_code == 429


def test_sql_and_cypher_injection_are_data(operator):
    admin, _ = operator
    for payload in ["' OR 1=1 --", "'; DROP TABLE cx_users; --", '%', '_']:
        response = admin.get('/api/platform/companies', params={'search': payload})
        assert response.status_code == 200 and response.json()['total'] == 0
    assert login("' OR '1'='1' --@example.test", 'anything')[1].status_code == 401
    customer, _ = account(); sid = demo(customer)
    assert customer.get('/api/dossiers', params={'search': "'; DROP TABLE cx_users; --"}).json()['dossiers'] == []
    assert customer.get('/api/dossiers', params={'sort': 'created_at; DROP TABLE cx_users'}).status_code == 422
    assert customer.get(f'/api/shipments/{sid}/context-evidence', params={'field_id': "') MATCH (n) DETACH DELETE n //"}).status_code in {200, 404, 422}
    with pytest.raises(HTTPException) as exc:
        GraphRepository('safe-test-tenant').query('../security', sid, 1)
    assert exc.value.status_code == 422


def test_concurrent_customer_updates_reject_stale_version(operator):
    admin, _ = operator
    company = add(admin)['company']
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(lambda: action(admin, company, 'status', status='suspended').status_code)
        b = pool.submit(lambda: action(admin, company, 'status', status='removed').status_code)
        assert sorted([a.result(), b.result()]) == [200, 409]


def test_company_status_does_not_lock_out_platform_operator(operator):
    admin, user = operator
    with SessionLocal() as db:
        home = db.get(Tenant, user['tenant_id']); revision = home.version
    assert action(admin, {'id': user['tenant_id'], 'version': revision}, 'status', status='suspended').status_code == 200
    assert admin.get('/api/platform/companies').status_code == 200
    assert login(user['email'])[1].json()['user']['role'] == 'platform_admin'


def test_status_filter_applies_before_pagination_and_events_name_customer(operator):
    admin, _ = operator
    prefix = f'Filter {uuid.uuid4()}'
    first = add(admin, name=prefix + ' Active')
    second = add(admin, name=prefix + ' Disabled')
    assert action(admin, second['company'], 'status', status='suspended').status_code == 200
    active = admin.get('/api/platform/companies', params={'search': prefix, 'status': 'active', 'limit': 1}).json()
    disabled = admin.get('/api/platform/companies', params={'search': prefix, 'status': 'suspended', 'limit': 1}).json()
    assert active['total'] == disabled['total'] == 1
    assert active['companies'][0]['id'] == first['company']['id']
    assert disabled['companies'][0]['id'] == second['company']['id']
    assert admin.get('/api/platform/companies', params={'status': "active'; DROP TABLE cx_tenants"}).status_code == 422
    assert any(event['company_name'] == second['company']['name'] for event in admin.get('/api/platform/events').json()['events'])


def test_temporary_login_requires_password_change_and_rotates_all_sessions(operator):
    admin, _ = operator
    result = add(admin, activate=False)
    first, response = login(result['email'], result['initial_password'])
    second, _ = login(result['email'], result['initial_password'])
    assert response.json()['user']['requires_password_change'] is True
    assert first.get('/api/auth/me').json()['user']['requires_password_change'] is True
    assert first.get('/api/dossiers').status_code == 403
    assert first.post('/api/demo/dossiers').status_code == 403
    assert first.get('/api/platform/companies').status_code == 403
    old_csrf = first.headers['X-CSRF-Token']
    personal = 'Sample2004'  # Ten-character customer password boundary.
    changed = first.post('/api/auth/change-password', json={'current_password': result['initial_password'], 'new_password': personal})
    assert changed.status_code == 200 and changed.json()['user']['requires_password_change'] is False
    assert old_csrf != changed.json()['csrf_token']
    assert second.get('/api/auth/me').status_code == 401
    assert first.post('/api/demo/dossiers').status_code == 403  # old CSRF cannot authorize a mutation
    first.headers['X-CSRF-Token'] = changed.json()['csrf_token']
    assert first.post('/api/demo/dossiers').status_code == 201
    assert login(result['email'], result['initial_password'])[1].status_code == 401
    fresh, response = login(result['email'], personal)
    assert response.json()['user']['requires_password_change'] is False and fresh.get('/api/dossiers').status_code == 200
    with SessionLocal() as db:
        user = db.query(User).filter_by(email=result['email']).one()
        assert not user.must_change_password and passwords.verify(user.password_hash, personal)
        assert personal not in str([entry.details for entry in db.query(CompanyEvent).filter_by(company_id=result['company']['id'])])


def test_password_change_checks_current_secret_policy_csrf_and_no_forged_user(operator):
    admin, _ = operator
    result = add(admin, activate=False)
    client, _ = login(result['email'], result['initial_password'])
    body = {'current_password': result['initial_password'], 'new_password': 'A private customer passphrase'}
    csrf = client.headers.pop('X-CSRF-Token')
    assert client.post('/api/auth/change-password', json=body).status_code == 403
    client.headers['X-CSRF-Token'] = csrf
    assert client.post('/api/auth/change-password', json=body, headers={'Origin': 'https://attacker.example'}).status_code == 403
    assert client.post('/api/auth/change-password', json={**body, 'current_password': 'wrong'}).status_code == 403
    assert client.post('/api/auth/change-password', json={**body, 'new_password': 'short'}).status_code == 422
    assert client.post('/api/auth/change-password', json={**body, 'new_password': 'Sample200'}).status_code == 422
    assert client.post('/api/auth/change-password', json={**body, 'new_password': ' ' * 12}).status_code == 422
    assert client.post('/api/auth/change-password', json={**body, 'new_password': result['initial_password']}).status_code == 422
    assert client.post('/api/auth/change-password', json={**body, 'user_id': 'other-user', 'role': 'admin'}).status_code == 422
    assert client.get('/api/dossiers').status_code == 403
    assert client.get('/api/auth/me').json()['user']['requires_password_change'] is True


def test_admin_reset_reinstates_first_login_password_requirement(operator):
    admin, _ = operator
    result = add(admin)
    client, _ = login(result['email'], result['password'])
    company = next(row for row in admin.get('/api/platform/companies', params={'search': result['email']}).json()['companies'] if row['id'] == result['company']['id'])
    reset = action(admin, company, f"users/{company['users'][0]['id']}/reset-password")
    assert reset.status_code == 200 and client.get('/api/auth/me').status_code == 401
    client, response = login(result['email'], reset.json()['initial_password'])
    assert response.json()['user']['requires_password_change'] is True
    assert client.get('/api/dossiers').status_code == 403
    assert client.post('/api/auth/logout').status_code == 200


def test_password_change_wrong_secret_attempts_are_throttled(operator):
    admin, _ = operator
    result = add(admin, activate=False)
    client, _ = login(result['email'], result['initial_password'])
    for _ in range(10):
        assert client.post('/api/auth/change-password', json={'current_password': 'wrong', 'new_password': 'A private customer passphrase'}).status_code == 403
    assert client.post('/api/auth/change-password', json={'current_password': result['initial_password'], 'new_password': 'A private customer passphrase'}).status_code == 429
    assert client.get('/api/auth/me').json()['user']['requires_password_change'] is True
