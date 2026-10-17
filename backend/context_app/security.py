import hashlib
import hmac
import secrets
import time
import uuid
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import or_
from database.connection import SessionLocal
from .models import User, Membership, Session, LoginAttempt, ContextDossier
from .config import SESSION_COOKIE, CSRF_COOKIE, SECURE_COOKIES, ORIGINS

router = APIRouter(prefix="/api/auth", tags=["authentication"])
passwords = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
_dummy_hash = passwords.hash(secrets.token_urlsafe(32))


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def cookie(response: Response, name: str, value: str, age: int):
    response.set_cookie(name, value, max_age=age, httponly=True, secure=SECURE_COOKIES, samesite="lax", path="/")


def identity(request: Request) -> dict:
    token = request.cookies.get(SESSION_COOKIE, "")
    now = int(time.time())
    with SessionLocal() as db:
        session = db.get(Session, digest(token)) if token else None
        if not session or session.expires_at <= now or session.last_seen < now - 1800:
            raise HTTPException(401, "Sign in to continue.")
        user = db.get(User, session.user_id)
        member = db.get(Membership, (session.user_id, session.tenant_id))
        if not user or user.disabled or not member:
            raise HTTPException(401, "Session is no longer valid.")
        session.last_seen = now
        db.commit()
        return {"id": user.id, "email": user.email, "tenant_id": member.tenant_id,
                "role": member.role, "csrf_hash": session.csrf_hash, "_session_hash": session.token_hash}


def check_csrf(request: Request, user: dict | None = None):
    if request.headers.get("origin") not in ORIGINS:
        raise HTTPException(403, "Request origin is not allowed.")
    supplied = request.headers.get("x-csrf-token", "")
    expected = user["csrf_hash"] if user else digest(request.cookies.get(CSRF_COOKIE, ""))
    if not supplied or not secrets.compare_digest(digest(supplied), expected):
        raise HTTPException(403, "Refresh the page to renew request verification.")


def authorize_dossier(db, dossier_id: str, user: dict, write=False, lock=False):
    current = db.get(User, user["id"])
    membership = db.get(Membership, (user["id"], user["tenant_id"]))
    if not current or current.disabled or not membership:
        raise HTTPException(401, "Workspace membership is no longer active.")
    if user.get("_session_hash"):
        session = db.get(Session, user["_session_hash"])
        if not session or session.expires_at <= int(time.time()) or session.last_seen < int(time.time()) - 1800:
            raise HTTPException(401, "Session is no longer active.")
    if write and membership.role not in {"reviewer", "admin"}:
        raise HTTPException(403, "Reviewer permission required.")
    query = db.query(ContextDossier).filter_by(id=dossier_id, tenant_id=user["tenant_id"])
    if lock:
        query = query.with_for_update()
    row = query.first()
    if not row:
        raise HTTPException(404, "Dossier not found.")
    return row


def request_user(request: Request):
    return request.state.user


@router.get("/csrf")
def csrf(request: Request, response: Response):
    token = secrets.token_urlsafe(32)
    existing = request.cookies.get(SESSION_COOKIE)
    if existing:
        with SessionLocal() as db:
            session = db.get(Session, digest(existing))
            if session:
                token = hmac.new(existing.encode(), b'clearancex-csrf-v1', hashlib.sha256).hexdigest()
                session.csrf_hash = digest(token)
                db.commit()
    cookie(response, CSRF_COOKIE, token, 28800)
    response.headers["Cache-Control"] = "no-store"
    return {"csrf_token": token}


class Login(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=512)


@router.post("/login")
def login(payload: Login, request: Request, response: Response):
    check_csrf(request)
    now = int(time.time())
    email = payload.email.strip().lower()
    # Do not trust client-supplied forwarded headers.
    ip_key, email_key = digest(request.client.host if request.client else "unknown"), digest(email)
    with SessionLocal() as db:
        recent = db.query(LoginAttempt).filter(LoginAttempt.timestamp > now - 900,
            or_(LoginAttempt.identity == email_key, LoginAttempt.identity == ip_key)).count()
        if recent >= 20:
            raise HTTPException(429, "Too many attempts. Try again later.")
        db.add_all([LoginAttempt(id=str(uuid.uuid4()), identity=k, timestamp=now) for k in {ip_key, email_key}])
        db.query(LoginAttempt).filter(LoginAttempt.timestamp < now - 86400).delete()
        db.commit()
        user = db.query(User).filter_by(email=email).first()
        try:
            valid = passwords.verify(user.password_hash if user else _dummy_hash, payload.password)
        except (VerificationError, InvalidHashError):
            valid = False
        member = db.query(Membership).filter_by(user_id=user.id).first() if user else None
        if not valid or not user or user.disabled or not member:
            raise HTTPException(401, "Email or password is incorrect.")
        old_token = request.cookies.get(SESSION_COOKIE)
        if old_token:
            db.query(Session).filter_by(token_hash=digest(old_token)).delete()
        token = secrets.token_urlsafe(32)
        csrf_token = hmac.new(token.encode(), b'clearancex-csrf-v1', hashlib.sha256).hexdigest()
        db.add(Session(token_hash=digest(token), user_id=user.id, tenant_id=member.tenant_id,
            csrf_hash=digest(csrf_token), created_at=now, last_seen=now, expires_at=now + 28800))
        db.commit()
        cookie(response, SESSION_COOKIE, token, 28800)
        cookie(response, CSRF_COOKIE, csrf_token, 28800)
        response.headers["Cache-Control"] = "no-store"
        return {"user": {"id": user.id, "email": user.email, "tenant_id": member.tenant_id, "role": member.role},
                "csrf_token": csrf_token}


@router.get("/me")
def me(request: Request):
    user = identity(request)
    return {"user": {k: user[k] for k in ("id", "email", "tenant_id", "role")}}


@router.post("/logout")
def logout(request: Request, response: Response):
    user = identity(request)
    check_csrf(request, user)
    with SessionLocal() as db:
        db.query(Session).filter_by(token_hash=digest(request.cookies[SESSION_COOKIE])).delete()
        db.commit()
    response.delete_cookie(SESSION_COOKIE, path="/", secure=SECURE_COOKIES, httponly=True, samesite="lax")
    response.delete_cookie(CSRF_COOKIE, path="/", secure=SECURE_COOKIES, httponly=True, samesite="lax")
    return {"status": "signed_out"}
