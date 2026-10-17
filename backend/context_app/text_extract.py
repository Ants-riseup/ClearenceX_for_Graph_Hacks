"""Local extraction from actual digital PDF text; no synthetic values or API calls."""
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from pypdf import PdfReader

NUM = r'([0-9]+(?:[,.][0-9]+)*)'
PATTERNS = {
    'GROSS_WEIGHT': rf'\b(?:gross[ _-]*weight|gross[ _-]*mass)\s*[:=]?\s*{NUM}\s*(kg|kgs|kilograms?|lb|lbs|tonnes?|mt)?',
    'NET_WEIGHT': rf'\bnet[ _-]*(?:weight|mass)\s*[:=]?\s*{NUM}\s*(kg|kgs|kilograms?|lb|lbs|tonnes?|mt)?',
    'PACKAGE_COUNT': rf'\b(?:package[ _-]*count|number of packages|no\.? of packages|total packages)\s*[:=]?\s*{NUM}',
    'TOTAL_AMOUNT': rf'\b(?:total[ _-]*amount|invoice total|grand total)\s*[:=]?\s*(?:USD|EUR|LKR)?\s*{NUM}',
    'INVOICE_NUMBER': r'\b(?:invoice[ _-]*(?:number|no\.?))\s*[:=#]?\s*([A-Z0-9][A-Z0-9/-]{1,49})',
    'AWB_NUMBER': r'\b(?:awb[ _-]*(?:number|no\.?)|air waybill[ _-]*(?:number|no\.?))\s*[:=#]?\s*([A-Z0-9][A-Z0-9/-]{1,49})',
    'BL_NUMBER': r'\b(?:bl[ _-]*(?:number|no\.?)|bill of lading[ _-]*(?:number|no\.?))\s*[:=#]?\s*([A-Z0-9][A-Z0-9/-]{1,49})',
    'INCOTERM': r'\b(?:incoterm|terms of delivery)\s*[:=]?\s*(EXW|FCA|FAS|FOB|CFR|CIF|CPT|CIP|DAP|DPU|DDP)\b',
    'CURRENCY_CODE': r'\b(?:currency|currency code)\s*[:=]?\s*(USD|EUR|LKR|GBP|JPY|CNY|INR)\b',
    'CONSIGNEE_NAME': r'\bconsignee(?:[ _-]*name)?\s*[:=]\s*([^\r\n]{2,150})',
    'SHIPPER_NAME': r'\b(?:shipper|exporter)(?:[ _-]*name)?\s*[:=]\s*([^\r\n]{2,150})',
}


def extract(path, document_id):
    reader = PdfReader(path)
    pages = [(index + 1, page.extract_text() or '') for index, page in enumerate(reader.pages)]
    if not any(text.strip() for _, text in pages):
        return None  # scanned document: use the separately installed OCR engine
    heading = '\n'.join(text[:1500] for _, text in pages[:2]).lower()
    kind = next((kind for pattern, kind in [('packing list', 'packing_list'), ('air waybill', 'awb'),
        ('bill of lading', 'bl'), ('commercial invoice', 'commercial_invoice'), ('freight invoice', 'freight_invoice'),
        ('delivery order', 'delivery_order'), ('invoice', 'commercial_invoice'), ('awb', 'awb')] if pattern in heading), 'unknown')
    entities, rows = [], []
    for page, text in pages:
        for field, expression in PATTERNS.items():
            for match in re.finditer(expression, text, re.I):
                raw, unit = match.group(1).strip(), None
                value = raw
                if field in {'GROSS_WEIGHT', 'NET_WEIGHT', 'PACKAGE_COUNT', 'TOTAL_AMOUNT'}:
                    try:
                        number = Decimal(raw.replace(',', ''))
                        if field == 'PACKAGE_COUNT':
                            if number != number.to_integral_value():
                                continue
                            value = int(number)
                        else:
                            value = float(number)
                    except (InvalidOperation, ValueError):
                        continue
                    if field in {'GROSS_WEIGHT', 'NET_WEIGHT'}:
                        unit = (match.group(2) or '').lower() or None
                        if unit in {'kgs', 'kilogram', 'kilograms'}: unit = 'kg'
                        if unit == 'lbs': unit = 'lb'
                entities.append({'entity_type': field, 'value': match.group(0).strip(), 'normalized_value': value,
                    'unit': unit, 'page': page, 'bbox': [], 'extraction_confidence': 0.0,
                    'confidence_status': 'not_calibrated', 'source_method': 'digital_pdf_text', 'ocr_text': match.group(0),
                    **({'party_role': 'consignee', 'resolver_eligible': True} if field == 'CONSIGNEE_NAME' else {})})
        # An explicit pipe-delimited table contract. Unsupported layouts remain
        # unextracted rather than guessed. Repeated rows retain page/row identity.
        for index, line in enumerate(text.splitlines()):
            cells = [cell.strip() for cell in line.split('|')]
            if len(cells) != 5 or not cells[0]: continue
            try:
                quantity, price, total = (Decimal(cells[i].replace(',', '')) for i in (1, 3, 4))
                if not all(v.is_finite() and v >= 0 for v in (quantity, price, total)): continue
            except InvalidOperation:
                continue
            rows.append({'row_id': f'{document_id}:{page}:{index}', 'document_id': document_id, 'page': page,
                'description': cells[0], 'quantity': str(quantity), 'unit': cells[2], 'unit_price': str(price), 'total_price': str(total),
                'bbox': [], 'source_reference': f'{document_id}:page:{page}:row:{index}', 'status': 'needs_review',
                'arithmetic_matches': (quantity * price).quantize(Decimal('0.01')) == total.quantize(Decimal('0.01'))})
    return {'document_id': document_id, 'document_type': kind, 'source_filename': Path(path).name,
        'extraction_method': 'digital_pdf_text', 'classification_confidence': 0.0, 'entities': entities,
        'line_items': rows, 'page_count': len(pages), 'raw_ocr': [], 'errors': [] if kind != 'unknown' and entities else ['Document type or labeled fields require manual review.'],
        'warnings': ['Actual PDF text parsed locally; extraction is not calibrated. Page links available; bounding boxes unavailable.',
            'Only explicitly labeled fields and pipe-delimited goods rows are supported by the digital-text parser.']}
