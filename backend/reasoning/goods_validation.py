"""Source-linked goods identities and complete per-item declaration validation."""
import re
from decimal import Decimal
from .declaration_validation import number, money, hs_code, allocate


def _identity(row):
    text = str(row.get('description',''))
    model = re.search(r'\bModel\s*:?\s*([A-Z0-9]+(?:[-/][A-Z0-9]+)+)', text, re.I)
    if model: return model.group(1).lower()
    text = re.split(r'\bModel\b|\bMarks:', text, flags=re.I)[0]
    return re.sub(r'[^a-z0-9]', '', text.lower())


def inventory(documents):
    """Current invoice rows only; declarations cannot corroborate themselves."""
    packing = [(doc,row) for doc in documents if doc.get('document_type')=='packing_list' for row in doc.get('line_items',[])]
    result=[]
    for doc in documents:
        if doc.get('document_type')!='commercial_invoice': continue
        values={e['entity_type']:e.get('normalized_value') for e in doc.get('entities',[])}
        for index,row in enumerate(doc.get('line_items',[])):
            reference=row.get('source_reference')
            if not reference: continue
            candidate={**row,'source_reference':reference,'source_row_id':reference,'source_document_id':doc['document_id'],
                'source_revision':doc.get('revision',1),'source_filename':doc.get('source_filename','Invoice'),
                'source_dependencies':[{'document_id':doc['document_id'],'revision':doc.get('revision',1)}],
                'currency':row.get('currency') or values.get('CURRENCY_CODE'),
                'origin':row.get('origin') or values.get('COUNTRY_OF_ORIGIN'),
                'hs_code':row.get('hs_code') or values.get('HS_CODE'),
                'valuation_basis':row.get('valuation_basis','invoice_line')}
            matches=[(p,r) for p,r in packing if _identity(row) and _identity(row)==_identity(r)
                and str(row.get('quantity'))==str(r.get('quantity'))]
            if len(matches)==1:
                pack, packed=matches[0]
                for key in ('gross_weight','net_weight','package_count','weight_unit'):
                    if packed.get(key) is not None: candidate[key]=packed[key]
                candidate['source_dependencies'].append({'document_id':pack['document_id'],'revision':pack.get('revision',1)})
                candidate['packing_source_reference']=packed.get('source_reference')
            if len(doc.get('line_items',[]))==1:
                for key,field in [('gross_weight','GROSS_WEIGHT'),('net_weight','NET_WEIGHT'),('package_count','PACKAGE_COUNT')]:
                    if candidate.get(key) is None and values.get(field) is not None: candidate[key]=str(values[field])
                if candidate.get('gross_weight') is not None: candidate.setdefault('weight_unit','kg')
            candidate['missing_review_fields']=[key for key in ('hs_code','origin','gross_weight','net_weight','package_count','currency') if candidate.get(key) in (None,'')]
            result.append(candidate)
    return result


def normalize_review(item,candidate):
    """Bind a review to real extracted values and current source dependencies."""
    result={**candidate, 'row_index':item.get('row_index')}
    for key in ('description','unit','quantity','unit_price','total_price','hs_code','origin','gross_weight','net_weight','package_count','currency'):
        if key in item: result[key]=item[key]
    for key in ('quantity','unit_price','total_price'):
        value=number(result.get(key),positive=key!='unit_price')
        if value != number(candidate.get(key),positive=key!='unit_price'):
            raise ValueError(f'{key} differs from the current invoice row. Correct the source extraction before verification.')
        result[key]=format(value,'f')
    if money(number(result['quantity'])*number(result['unit_price']))!=money(result['total_price']):
        raise ValueError('Total price must equal quantity times unit price, rounded half up to two decimals.')
    result['hs_code']=hs_code(result.get('hs_code'))
    if candidate.get('hs_code') and result['hs_code']!=hs_code(candidate['hs_code']):
        raise ValueError('HS code differs from the linked source row. Correct the source before verification.')
    result['origin']=str(result.get('origin') or '').upper().strip()
    if not re.fullmatch(r'[A-Z]{2}',result['origin']): raise ValueError('Item origin must be a two-letter country code.')
    if candidate.get('origin') and result['origin']!=str(candidate['origin']).upper():
        raise ValueError('Origin differs from the linked invoice row.')
    result['currency']=str(result.get('currency') or '').upper().strip()
    if not re.fullmatch(r'[A-Z]{3}',result['currency']): raise ValueError('Item currency must be a three-letter code.')
    if candidate.get('currency') and result['currency']!=str(candidate['currency']).upper():
        raise ValueError('Currency differs from the linked invoice row.')
    for key in ('gross_weight','net_weight','package_count'):
        value=number(result.get(key),positive=key!='net_weight',integer=key=='package_count')
        if candidate.get(key) is not None and value != number(candidate[key]):
            raise ValueError(f'{key} differs from the linked source allocation.')
        result[key]=format(value,'f')
    if number(result['net_weight'])>number(result['gross_weight']): raise ValueError('Net weight cannot exceed gross weight.')
    if str(result.get('weight_unit','kg')).lower()!='kg': raise ValueError('Declaration weights must be verified in kilograms.')
    if str(result['unit']).upper()!=str(candidate.get('unit','')).upper(): raise ValueError('Quantity unit differs from the source row.')
    if not str(result['description']).strip() or len(str(result['description']))>1000: raise ValueError('Goods description must contain 1–1000 characters.')
    result.update(weight_unit='kg',status='verified')
    return result


