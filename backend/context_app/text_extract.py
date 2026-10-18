"""Actual local digital PDF extraction with heading and column provenance."""
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path
from pypdf import PdfReader
from .pdf_layout import fragments, box, column_tables

NUM = r'([0-9]+(?:[,.][0-9]+)*)'
WEIGHT = r'(?:\s*\(\s*Cage\s+\d+\s*\))?\s*[:=]?\s*'
PATTERNS = {
    'GROSS_WEIGHT': rf'\b(?:total\s+)?gross[ _-]*(?:weight|mass|wt){WEIGHT}{NUM}\s*(kg|kgs|kilograms?|lb|lbs|tonnes?|mt)?',
    'NET_WEIGHT': rf'\b(?:total\s+)?net[ _-]*(?:weight|mass|wt){WEIGHT}{NUM}\s*(kg|kgs|kilograms?|lb|lbs|tonnes?|mt)?',
    'PACKAGE_COUNT': rf'\b(?:package[ _-]*count|number of packages|no\.? of packages|total packages)\s*[:=]?\s*{NUM}',
    'TOTAL_AMOUNT': rf'\b(?:total[ _-]*amount|invoice total|grand total|total (?:CIF|CIP|FOB)(?:\s+[A-Za-z]+)?)\s*[:=]?\s*(?:USD|EUR|LKR)?\s*[$€£]?\s*{NUM}',
    'INVOICE_NUMBER': r'\b(?:invoice[ _-]*(?:number|no\.?|ref(?:erence)?)|associated commercial invoice)\s*[:=#]?\s*([A-Z0-9][A-Z0-9/-]{1,49})',
    'AWB_NUMBER': r'\b(?:awb[ _-]*(?:number|no\.?)|air waybill[ _-]*(?:number|no\.?)|manifest/awb|transport master document ref)\s*[:=#]?\s*([0-9]{3}\s*-\s*[0-9 ]{8,11}|[A-Z0-9][A-Z0-9/-]{3,49})',
    'BL_NUMBER': r'\b(?:bl[ _-]*(?:number|no\.?)|bill of lading[ _-]*(?:number|no\.?))\s*[:=#]?\s*([A-Z0-9][A-Z0-9/-]{1,49})',
    'INCOTERM': r'\b(?:incoterms?|terms of delivery|delivery terms)\s*[:=]?\s*(EXW|FCA|FAS|FOB|CFR|CIF|CPT|CIP|DAP|DPU|DDP)\b',
    'CURRENCY_CODE': r'\b(?:currency|currency code)\s*[:=]?\s*(USD|EUR|LKR|GBP|JPY|CNY|INR)\b',
    'CONSIGNEE_NAME': r'\bconsignee(?:[ _-]*name)?\s*[:=]\s*([^\r\n]{2,150})',
    'SHIPPER_NAME': r'\b(?:shipper|exporter)(?:[ _-]*name)?\s*[:=]\s*([^\r\n]{2,150})',
    'FREIGHT_AMOUNT': rf'\b(?:international air freight|freight amount)\s*[:=]?\s*(?:USD)?\s*\$?\s*{NUM}',
    'INSURANCE_AMOUNT': rf'\b(?:marine\s*/\s*cargo insurance|insurance amount)\s*[:=]?\s*(?:USD)?\s*\$?\s*{NUM}',
    'COUNTRY_OF_ORIGIN': r'\b(?:country of origin|origin country)\s*[:=]\s*([A-Z]{2})\b',
    'PORT_OF_LOADING': r'\b(?:airport|port|place) of loading\s*[:=]\s*([^\r\n]{2,100}(?:\n\([A-Z]{3}\))?)',
    'PORT_OF_DISCHARGE': r'\b(?:airport|port|place) of discharge\s*[:=]\s*([^\r\n]{2,100}(?:\n\([A-Z]{3}\))?)',
}
NUMERIC = {'GROSS_WEIGHT', 'NET_WEIGHT', 'PACKAGE_COUNT', 'TOTAL_AMOUNT', 'FREIGHT_AMOUNT', 'INSURANCE_AMOUNT'}
TITLES = [('customs_worksheet', r'CUSTOMS DECLARATION.*(?:WORKSHEET|ENTRY)|CUSDEC.*WORKSHEET'),
    ('packing_list', r'(?:EXPORT\s+)?PACKING LIST'), ('awb', r'(?:NOT NEGOTIABLE\s+)?AIR WAYBILL(?:\s*/.*)?|AWB'),
    ('bl', r'BILL OF LADING'), ('freight_invoice', r'FREIGHT INVOICE'),
    ('commercial_invoice', r'COMMERCIAL INVOICE|INVOICE'), ('delivery_order', r'DELIVERY ORDER')]


