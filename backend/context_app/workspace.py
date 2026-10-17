"""Workspace controls use the same tenant, role, CSRF and revision boundaries."""
import copy
import uuid
from collections import Counter
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from database.connection import SessionLocal
from .models import Tenant, ContextDossier, AgentRun, Outbox, Membership
from .security import authorize_dossier
from .service import enqueue, require_current, replace_document, now
from reasoning.comparison import describe

router = APIRouter(prefix='/api', tags=['workspace'])


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Settings(Strict):
    expected_version: int = Field(ge=0)
    weight_absolute_tolerance: float = Field(ge=0, le=5, allow_inf_nan=False)
    retention_days: int = Field(ge=7, le=3650)
    notifications_enabled: bool


@router.get('/workspace/settings')
def settings(request: Request):
    with SessionLocal() as db:
        tenant = db.get(Tenant, request.state.user['tenant_id'])
        data = tenant.settings or {}
        return {'name': tenant.name, 'version': data.get('version', 0), 'comparison_policy': describe(data.get('comparison_policy')),
            'retention_days': data.get('retention_days', 90), 'notifications_enabled': data.get('notifications_enabled', True),
            'retention_mode': 'preview_only', 'notice': 'No automatic data deletion or email service is enabled.'}


@router.post('/workspace/settings')
def save_settings(payload: Settings, request: Request):
    if request.state.user['role'] != 'admin':
        raise HTTPException(403, 'Workspace administrator required.')
    with SessionLocal() as db:
        tenant = db.query(Tenant).filter_by(id=request.state.user['tenant_id']).with_for_update().one()
        data = dict(tenant.settings or {})
        if payload.expected_version != data.get('version', 0):
            raise HTTPException(409, 'Settings changed. Reload before saving.')
        changed = str(payload.weight_absolute_tolerance) != str(float(describe(data.get('comparison_policy'))['weight_absolute_tolerance']))
        policy = {'weight_absolute_tolerance': str(payload.weight_absolute_tolerance), 'configuration_revision': data.get('version', 0) + 1}
        tenant.settings = {'version': data.get('version', 0) + 1, 'comparison_policy': policy,
            'retention_days': payload.retention_days, 'notifications_enabled': payload.notifications_enabled}
        affected = 0
        for row in db.query(ContextDossier).filter_by(tenant_id=tenant.id).order_by(ContextDossier.id).with_for_update():
            state = copy.deepcopy(row.state)
            if changed:
                state['comparison_policy'] = policy
                for decision in state.get('decisions', []):
                    if decision['field_id'].split(':')[-1] in {'GROSS_WEIGHT', 'NET_WEIGHT'} and decision['validity_state'] == 'current':
                        decision['validity_state'] = 'stale'; affected += 1
                for task in state.get('tasks', []):
                    if task['field_id'].split(':')[-1] in {'GROSS_WEIGHT', 'NET_WEIGHT'} and task['status'] == 'pending':
                        task['status'] = 'superseded'
            enqueue(db, row, state, request.state.user['id'], 'workspace_settings_changed', {'version': tenant.settings['version'], 'comparison_changed': changed})
        db.commit()
    return {'status': 'saved', 'stale_approvals': affected, 'settings': settings(request)}


@router.get('/workspace/operations')
def operations(request: Request):
    with SessionLocal() as db:
        tid = request.state.user['tenant_id']
        tenant = db.get(Tenant, tid)
        rows = db.query(ContextDossier).filter_by(tenant_id=tid).all()
        ids = [r.id for r in rows]
        run_counts = Counter(r.status for r in db.query(AgentRun).filter(AgentRun.dossier_id.in_(ids)))
        queue_counts = Counter(r.status for r in db.query(Outbox).filter(Outbox.dossier_id.in_(ids)))
        cutoff = now() - (tenant.settings or {}).get('retention_days', 90) * 86400
        return {'dossier_count': len(rows), 'context_pending': sum(r.revision != r.graph_revision for r in rows),
            'agent_runs': dict(run_counts), 'graph_jobs': dict(queue_counts),
            'retention_preview': [{'shipment_id': r.id, 'title': r.title, 'created_at': r.created_at} for r in rows if r.created_at < cutoff],
            'retention_mode': 'preview_only', 'notification_mode': 'in_app',
            'onboarding': ['Create or select a dossier.', 'Wait for graph synchronization.', 'Inspect competing evidence.', 'Propose a task and approve a source with a reason.', 'Replace a source and review stale approvals.']}


class Title(Strict):
    title: str = Field(min_length=1, max_length=200)
    expected_revision: int = Field(ge=1)


@router.post('/shipments/{shipment_id}/reference')
def rename(shipment_id: str, payload: Title, request: Request):
    if not payload.title.strip():
        raise HTTPException(422, 'Reference cannot be blank.')
    with SessionLocal() as db:
        row = authorize_dossier(db, shipment_id, request.state.user, write=True, lock=True)
        require_current(row, payload.expected_revision)
        row.title = payload.title.strip()
        enqueue(db, row, copy.deepcopy(row.state), request.state.user['id'], 'dossier_reference_changed')
        db.commit()
    return {'status': 'saved'}


class Draft(Strict):
    reason: str = Field(max_length=1000)
    field_id: str = Field(max_length=255)
    expected_revision: int = Field(ge=1)


@router.get('/shipments/{shipment_id}/review-draft')
def draft(shipment_id: str, request: Request):
    with SessionLocal() as db:
        row = authorize_dossier(db, shipment_id, request.state.user)
        return {'draft': row.state.get('drafts', {}).get(request.state.user['id']), 'current_revision': row.revision}


@router.post('/shipments/{shipment_id}/review-draft')
def save_draft(shipment_id: str, payload: Draft, request: Request):
    with SessionLocal() as db:
        row = authorize_dossier(db, shipment_id, request.state.user, write=True, lock=True)
        if payload.expected_revision != row.revision:
            raise HTTPException(409, 'Evidence changed; review the current sources before saving the draft.')
        if payload.field_id and not payload.field_id.startswith(f'shipment:{shipment_id}:field:'):
            raise HTTPException(422, 'Draft field is outside this dossier.')
        state = copy.deepcopy(row.state)
        state.setdefault('drafts', {})[request.state.user['id']] = {**payload.model_dump(), 'saved_at': now()}
        row.state = state
        db.commit()
    return {'status': 'saved', 'saved_at': now()}


class DocumentType(Strict):
    document_type: str
    expected_revision: int = Field(ge=1)


@router.post('/shipments/{shipment_id}/documents/{document_id}/type')
def correct_type(shipment_id: str, document_id: str, payload: DocumentType, request: Request):
    if payload.document_type not in {'commercial_invoice', 'packing_list', 'awb', 'bl', 'freight_invoice', 'delivery_order'}:
        raise HTTPException(422, 'Unsupported document type.')
    with SessionLocal() as db:
        row = authorize_dossier(db, shipment_id, request.state.user, write=True)
        old = next((d for d in row.state['documents'] if d['document_id'] == document_id), None)
        if not old:
            raise HTTPException(404, 'Current document not found.')
        replacement = copy.deepcopy(old)
        replacement.update(document_id=str(uuid.uuid4()), document_type=payload.document_type)
    return replace_document(shipment_id, request.state.user, document_id, replacement, payload.expected_revision)