def check_goods(documents,fields,reviewed):
    blockers=[];prepared=[]
    def fail(code,message): blockers.append({'code':code,'field':'line_items','message':message,'source':'goods review'})
    candidates={r['source_reference']:r for r in inventory(documents)}
    if not candidates:
        fail('MISSING_LINE_ITEMS','No supported invoice rows are available. Extract or correct the source goods table.')
        return blockers,prepared
    current={}
    for row in reviewed or []:
        ref=row.get('source_row_id') or row.get('source_reference')
        candidate=candidates.get(ref)
        if row.get('validity_state') in {'stale','unverified'} and ref not in candidates:
            continue # Preserve historical reviews without counting them as current.
        if row.get('validity_state')!='current' or not candidate or row.get('source_document_id')!=candidate['source_document_id'] or row.get('source_revision')!=candidate['source_revision']:
            fail('STALE_GOODS','A saved goods row has unverified, replaced or stale source evidence. Review its current source again.');continue
        if row.get('source_dependencies')!=candidate['source_dependencies']:
            fail('STALE_GOODS','A packing or invoice dependency changed. Review the current allocation again.');continue
        if ref in current:
            fail('DUPLICATE_GOODS','The same source goods row appears more than once.');continue
        try: current[ref]=normalize_review(row,candidate)|{'review_id':row.get('id'),'verified_by':row.get('verified_by')}
        except ValueError as exc: fail('INVALID_GOODS',str(exc))
    if set(current)!=set(candidates): fail('UNVERIFIED_GOODS','Verify every current invoice row; a partial saved list cannot complete the declaration.')
    if blockers: return blockers,prepared
    items=[current[ref] for ref in candidates]
    values={f['entity_type']:f.get('consensus_value') for f in fields}
    try:
        for key,field in [('gross_weight','GROSS_WEIGHT'),('net_weight','NET_WEIGHT'),('package_count','PACKAGE_COUNT')]:
            if values.get(field) is not None:
                total=sum((number(r[key]) for r in items),Decimal(0))
                tolerance=Decimal(0) if key=='package_count' else Decimal('.01')
                if abs(total-number(values[field]))>tolerance: fail('GOODS_ALLOCATION_MISMATCH',f'Item {key} totals do not equal the shipment header.')
        if any(r['currency']!=values.get('CURRENCY_CODE') for r in items): fail('GOODS_CURRENCY_MISMATCH','Goods and invoice currency must match.')
        bases={r['valuation_basis'] for r in items}
        if len(bases)!=1: raise ValueError('Mixed valuation bases require separate source reconciliation.')
        freight=insurance=Decimal(0)
        if bases=={'FOB'} and values.get('INCOTERM') in {'CIF','CIP'}:
            if any(values.get(k) is None for k in ('FREIGHT_AMOUNT','INSURANCE_AMOUNT')):
                raise ValueError('FOB rows under CIF/CIP require explicit freight and insurance evidence.')
            freight=number(values['FREIGHT_AMOUNT']);insurance=number(values['INSURANCE_AMOUNT'])
        subtotal=sum((money(r['total_price']) for r in items),Decimal(0))
        if money(subtotal+freight+insurance)!=money(values.get('TOTAL_AMOUNT')):
            fail('GOODS_VALUE_MISMATCH','Goods totals plus evidenced freight/insurance do not equal the invoice total.')
        f_parts=allocate(freight,[r['total_price'] for r in items]);i_parts=allocate(insurance,[r['total_price'] for r in items])
        for r,f_part,i_part in zip(items,f_parts,i_parts):
            prepared.append({**r,'invoice_amount':format(money(r['total_price'])+f_part+i_part,'f'),
                'allocated_freight':format(f_part,'f'),'allocated_insurance':format(i_part,'f')})
    except ValueError as exc: fail('INVALID_GOODS_VALUATION',str(exc))
    return blockers,prepared if not blockers else []
