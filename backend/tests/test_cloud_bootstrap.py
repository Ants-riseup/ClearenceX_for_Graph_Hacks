import uuid
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database.connection import engine
from database.models import Base
from context_app import cloud_bootstrap
from context_app.models import User
from context_app.security import passwords


def test_bootstrap_only_initializes_empty_database(monkeypatch):
    # Separate schema in the asserted isolated test DB; no existing users touched.
    schema = 'bootstrap_' + uuid.uuid4().hex
    with engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA {schema}'))
    isolated = create_engine(engine.url, connect_args={'options': f'-csearch_path={schema}'})
    sessions = sessionmaker(bind=isolated)
    try:
        Base.metadata.create_all(isolated)
        monkeypatch.setattr(cloud_bootstrap, 'SessionLocal', sessions)
        monkeypatch.setenv('BOOTSTRAP_ADMIN_EMAIL', 'initial@example.test')
        monkeypatch.setenv('BOOTSTRAP_ADMIN_PASSWORD', 'Private-test-password-42!')
        assert cloud_bootstrap.bootstrap() is True
        with sessions() as db:
            user = db.query(User).one()
            original_hash = user.password_hash
            assert user.platform_admin == 1 and user.must_change_password == 1
            assert passwords.verify(user.password_hash, 'Private-test-password-42!')
        monkeypatch.setenv('BOOTSTRAP_ADMIN_EMAIL', 'attacker@example.test')
        monkeypatch.setenv('BOOTSTRAP_ADMIN_PASSWORD', 'Different-private-password-42!')
        assert cloud_bootstrap.bootstrap() is False
        with sessions() as db:
            assert db.query(User).count() == 1
            assert db.query(User).one().password_hash == original_hash
    finally:
        isolated.dispose()
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA {schema} CASCADE'))
