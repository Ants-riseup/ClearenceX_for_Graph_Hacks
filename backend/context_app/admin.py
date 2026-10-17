"""Explicit local administration; no shared default passwords or public signup."""
import argparse
import secrets
import uuid
from database.connection import init_db, SessionLocal
from .models import Tenant, User, Membership
from .security import passwords


def create_user(email, tenant_name, role="reviewer", password=None):
    secret = password or secrets.token_urlsafe(20)
    with SessionLocal() as db:
        email = email.strip().lower()
        if db.query(User).filter_by(email=email).first():
            raise ValueError("Account already exists; existing credentials were preserved.")
        tenant = db.query(Tenant).filter_by(name=tenant_name).first()
        if not tenant:
            tenant = Tenant(id=str(uuid.uuid4()), name=tenant_name)
            db.add(tenant)
            db.flush()
        uid = str(uuid.uuid4())
        db.add(User(id=uid, email=email, password_hash=passwords.hash(secret), disabled=0))
        db.flush()
        db.add(Membership(user_id=uid, tenant_id=tenant.id, role=role))
        db.commit()
        return {"id": uid, "email": email, "tenant_id": tenant.id, "role": role}, secret


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["migrate", "migration-status", "create-user", "recover-uploads", 'reconcile-graphs'])
    parser.add_argument("--email")
    parser.add_argument("--tenant", default="ClearanceX team")
    parser.add_argument("--role", choices=["reviewer", "viewer", "admin"], default="reviewer")
    args = parser.parse_args()
    init_db()
    if args.command == "create-user":
        if not args.email:
            parser.error("--email is required")
        user, password = create_user(args.email, args.tenant, args.role)
        print(f"Account: {user['email']}\nGenerated password (save privately): {password}")
    elif args.command == 'migration-status':
        from migrations import status
        from database.connection import engine
        for revision in status(engine):
            print(revision['version'], revision['name'], revision['applied_at'])
    elif args.command == 'reconcile-graphs':
        from .service import reconcile_graph_projections
        print('Missing graph projections queued:', reconcile_graph_projections())
    elif args.command == "recover-uploads":
        # Run only after stopping all API/ingestion processes.
        from database.models import Dossier, DossierDocument
        from .models import BatchJob
        with SessionLocal() as db:
            db.query(Dossier).filter_by(status="processing").update({"status": "interrupted"})
            db.query(DossierDocument).filter_by(status="processing").update({"status": "error", "error_message": "Processing interrupted. Retry this upload."})
            db.query(BatchJob).filter_by(status='processing').update({'status': 'interrupted'})
            db.commit()
        print("Interrupted uploads can now be retried. Start one API instance.")
    else:
        print("Additive ClearanceX tables are ready; historical tables/data were preserved.")
