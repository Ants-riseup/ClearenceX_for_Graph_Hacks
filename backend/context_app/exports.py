"""Versioned private export snapshots and persisted, readiness-controlled batches."""
import copy
import hashlib
import io
import uuid
import zipfile
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field, ConfigDict
from database.connection import SessionLocal
from .models import ContextDossier, ExportArtifact, BatchJob
from .security import authorize_dossier
from .service import require_current, enqueue, now
from .graph import fields
from .exporting import readiness, metadata, line_items
from reasoning.cusdec_xml import generate_cusdec_xml

router = APIRouter(prefix='/api', tags=['exports'])


def prepare(sid, user, expected, request_id):
    with SessionLocal() as db:
        row = authorize_dossier(db, sid, user, write=True, lock=True)
        existing = db.get(ExportArtifact, request_id)
        if existing:
            if existing.dossier_id != sid or existing.actor_id != user['id']:
                raise HTTPException(409, 'Export request ID is already used.')
            return artifact_view(existing)
        require_current(row, expected)
        check = readiness(db, row)
        if not check['export_allowed']:
            raise HTTPException(422, {'message': 'Resolve readiness blockers before export.', 'readiness': check})
        xml = generate_cusdec_xml(fields(row.state, row.id), metadata(db, row.id), check['prepared_line_items'])
        if isinstance(xml, bytes):
            xml = xml.decode('utf-8')
        decisions = [d for d in row.state['decisions'] if d['status'] == 'approved' and d['validity_state'] == 'current']
        payload = {'template': check.get('template_version', 'clearancex-prototype'), 'sha256': hashlib.sha256(xml.encode()).hexdigest(),
            'decision_ids': [d['id'] for d in decisions], 'reviewer_id': user['id'], 'source_revision': row.revision,
            'created_at': now(), 'notice': check['notice'], 'metadata': metadata(db, row.id),
            'line_items': check['prepared_line_items'], 'fields': [{'field_id': f['canonical_field_id'], 'value': f['consensus_value'], 'assertions': [a['assertion_id'] for a in f['assertions']]} for f in fields(row.state, row.id)]}
        artifact = ExportArtifact(id=request_id, dossier_id=sid, actor_id=user['id'], source_revision=row.revision,
            validity_state='current', created_at=now(), payload=payload, xml=xml)
        db.add(artifact)
        enqueue(db, row, copy.deepcopy(row.state), user['id'], 'export_snapshot_created', {'export_id': request_id, 'source_revision': row.revision})
        db.commit()
        return artifact_view(artifact)


def artifact_view(artifact):
    return {'export_id': artifact.id, 'shipment_id': artifact.dossier_id, 'validity_state': artifact.validity_state,
        'source_revision': artifact.source_revision, 'created_at': artifact.created_at, 'manifest': artifact.payload}


class ExportRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_revision: int = Field(ge=1)
    request_id: uuid.UUID


@router.post('/shipments/{shipment_id}/exports', status_code=201)
def create_export(shipment_id: str, payload: ExportRequest, request: Request):
    return prepare(shipment_id, request.state.user, payload.expected_revision, str(payload.request_id))


@router.get('/shipments/{shipment_id}/exports')
def exports(shipment_id: str, request: Request):
    with SessionLocal() as db:
        authorize_dossier(db, shipment_id, request.state.user)
        return {'exports': [artifact_view(a) for a in db.query(ExportArtifact).filter_by(dossier_id=shipment_id).order_by(ExportArtifact.created_at.desc()).limit(50)]}


@router.get('/shipments/{shipment_id}/exports/{export_id}/content')
def download(shipment_id: str, export_id: str, request: Request):
    with SessionLocal() as db:
        authorize_dossier(db, shipment_id, request.state.user, write=True)
        artifact = db.get(ExportArtifact, export_id)
        if not artifact or artifact.dossier_id != shipment_id:
            raise HTTPException(404, 'Export not found.')
        if artifact.validity_state != 'current':
            raise HTTPException(409, 'Export is stale. Prepare a new reviewed revision.')
        return Response(artifact.xml, media_type='application/xml', headers={'Cache-Control': 'no-store',
            'Content-Disposition': f'attachment; filename="CUSDEC_{shipment_id[:8]}_r{artifact.source_revision}.xml"'})


class BatchRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: uuid.UUID
    dossiers: dict[uuid.UUID, int] = Field(min_length=1, max_length=10)


@router.post('/batch-exports', status_code=201)
def create_batch(payload: BatchRequest, request: Request):
    user, bid = request.state.user, str(payload.request_id)
    with SessionLocal() as db:
        existing = db.get(BatchJob, bid)
        if existing:
            if existing.tenant_id != user['tenant_id'] or existing.actor_id != user['id']:
                raise HTTPException(409, 'Batch request ID is already used.')
            return batch_view(existing)
        # Authorize every selected ID before any side effect or disclosure.
        for sid in payload.dossiers:
            authorize_dossier(db, str(sid), user, write=True)
        db.add(BatchJob(id=bid, tenant_id=user['tenant_id'], actor_id=user['id'], created_at=now(), status='processing', result={'items': []}))
        db.commit()
    items = []
    for sid, revision in payload.dossiers.items():
        try:
            artifact = prepare(str(sid), user, revision, str(uuid.uuid5(uuid.UUID(bid), str(sid))))
            items.append({'shipment_id': str(sid), 'status': 'prepared', 'export_id': artifact['export_id']})
        except HTTPException as exc:
            items.append({'shipment_id': str(sid), 'status': 'blocked', 'detail': exc.detail})
        except Exception:
            items.append({'shipment_id': str(sid), 'status': 'failed', 'detail': 'Preparation failed. No successful result was fabricated.'})
        # Keep per-item progress durable even if the process stops mid-batch.
        with SessionLocal() as db:
            job = db.get(BatchJob, bid); job.result = {'items': list(items)}; db.commit()
    with SessionLocal() as db:
        job = db.get(BatchJob, bid)
        job.status = 'completed' if all(i['status'] == 'prepared' for i in items) else 'partial' if any(i['status'] == 'prepared' for i in items) else 'blocked'
        db.commit()
        return batch_view(job)


def batch_view(job):
    return {'batch_id': job.id, 'status': job.status, 'created_at': job.created_at, **job.result}


@router.get('/batch-exports')
def batches(request: Request):
    with SessionLocal() as db:
        return {'batches': [batch_view(j) for j in db.query(BatchJob).filter_by(tenant_id=request.state.user['tenant_id']).order_by(BatchJob.created_at.desc()).limit(30)]}


@router.get('/batch-exports/{batch_id}/content')
def download_batch(batch_id: str, request: Request):
    with SessionLocal() as db:
        job = db.get(BatchJob, batch_id)
        if not job or job.tenant_id != request.state.user['tenant_id']:
            raise HTTPException(404, 'Batch not found.')
        if job.status == 'processing':
            raise HTTPException(409, 'Batch has not finished; inspect its persisted per-item results.')
        output = io.BytesIO()
        prepared = [i for i in job.result.get('items', []) if i['status'] == 'prepared']
        if not prepared:
            raise HTTPException(422, 'No dossiers were ready for this batch.')
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
            for item in prepared:
                authorize_dossier(db, item['shipment_id'], request.state.user, write=True)
                artifact = db.get(ExportArtifact, item['export_id'])
                if not artifact or artifact.validity_state != 'current':
                    raise HTTPException(409, 'A prepared export is now stale. Prepare a new batch.')
                archive.writestr(f"CUSDEC_{item['shipment_id'][:8]}_r{artifact.source_revision}.xml", artifact.xml)
            import json
            archive.writestr('manifest.json', json.dumps(batch_view(job), indent=2))
        return Response(output.getvalue(), media_type='application/zip', headers={'Cache-Control': 'no-store', 'Content-Disposition': f'attachment; filename="batch_{batch_id[:8]}.zip"'})
