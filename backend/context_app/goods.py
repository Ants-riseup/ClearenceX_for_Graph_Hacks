"""Authorized, revision-aware reviewed goods and declaration metadata."""
import copy
from fastapi import APIRouter, HTTPException, Request
from database.connection import SessionLocal
from database.models import CusdecLineItem, DeclarationMetadata
from .models import ContextDossier
from .security import authorize_dossier
from .service import enqueue, require_current
from reasoning.goods_validation import inventory, normalize_review
from reasoning.declaration_validation import validate_profile

router=APIRouter(prefix='/api',tags=['goods review'])


def view(row):
    return {**(row.details or {}),'id':str(row.id),'row_index':row.row_index,'description':row.description,
        **{key:(row.details or {}).get(key,getattr(row,key)) for key in ('quantity','unit','unit_price','total_price')},
        'source_reference':row.source_reference,'source_row_id':row.source_row_id,'source_document_id':row.source_document_id,
        'source_revision':row.source_revision,'validity_state':row.validity_state,'verified_by':row.verified_by}


def saved_rows(db,sid):
    return [view(r) for r in db.query(CusdecLineItem).filter(CusdecLineItem.shipment_id==sid,CusdecLineItem.validity_state!='removed').order_by(CusdecLineItem.row_index)]


def expected(payload):
    revision=payload.get('expected_revision')
    if not isinstance(revision,int) or isinstance(revision,bool) or revision<1:
        raise HTTPException(422,'Supply the current expected_revision. Refresh this dossier before saving.')
    return revision


def result(db,row):
    from .exporting import readiness
    check=readiness(db,row)
    return {'status':'saved','profile':check['profile'],'line_items':check['line_items'],'readiness':check}


def save_profile(sid,payload,user):
    from reasoning.cusdec_readiness import PROFILE_REQUIREMENTS
    values=payload.get('values')
    if not isinstance(values,dict) or not values or set(values)-set(PROFILE_REQUIREMENTS):
        raise HTTPException(422,'Supply supported declaration profile values.')
    try: cleaned=validate_profile(values)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc
    with SessionLocal() as db:
        row=authorize_dossier(db,sid,user,write=True,lock=True)
        require_current(row,expected(payload))
        changed=False
        for key,value in cleaned.items():
            record=db.query(DeclarationMetadata).filter_by(shipment_id=sid,field_name=key).first()
            if record is None:
                record=DeclarationMetadata(shipment_id=sid,field_name=key);db.add(record)
            if record.value!=value:
                record.value=value;record.updated_by=user['id'];changed=True
        if changed: enqueue(db,row,copy.deepcopy(row.state),user['id'],'declarationmetadata_saved')
        db.commit()
        return result(db,row)


def save_review(sid,payload,user):
    with SessionLocal() as db:
        row=authorize_dossier(db,sid,user,write=True,lock=True)
        ref=payload.get('source_reference')
        candidate=next((r for r in inventory(row.state.get('documents',[])) if r['source_reference']==ref),None)
        if candidate is None: raise HTTPException(422,'Choose a goods row from a current invoice in this dossier.')
        try: details=normalize_review(payload,candidate)
        except ValueError as exc: raise HTTPException(422,str(exc)) from exc
        existing=db.query(CusdecLineItem).filter_by(shipment_id=sid,source_row_id=ref).first()
        if existing and existing.validity_state=='current' and existing.details==details:
            return result(db,row) # Stable source identity makes retries safe even during projection.
        require_current(row,expected(payload))
        if existing is None:
            last=db.query(CusdecLineItem.row_index).filter_by(shipment_id=sid).order_by(CusdecLineItem.row_index.desc()).first()
            existing=CusdecLineItem(shipment_id=sid,row_index=(last[0] if last else 0)+1);db.add(existing)
        for key in ('description','unit','source_reference'): setattr(existing,key,details[key])
        for key in ('quantity','unit_price','total_price'): setattr(existing,key,float(details[key]))
        existing.source_document_id=candidate['source_document_id'];existing.source_revision=candidate['source_revision']
        existing.source_row_id=ref;existing.details=details;existing.validity_state='current';existing.verified_by=user['id']
        enqueue(db,row,copy.deepcopy(row.state),user['id'],'cusdeclineitem_saved',{'source_row_id':ref})
        db.commit()
        return result(db,row)


@router.get('/shipments/{shipment_id}/goods-candidates')
def candidates(shipment_id:str,request:Request):
    with SessionLocal() as db:
        row=authorize_dossier(db,shipment_id,request.state.user)
        return {'revision':row.revision,'candidates':inventory(row.state.get('documents',[])),'saved_rows':saved_rows(db,shipment_id)}


@router.post('/shipments/{shipment_id}/goods/{row_id}/remove')
def remove(shipment_id:str,row_id:str,payload:dict,request:Request):
    import uuid
    try: key=uuid.UUID(row_id)
    except ValueError: raise HTTPException(404,'Goods review not found.') from None
    with SessionLocal() as db:
        row=authorize_dossier(db,shipment_id,request.state.user,write=True,lock=True)
        record=db.get(CusdecLineItem,key)
        if not record or record.shipment_id!=shipment_id: raise HTTPException(404,'Goods review not found.')
        require_current(row,expected(payload))
        record.validity_state='removed'
        enqueue(db,row,copy.deepcopy(row.state),request.state.user['id'],'cusdeclineitem_saved',{'removed_row_id':row_id})
        db.commit()
        return result(db,row)
