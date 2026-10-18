"""Regression gates for the nine runtime findings and complete real-input flow."""
import copy
import uuid
from pathlib import Path
from decimal import Decimal
from xml.etree import ElementTree as ET
import pytest
from context_app.text_extract import extract
from context_app.service import create_dossier
from database.connection import SessionLocal
from database.models import DeclarationMetadata, CusdecLineItem
from context_app.models import ContextDossier
from conftest import sync
from test_export_snapshots import valid_profile


@pytest.fixture
def actual_dossier(reviewer):
    client,user=reviewer
    inputs=Path(__file__).resolve().parents[2]/'Docs/TEST FILE'
    if len(list(inputs.glob('*.pdf')))!=4: pytest.skip('Private source PDFs are outside the source archive.')
    docs=[]
    for path in sorted(inputs.glob('*.pdf')):
        doc=extract(path,str(uuid.uuid4()));doc.update(revision=1,file_path=str(path),fixture=False);docs.append(doc)
    sid=create_dossier(user,docs,'Actual four-PDF regression');sync(sid)
    return client,user,sid


def state(client,sid): return client.get(f'/api/shipments/{sid}/context-status').json()
def readiness(client,sid): return client.get(f'/api/shipments/{sid}/cusdec-readiness').json()
def candidates(client,sid): return client.get(f'/api/shipments/{sid}/goods-candidates').json()['candidates']
def review(client,sid,row):
    return client.post(f'/api/shipments/{sid}/cusdec-line-items',json={**row,'expected_revision':state(client,sid)['source_revision']})


def finish_headers(client,sid):
    base=f'/api/shipments/{sid}'
    for field in client.get(base+'/key-fields').json()['fields']:
        if field['status']=='pending':
            result=client.post(base+'/field-resolutions',json={'canonical_field_id':field['canonical_field_id'],
                'source_assertion_id':field['assertions'][0]['assertion_id'],'reason':'Automated test of reviewer API against source evidence.',
                'request_id':str(uuid.uuid4()),'expected_revision':state(client,sid)['source_revision']})
            assert result.status_code==200,result.text
            sync(sid)
    result=client.post(base+'/declaration-metadata',json={'values':valid_profile(),'expected_revision':state(client,sid)['source_revision']})
    assert result.status_code==200,result.text
    sync(sid)


def complete(client,sid):
    finish_headers(client,sid)
    for row in candidates(client,sid):
        result=review(client,sid,row);assert result.status_code==200,result.text;sync(sid)
    assert readiness(client,sid)['export_allowed'],readiness(client,sid)['blockers']


def test_real_sources_reach_correct_two_item_xml(actual_dossier):
    client,_,sid=actual_dossier
    initial=readiness(client,sid)
    assert not any(b['code']=='MISSING_FIELD' for b in initial['blockers'])
    assert not initial['export_allowed']
    listing=client.get('/api/dossiers').json()['dossiers']
    assert next(d for d in listing if d['dossier_id']==sid)['export_allowed'] is False
    complete(client,sid)
    response=client.post(f'/api/shipments/{sid}/exports',json={'request_id':str(uuid.uuid4()),'expected_revision':state(client,sid)['source_revision']})
    assert response.status_code==201,response.text
    xml=client.get(f"/api/shipments/{sid}/exports/{response.json()['export_id']}/content")
    assert xml.status_code==200
    root=ET.fromstring(xml.content);items=root.findall('Item')
    assert [i.findtext('Tariff/Commodity_code') for i in items]==['90318000','85371090']
    assert [Decimal(i.findtext('Weight/Gross_mass')) for i in items]==[Decimal(48),Decimal(72)]
    assert [Decimal(i.findtext('Weight/Net_mass')) for i in items]==[Decimal(40),Decimal(60)]
    assert [Decimal(i.findtext('Packages/Number_of_packages')) for i in items]==[Decimal(4),Decimal(4)]
    assert [Decimal(i.findtext('Valuation_item/Item_Invoice_amount')) for i in items]==[Decimal('8068.97'),Decimal('7531.03')]
    assert sum(Decimal(i.findtext('Valuation_item/Statistical_value')) for i in items)==Decimal('4758000')
    sync(sid)
    assert next(d for d in client.get('/api/dossiers').json()['dossiers'] if d['dossier_id']==sid)['export_allowed']