def classify(pages, layouts):
    # Whole-line headings only. An attachment/reference in body text cannot win.
    for text in pages[:1]:
        lines = text.splitlines()
        for line in lines[:35]:
            for kind, pattern in TITLES:
                if re.fullmatch(pattern, line.strip(), re.I):
                    return kind
    return 'unknown'


def extract(path, document_id):
    reader = PdfReader(path)
    pages = [unicodedata.normalize('NFKC', page.extract_text() or '') for page in reader.pages]
    if not any(text.strip() for text in pages):
        return None
    layouts = [fragments(page) for page in reader.pages]
    kind = classify(pages, layouts)
    entities, rows, seen = [], [], set()
    def add(field, raw, value, page, spans=(), unit=None):
        key = (field, str(value), unit, page)
        if key in seen:
            return
        seen.add(key)
        entity = {'entity_type': field, 'value': raw.strip(), 'normalized_value': value, 'unit': unit,
            'page': page, 'bbox': box(spans), 'geometry_status': 'pdf_origins_estimated_text_extents' if spans else 'unavailable',
            'extraction_confidence': 0.0, 'confidence_status': 'not_calibrated',
            'source_method': 'digital_pdf_text', 'ocr_text': raw,
            'resolver_eligible': kind != 'customs_worksheet'}
        if field == 'CONSIGNEE_NAME': entity['party_role'] = 'consignee'
        if field == 'SHIPPER_NAME': entity['party_role'] = 'shipper'
        entities.append(entity)
    for index, (text, spans) in enumerate(zip(pages, layouts)):
        page = index+1
        for field, expression in PATTERNS.items():
            for match in re.finditer(expression, text, re.I):
                value, unit = match.group(1).strip(), None
                if field in NUMERIC:
                    try:
                        number = Decimal(value.replace(',', ''))
                        if not number.is_finite() or number < 0: continue
                        if field == 'PACKAGE_COUNT' and number != number.to_integral_value(): continue
                        value = int(number) if field == 'PACKAGE_COUNT' else float(number)
                    except (InvalidOperation, ValueError): continue
                    if field in {'GROSS_WEIGHT', 'NET_WEIGHT'}:
                        unit = (match.group(2) or '').lower() or None
                        if unit in {'kgs', 'kilogram', 'kilograms'}: unit = 'kg'
                        if unit == 'lbs': unit = 'lb'
                if field == 'AWB_NUMBER': value = re.sub(r'\s+', '', value)
                if field in {'PORT_OF_LOADING','PORT_OF_DISCHARGE'}:
                    code = re.search(r'\(([A-Z]{3})\)', value)
                    if code: value = code.group(1)
                matching = [s for s in spans if match.group(1).strip() in s['text']]
                add(field, match.group(), value, page, matching[:1], unit)
        # Read the company immediately under a role heading in the SAME column.
        for field, pattern in [('CONSIGNEE_NAME', r"^CONSIGNEE(?:'S)?(?:\s+NAME AND ADDRESS|\s*/\s*IMPORTER|\s*&\s*DELIVERY POINT)$"),
                ('SHIPPER_NAME', r"^SHIPPER(?:'S)? NAME AND ADDRESS$|^CONSIGNOR\s*/\s*EXPORTER(?:\s*\(SHIPPER\))?$")]:
            for label in spans:
                if not re.fullmatch(pattern, label['text'], re.I): continue
                candidates = [s for s in spans if abs(s['x']-label['x']) < 8 and 3 < s['y']-label['y'] < 30]
                if candidates:
                    source = min(candidates, key=lambda s: s['y'])
                    add(field, label['text']+'\n'+source['text'], source['text'], page, [label, source])
        # AWB table: gross is under its own header, never chargeable weight.
        if kind == 'awb':
            for field, pattern in [('PORT_OF_LOADING', r'^AIRPORT OF DEPARTURE.*'), ('PORT_OF_DISCHARGE', r'^AIRPORT OF DESTINATION$')]:
                for label in spans:
                    if not re.fullmatch(pattern,label['text'],re.I): continue
                    candidates=[s for s in spans if abs(s['x']-label['x'])<8 and 3<s['y']-label['y']<25]
                    if candidates:
                        source=min(candidates,key=lambda s:s['y']);code=re.search(r'\(([A-Z]{3})\)',source['text'])
                        add(field,label['text']+'\n'+source['text'],code.group(1) if code else source['text'],page,[label,source])
            for field, pattern in [('GROSS_WEIGHT', r'^Gross\s+(?:Wt|Weight)\s*\(kg\)$'), ('PACKAGE_COUNT', r'^No\.?\s*(?:Pcs|Pieces|Packages)$')]:
                for header in spans:
                    if not re.fullmatch(pattern, header['text'], re.I): continue
                    values = [s for s in spans if 5 < s['y']-header['y'] < 60 and abs(s['x']-header['x']) < 30
                        and re.fullmatch(r'\d+(?:\.\d+)?\s*K?', s['text'], re.I)]
                    if values:
                        source = min(values, key=lambda s: s['y'])
                        number = Decimal(re.search(NUM, source['text']).group(1))
                        if field == 'PACKAGE_COUNT' and number != number.to_integral_value(): continue
                        add(field, header['text']+'\n'+source['text'], int(number) if field == 'PACKAGE_COUNT' else float(number), page, [header,source], 'kg' if field == 'GROSS_WEIGHT' else None)
        if kind == 'customs_worksheet':
            package = re.search(r'\bCage\s+6\s+Packages:\s*(\d+)\b', text, re.I)
            if package: add('PACKAGE_COUNT', package.group(), int(package.group(1)), page)
            totals = re.search(r'Consolidated\s+CusDec\s+Totals:\s*'+NUM+r'\s*/\s*'+NUM, text, re.I)
            if totals:
                add('GROSS_WEIGHT', totals.group(), float(Decimal(totals.group(1))), page, unit='kg')
                add('NET_WEIGHT', totals.group(), float(Decimal(totals.group(2))), page, unit='kg')
            currency = re.search(r'Invoice Total:\s*(USD|EUR|LKR|GBP|JPY|CNY|INR)', text, re.I)
            if currency: add('CURRENCY_CODE', currency.group(), currency.group(1).upper(), page)
        rows.extend(column_tables(spans, kind, document_id, page))
        # Retain the explicit pipe table format for text-first/legacy inputs.
        for line_index, line in enumerate(text.splitlines()):
            cells = [cell.strip() for cell in line.split('|')]
            if len(cells) != 5 or not cells[0]: continue
            try:
                quantity, price, total = (Decimal(cells[i].replace(',', '')) for i in (1,3,4))
                if not all(v.is_finite() and v >= 0 for v in (quantity,price,total)): continue
            except InvalidOperation: continue
            rows.append({'row_id':f'{document_id}:{page}:{line_index}', 'document_id':document_id,'page':page,
                'description':cells[0], 'quantity':str(quantity),'unit':cells[2],'unit_price':str(price),'total_price':str(total),
                'bbox':[], 'source_reference':f'{document_id}:page:{page}:row:{line_index}', 'status':'needs_review',
                'arithmetic_matches':(quantity*price).quantize(Decimal('.01'))==total.quantize(Decimal('.01'))})
    if kind == 'commercial_invoice':
        origins={row.get('origin') for row in rows if row.get('origin')}
        if len(origins)==1 and all(row.get('origin') for row in rows):
            origin=next(iter(origins))
            if re.fullmatch(r'[A-Z]{2}',origin): add('COUNTRY_OF_ORIGIN','Invoice goods origin: '+origin,origin,rows[0]['page'])
    # Missing expected fields are explicit quality warnings, not invented values.
    required = {'awb': {'AWB_NUMBER','PACKAGE_COUNT','GROSS_WEIGHT','CONSIGNEE_NAME','SHIPPER_NAME'},
        'commercial_invoice': {'INVOICE_NUMBER','TOTAL_AMOUNT','CURRENCY_CODE','INCOTERM','CONSIGNEE_NAME','SHIPPER_NAME','PORT_OF_LOADING','PORT_OF_DISCHARGE'},
        'packing_list': {'PACKAGE_COUNT','NET_WEIGHT','GROSS_WEIGHT','CONSIGNEE_NAME'}}.get(kind,set())
    missing = sorted(required-{e['entity_type'] for e in entities})
    warnings = ['Actual digital PDF text and header-aligned columns parsed locally; confidence is not calibrated.',
        'PDF text origins are preserved; text bounding extents are estimated. All extracted goods rows require human verification.']
    if missing: warnings.append('Missing expected fields: '+', '.join(missing)+'. Manual review required.')
    table_expected = kind in {'commercial_invoice','packing_list','customs_worksheet'} and bool(re.search(r'DESCRIPTION|CONTENTS', '\n'.join(pages), re.I))
    if table_expected and not rows: warnings.append('A goods table was detected but no supported rows were extracted. Manual entry required.')
    if kind == 'customs_worksheet': warnings.append('Supporting customs worksheet: not independent commercial evidence; excluded from canonical shipment consensus.')
    validations = []
    values = {e['entity_type']: e['normalized_value'] for e in entities}
    if kind == 'commercial_invoice' and rows and all(r.get('total_price') is not None for r in rows):
        subtotal = sum((Decimal(r['total_price']) for r in rows), Decimal(0))
        if all(r.get('valuation_basis') == 'FOB' for r in rows) and all(k in values for k in ('FREIGHT_AMOUNT','INSURANCE_AMOUNT','TOTAL_AMOUNT')):
            calculated = subtotal + Decimal(str(values['FREIGHT_AMOUNT'])) + Decimal(str(values['INSURANCE_AMOUNT']))
            validations.append({'check': 'FOB_plus_freight_plus_insurance_equals_invoice_total',
                'matches': abs(calculated-Decimal(str(values['TOTAL_AMOUNT']))) <= Decimal('.01'), 'calculated': str(calculated)})
    if kind == 'packing_list' and rows:
        for key, field in [('gross_weight','GROSS_WEIGHT'), ('net_weight','NET_WEIGHT')]:
            if field in values and all(r.get(key) is not None for r in rows):
                calculated = sum((Decimal(r[key]) for r in rows), Decimal(0))
                validations.append({'check': key+'_rows_equal_header', 'matches': abs(calculated-Decimal(str(values[field]))) <= Decimal('.01'), 'calculated': str(calculated)})
    invalid_rows = any(r.get('arithmetic_matches') is False for r in rows)
    failed_checks = any(not check['matches'] for check in validations)
    if invalid_rows or failed_checks: warnings.append('Row arithmetic or header reconciliation failed. Manual correction required.')
    currency = next((e['normalized_value'] for e in entities if e['entity_type']=='CURRENCY_CODE'),None)
    for row in rows:
        if currency and row.get('unit_price') is not None: row['currency']=currency
    return {'document_id':document_id,'document_type':kind,'source_filename':Path(path).name,
        'extraction_method':'digital_pdf_text','classification_confidence':0.0,'entities':entities,'line_items':rows,
        'page_count':len(pages),'raw_ocr':[], 'errors':[] if kind!='unknown' and entities else ['Document type or labeled fields require manual review.'],
        'warnings':warnings,'quality_status':'partial' if missing or (table_expected and not rows) or invalid_rows or failed_checks else 'extracted_needs_review',
        'validation_checks': validations,
        'missing_fields':missing,'requires_human_review':True,'source_role':'supporting_declaration' if kind=='customs_worksheet' else 'commercial_source'}
