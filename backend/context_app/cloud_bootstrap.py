"""One-time administrator bootstrap for hosts without an interactive shell.

Set both BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD privately for the
first deployment, then remove them. Existing accounts are never modified.
"""
import os
import uuid
from sqlalchemy import text
from database.connection import init_db, SessionLocal
from .models import Tenant, User, Membership
from .security import passwords


def bootstrap():
    email = os.getenv('BOOTSTRAP_ADMIN_EMAIL', '').strip().lower()
    secret = os.getenv('BOOTSTRAP_ADMIN_PASSWORD', '')
    if not email and not secret:
        return False
    if '@' not in email or len(email) > 254 or len(secret) < 12:
        raise ValueError('Provide an administrator email and a private password of at least 12 characters.')
    with SessionLocal() as db:
        db.execute(text('SELECT pg_advisory_xact_lock(467831211)'))
        if db.query(User).first():
            return False
        tenant = Tenant(id=str(uuid.uuid4()), name='ClearanceX administration')
        db.add(tenant)
        db.flush()
        user = User(id=str(uuid.uuid4()), email=email, password_hash=passwords.hash(secret),
            platform_admin=1, must_change_password=1, disabled=0)
        db.add(user)
        db.flush()
        db.add(Membership(user_id=user.id, tenant_id=tenant.id, role='admin'))
        db.commit()
    return True


if __name__ == '__main__':
    init_db()
    created = bootstrap()
    print('Initial administrator created; password change required.' if created else 'Existing accounts preserved.')
