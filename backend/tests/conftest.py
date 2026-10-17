"""Integration tests require the isolated services in tests/compose.yaml."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DATABASE_URL", "postgresql://test:clearancex_local_test_only@localhost:5449/clearancex_test")
os.environ.setdefault("FALKORDB_PORT", "6399")
os.environ.setdefault("FALKORDB_PASSWORD", "clearancex_graph_test_only")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")
os.environ.setdefault("UPLOAD_ROOT", str(Path(__file__).parent / ".test_uploads"))
os.environ["ENABLE_LIVE_AGENT"] = "false"
os.environ["CLEARANCEX_LOCAL_EXTRACTION"] = "true"

import pytest
from fastapi.testclient import TestClient
from main import app
from database.connection import init_db, SessionLocal
from context_app.admin import create_user
from context_app.models import ContextDossier, Outbox, LoginAttempt
from context_app.graph import GraphRepository
import uuid


@pytest.fixture(scope="session", autouse=True)
def schema():
    assert "clearancex_test" in os.environ["DATABASE_URL"], "Tests must use an isolated test database."
    init_db()
    with SessionLocal() as db:
        # Only this asserted isolated database is touched. Repeated test runs
        # must not inherit login throttles from a previous run's shared test IP.
        db.query(LoginAttempt).delete()
        db.commit()


def account(tenant=None, role="reviewer"):
    email = f"{uuid.uuid4()}@example.test"
    user, password = create_user(email, tenant or str(uuid.uuid4()), role)
    client = TestClient(app, headers={"Origin": "http://localhost:5173"}, client=(f'test-{uuid.uuid4()}', 50000))
    csrf = client.get("/api/auth/csrf").json()["csrf_token"]
    result = client.post("/api/auth/login", json={"email": email, "password": password}, headers={"X-CSRF-Token": csrf})
    assert result.status_code == 200, result.text
    client.headers["X-CSRF-Token"] = result.json()["csrf_token"]
    return client, user


@pytest.fixture
def reviewer():
    return account()


def sync(sid):
    with SessionLocal() as db:
        row = db.query(ContextDossier).filter_by(id=sid).with_for_update().one()
        GraphRepository(row.tenant_id).project(row)
        row.graph_revision = row.revision
        db.query(Outbox).filter_by(dossier_id=sid).update({"status": "done"})
        db.commit()


def demo(client):
    result = client.post("/api/demo/dossiers")
    assert result.status_code == 201, result.text
    sid = result.json()["shipment_id"]
    sync(sid)
    return sid