def test_goods_require_current_source_and_all_rows(actual_dossier):
    client,_,sid=actual_dossier;finish_headers(client,sid)
    rows=candidates(client,sid)
    fake={**rows[0],'source_reference':'not-a-real-source:page:999:row:999'}
    assert review(client,sid,fake).status_code==422
    assert review(client,sid,{**rows[0],'quantity':'1','unit_price':'1','total_price':'1'}).status_code==422
    assert review(client,sid,rows[0]).status_code==200;sync(sid)
    check=readiness(client,sid)
    assert not check['export_allowed'] and 'UNVERIFIED_GOODS' in {b['code'] for b in check['blockers']}
    assert client.post(f'/api/shipments/{sid}/exports',json={'request_id':str(uuid.uuid4()),'expected_revision':state(client,sid)['source_revision']}).status_code==422
    # Duplicate submission is an idempotent review of one source, not a new item.
    count=len(check['line_items']);rev=state(client,sid)['source_revision']
    assert review(client,sid,rows[0]).status_code==200
    assert len(readiness(client,sid)['line_items'])==count and state(client,sid)['source_revision']==rev
    assert review(client,sid,rows[1]).status_code==200;sync(sid)
    assert readiness(client,sid)['export_allowed']


def test_invalid_exchange_rates_rejected_at_save_and_export(actual_dossier):
    client,_,sid=actual_dossier;complete(client,sid)
    for value in ['NOT-A-NUMBER','NaN','Infinity','0','-1']:
        response=client.post(f'/api/shipments/{sid}/declaration-metadata',json={'values':{'currency_rate':value},'expected_revision':state(client,sid)['source_revision']})
        assert response.status_code==422,response.text
    # Defense in depth: an old/externally changed record cannot pass export.
    with SessionLocal() as db:
        db.query(DeclarationMetadata).filter_by(shipment_id=sid,field_name='currency_rate').one().value='NOT-A-NUMBER';db.commit()
    assert not readiness(client,sid)['export_allowed']
    assert client.post(f'/api/shipments/{sid}/exports',json={'request_id':str(uuid.uuid4()),'expected_revision':state(client,sid)['source_revision']}).status_code==422


def test_save_response_preserves_goods_and_matches_authoritative_get(actual_dossier):
    client,_,sid=actual_dossier;complete(client,sid)
    response=client.post(f'/api/shipments/{sid}/declaration-metadata',json={'values':valid_profile(),'expected_revision':state(client,sid)['source_revision']})
    assert response.status_code==200
    direct=readiness(client,sid)
    assert response.json()['readiness']=={key:value for key,value in direct.items() if key!='shipment_id'}
    assert len(response.json()['line_items'])==2


def test_packing_change_graph_invalidates_goods_and_allows_rereview(actual_dossier):
    client,_,sid=actual_dossier;complete(client,sid)
    packing=next(d for d in client.get(f'/api/shipments/{sid}/extraction').json()['documents'] if d['document_type']=='packing_list')
    old=readiness(client,sid)['line_items']
    impact=client.get(f'/api/shipments/{sid}/change-impact',params={'document_id':packing['document_id']}).json()['impact']
    assert {r['id'] for r in old}.issubset({r['id'] for r in impact})
    response=client.post(f"/api/shipments/{sid}/documents/{packing['document_id']}/type",json={'document_type':'packing_list','expected_revision':state(client,sid)['source_revision']})
    assert response.status_code==200,response.text;sync(sid)
    check=readiness(client,sid)
    assert not check['export_allowed'] and all(r['validity_state']=='stale' for r in check['line_items'])
    complete(client,sid)
    check=readiness(client,sid)
    assert len(check['line_items'])==2 and all(r['validity_state']=='current' for r in check['line_items'])


def test_remove_and_restore_review_are_auditable(actual_dossier):
    client,_,sid=actual_dossier;complete(client,sid)
    row=readiness(client,sid)['line_items'][0]
    result=client.post(f"/api/shipments/{sid}/goods/{row['id']}/remove",json={'expected_revision':state(client,sid)['source_revision']})
    assert result.status_code==200;sync(sid)
    assert not readiness(client,sid)['export_allowed']
    assert review(client,sid,candidates(client,sid)[0]).status_code==200;sync(sid)
    assert readiness(client,sid)['export_allowed']


def test_allocations_must_match_source_not_just_grand_total(actual_dossier):
    client,_,sid=actual_dossier
    row=candidates(client,sid)[0]
    assert review(client,sid,{**row,'gross_weight':'120','package_count':'8'}).status_code==422
    for change in [{'hs_code':'999999'}, {'origin':'US'}, {'currency':'EUR'}]:
        assert review(client,sid,{**row,**change}).status_code==422
