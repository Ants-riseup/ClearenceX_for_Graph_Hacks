"""ClearanceX operator onboarding for customer company logins."""
import secrets
import time
import uuid
from typing import Literal
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import Field, field_validator
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from database.connection import SessionLocal
from .admin_security import ConfirmAdmin, email_address, confirm_password
from .models import CompanyEvent, ContextDossier, Membership, Session, Tenant, User
from .security import passwords

router = APIRouter(prefix='/api/platform', tags=['ClearanceX customer administration'])


class CustomerProfile(ConfirmAdmin):
    name: str = Field(min_length=1, max_length=200)
    contact_name: str = Field(default='', max_length=120)

    @field_validator('name')
    @classmethod
    def company_name(cls, value):
        if not value.strip():
            raise ValueError('Enter a company name.')
        return value.strip()


class NewCustomer(CustomerProfile):
    email: str = Field(min_length=3, max_length=254)
    password: str | None = Field(default=None, min_length=8, max_length=128, repr=False)

    @field_validator('email')
    @classmethod
    def customer_email(cls, value):
        return email_address(value)


class Revision(ConfirmAdmin):
    expected_version: int = Field(ge=1, strict=True)


class CustomerEdit(CustomerProfile):
    expected_version: int = Field(ge=1, strict=True)


class CustomerStatus(Revision):
    status: Literal['active', 'suspended', 'removed']


def require_operator(db, actor):
    user = db.get(User, actor['id'])
    member = db.get(Membership, (actor['id'], actor['tenant_id']))
    session = db.get(Session, actor.get('_session_hash', ''))
    now = int(time.time())
    if not user or user.disabled or not member or member.disabled or not session or session.user_id != user.id or session.tenant_id != actor['tenant_id'] or session.expires_at <= now or session.last_seen < now - 1800:
        raise HTTPException(401, 'Sign in again to manage customers.')
    if not user.platform_admin:
        raise HTTPException(403, 'ClearanceX platform administrator required.')
    return user


def event(db, actor, company, action, details=None):
    db.add(CompanyEvent(id=str(uuid.uuid4()), company_id=company.id, actor_id=actor['id'], action=action,
        created_at=int(time.time()), details=details or {}))


def company_view(db, company, members=None, shipment_count=None):
    if members is None:
        members = db.query(User, Membership).join(Membership, Membership.user_id == User.id).filter(
            Membership.tenant_id == company.id, User.platform_admin == 0).order_by(User.email).all()
    return {'id': company.id, 'name': company.name, 'status': company.status, 'version': company.version,
        'contact_name': (company.profile or {}).get('contact_name', ''),
        'shipment_count': shipment_count if shipment_count is not None else db.query(ContextDossier).filter_by(tenant_id=company.id).count(),
        'users': [{'id': user.id, 'email': user.email, 'enabled': not bool(user.disabled or member.disabled), 'requires_password_change': bool(user.must_change_password)} for user, member in members]}


def target_company(db, company_id, version):
    company = db.query(Tenant).filter_by(id=str(company_id)).with_for_update().first()
    if not company:
        raise HTTPException(404, 'Customer company not found.')
    if company.version != version:
        raise HTTPException(409, 'Customer changed. Refresh before applying this action.')
    return company


@router.get('/companies')
def list_customers(request: Request, search: str = Query(default='', max_length=100), offset: int = Query(default=0, ge=0), limit: int = Query(default=20, ge=1, le=50), status: Literal['all', 'active', 'suspended', 'removed'] = 'all'):
    with SessionLocal() as db:
        require_operator(db, request.state.user)
        query = db.query(Tenant)
        if status != 'all':
            query = query.filter(Tenant.status == status)
        if search:
            literal = '%' + search.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
            matched = db.query(Membership.tenant_id).join(User, User.id == Membership.user_id).filter(User.platform_admin == 0, User.email.ilike(literal, escape='\\'))
            query = query.filter(or_(Tenant.name.ilike(literal, escape='\\'), Tenant.id.in_(matched)))
        total = query.count()
        rows = query.order_by(Tenant.name, Tenant.id).offset(offset).limit(limit).all()
        # Fetch page members/counts together rather than two extra queries per company.
        ids = [company.id for company in rows]
        members = {company_id: [] for company_id in ids}
        for user, member in db.query(User, Membership).join(Membership, Membership.user_id == User.id).filter(Membership.tenant_id.in_(ids), User.platform_admin == 0).order_by(User.email):
            members[member.tenant_id].append((user, member))
        counts = dict(db.query(ContextDossier.tenant_id, func.count(ContextDossier.id)).filter(ContextDossier.tenant_id.in_(ids)).group_by(ContextDossier.tenant_id).all())
        statuses = dict(db.query(Tenant.status, func.count(Tenant.id)).group_by(Tenant.status).all())
        return {'companies': [company_view(db, company, members[company.id], counts.get(company.id, 0)) for company in rows], 'total': total,
            'summary': {'total': sum(statuses.values()), 'active': statuses.get('active', 0), 'suspended': statuses.get('suspended', 0), 'removed': statuses.get('removed', 0)}}


