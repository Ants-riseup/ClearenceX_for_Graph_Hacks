import copy
import io
import uuid
import zipfile
from database.connection import SessionLocal
from database.models import DeclarationMetadata, CusdecLineItem
from context_app.fixtures import hero_documents, write_pdf
from pathlib import Path
from context_app.models import ContextDossier, ExportArtifact
from context_app.service import create_dossier
from context_app.graph import GraphRepository
from reasoning.cusdec_readiness import PROFILE_REQUIREMENTS
from conftest import sync, account
from test_context_flow import approve, evidence, status


def valid_profile():
    return {key: {'currency_rate':'305','transport_mode':'4','container_flag':'0','general_procedure_code':'4','declaration_type':'IM'}.get(key, 'SYNTHETIC-'+key) for key in PROFILE_REQUIREMENTS}


def ready_dossier(user):
    docs = hero_documents()[:2]
    values = {'INVOICE_NUMBER': 'SYNTHETIC-100', 'CONSIGNEE_NAME': 'Example Importer', 'SHIPPER_NAME': 'Example Exporter',
        'TOTAL_AMOUNT': 120, 'CURRENCY_CODE': 'USD', 'INCOTERM': 'CIF', 'GROSS_WEIGHT': 450, 'PACKAGE_COUNT': 12,
        'COUNTRY_OF_ORIGIN': 'IN', 'PORT_OF_LOADING': 'Chennai', 'PORT_OF_DISCHARGE': 'Colombo', 'HS_CODE': '61091000', 'AWB_NUMBER': 'SYNTHETIC-AWB'}
    for doc in docs:
        doc['entities'] = [{'entity_type': field, 'value': str(value), 'normalized_value': value, 'page': 1, 'bbox': [],
            'unit': 'kg' if field == 'GROSS_WEIGHT' else None, 'extraction_confidence': 0} for field, value in values.items()]
        doc['content_hash'] = write_pdf(Path(doc['file_path']), ['SYNTHETIC EXPORT TEST'] + [f'{field}: {value}' for field, value in values.items()])
    ref = docs[0]['document_id'] + ':page:1:row:1'
    docs[0]['line_items'] = [{'description':'Synthetic shirts','quantity':'12','unit':'PCS','unit_price':'10','total_price':'120',
        'hs_code':'61091000','origin':'IN','gross_weight':'450','net_weight':'420','package_count':'12','currency':'USD',
        'source_reference':ref,'page':1,'status':'needs_review'}]
    sid = create_dossier(user, docs, 'Complete synthetic export test')
    with SessionLocal() as db:
        for key, value in valid_profile().items():
            db.add(DeclarationMetadata(shipment_id=sid, field_name=key, value=value))
        from reasoning.goods_validation import inventory, normalize_review
        candidate = inventory(docs)[0]
        details = normalize_review(candidate, candidate)
        db.add(CusdecLineItem(shipment_id=sid, row_index=1, description='Synthetic shirts', quantity=12, unit='PCS', unit_price=10,
            total_price=120, source_reference=ref, verified_by=user['id'], source_document_id=docs[0]['document_id'],
            source_revision=1, source_row_id=ref, validity_state='current', details=details))
        db.commit()
    sync(sid)
    return sid


def test_export_is_idempotent_and_becomes_stale_on_dependency_change(reviewer):
    client, user = reviewer
    sid = ready_dossier(user)
    chosen = next(a for a in evidence(client, sid) if a['document_type'] == 'packing_list')
    decision = approve(client, sid, chosen)
    request = {'request_id': str(uuid.uuid4()), 'expected_revision': status(client, sid)['source_revision']}
    response = client.post(f'/api/shipments/{sid}/exports', json=request)
    assert response.status_code == 201, response.text
    artifact = response.json()
    assert artifact['manifest']['decision_ids'] == [decision['id']]
    assert client.post(f'/api/shipments/{sid}/exports', json=request).json()['export_id'] == artifact['export_id']
    content = client.get(f"/api/shipments/{sid}/exports/{artifact['export_id']}/content")
    assert content.status_code == 200 and b'<?xml' in content.content
    sync(sid)
    graph = GraphRepository(user['tenant_id'])
    impact = graph.impact(sid, status(client, sid)['source_revision'], chosen['document_id'])
    assert artifact['export_id'] in {r['id'] for r in impact}
    correction = client.post(f'/api/shipments/{sid}/demo-correction', params={'expected_revision': status(client, sid)['source_revision']})
    assert correction.status_code == 200
    assert client.get(f"/api/shipments/{sid}/exports/{artifact['export_id']}/content").status_code == 409
    other, _ = account()
    assert other.get(f"/api/shipments/{sid}/exports/{artifact['export_id']}/content").status_code == 404


def test_batch_contains_ready_outputs_and_reports_each_blocker(reviewer):
    client, user = reviewer
    sid = ready_dossier(user)
    from conftest import demo
    blocked = demo(client)
    response = client.post('/api/batch-exports', json={'request_id': str(uuid.uuid4()), 'dossiers': {sid: 1, blocked: 1}})
    assert response.status_code == 201, response.text
    result = response.json()
    assert result['status'] == 'partial'
    assert {i['status'] for i in result['items']} == {'prepared', 'blocked'}
    archive = client.get(f"/api/batch-exports/{result['batch_id']}/content")
    assert archive.status_code == 200, archive.text
    with zipfile.ZipFile(io.BytesIO(archive.content)) as files:
        assert len([n for n in files.namelist() if n.endswith('.xml')]) == 1
        assert 'manifest.json' in files.namelist()