@router.post('/companies', status_code=201)
def add_customer(payload: NewCustomer, request: Request):
    actor = request.state.user
    with SessionLocal() as db:
        operator = require_operator(db, actor)
        confirm_password(db, actor, operator, payload.admin_password)
        if db.query(User).filter_by(email=payload.email).first():
            raise HTTPException(409, 'This email already has an account. Use a different customer email.')
        secret = payload.password or secrets.token_urlsafe(24)
        company = Tenant(id=str(uuid.uuid4()), name=payload.name, status='active', version=1, profile={'contact_name': payload.contact_name})
        user = User(id=str(uuid.uuid4()), email=payload.email, password_hash=passwords.hash(secret), disabled=0, platform_admin=0, must_change_password=1)
        try:
            db.add(company); db.add(user); db.flush()
            db.add(Membership(user_id=user.id, tenant_id=company.id, role='user', disabled=0, version=1)); db.flush()
            event(db, actor, company, 'customer_added', {'user_id': user.id})
            result = company_view(db, company); db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, 'Customer could not be added. The email may already be registered.')
        return {'company': result, 'email': user.email, 'initial_password': secret}


@router.post('/companies/{company_id}/profile')
def edit_customer(company_id: uuid.UUID, payload: CustomerEdit, request: Request):
    actor = request.state.user
    with SessionLocal() as db:
        company = target_company(db, company_id, payload.expected_version)
        operator = require_operator(db, actor); confirm_password(db, actor, operator, payload.admin_password)
        company.name = payload.name
        company.profile = {**(company.profile or {}), 'contact_name': payload.contact_name}
        company.version += 1
        event(db, actor, company, 'customer_details_updated')
        db.flush(); result = company_view(db, company); db.commit()
        return {'company': result}


@router.post('/companies/{company_id}/status')
def customer_status(company_id: uuid.UUID, payload: CustomerStatus, request: Request):
    actor = request.state.user
    with SessionLocal() as db:
        company = target_company(db, company_id, payload.expected_version)
        operator = require_operator(db, actor); confirm_password(db, actor, operator, payload.admin_password)
        if company.status != payload.status:
            before = company.status
            company.status = payload.status; company.version += 1
            customer_ids = db.query(User.id).join(Membership, Membership.user_id == User.id).filter(Membership.tenant_id == company.id, User.platform_admin == 0)
            db.query(Session).filter(Session.tenant_id == company.id, Session.user_id.in_(customer_ids)).delete(synchronize_session=False)
            event(db, actor, company, 'customer_access_changed', {'before': before, 'after': payload.status})
        db.flush(); result = company_view(db, company); db.commit()
        return {'company': result}


@router.post('/companies/{company_id}/users/{user_id}/reset-password')
def reset_customer_password(company_id: uuid.UUID, user_id: uuid.UUID, payload: Revision, request: Request):
    actor = request.state.user
    with SessionLocal() as db:
        company = target_company(db, company_id, payload.expected_version)
        operator = require_operator(db, actor); confirm_password(db, actor, operator, payload.admin_password)
        member = db.get(Membership, (str(user_id), company.id)); user = db.get(User, str(user_id))
        if not member or not user or user.platform_admin:
            raise HTTPException(404, 'Customer user not found.')
        if db.query(Membership).filter_by(user_id=user.id).count() != 1:
            raise HTTPException(409, 'Shared identity recovery requires the local operator.')
        secret = secrets.token_urlsafe(24)
        user.password_hash = passwords.hash(secret); user.must_change_password = 1; member.version += 1; company.version += 1
        db.query(Session).filter_by(user_id=user.id).delete()
        event(db, actor, company, 'customer_password_reset', {'user_id': user.id}); db.commit()
        return {'email': user.email, 'initial_password': secret}


@router.get('/events')
def customer_events(request: Request):
    with SessionLocal() as db:
        require_operator(db, request.state.user)
        rows = db.query(CompanyEvent, Tenant.name).join(Tenant, Tenant.id == CompanyEvent.company_id).order_by(CompanyEvent.created_at.desc(), CompanyEvent.id).limit(50)
        return {'events': [{'id': row.id, 'company_id': row.company_id, 'company_name': name, 'action': row.action, 'created_at': row.created_at} for row, name in rows]}
