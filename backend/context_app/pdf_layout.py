"""Bounded digital PDF fragment geometry and header-driven tables (no models)."""
import re
import unicodedata
from decimal import Decimal, InvalidOperation


def fragments(page):
    result = []
    width, height = float(page.mediabox.width), float(page.mediabox.height)
    def visit(text, cm, tm, font, size):
        text = unicodedata.normalize('NFKC', text).strip()
        if not text or len(result) >= 20000:
            return
        x = tm[4] * cm[0] + tm[5] * cm[2] + cm[4]
        y = height - (tm[4] * cm[1] + tm[5] * cm[3] + cm[5])
        scale = max(abs(cm[0]), abs(cm[1]), 0.01)
        size = float(size) * scale
        if not (0 <= x <= width and 0 <= y <= height):
            return
        # Text origins are PDF coordinates; widths are conservative estimates,
        # not measured glyph outlines. Expose that distinction to consumers.
        result.append({'text': text, 'x': x, 'y': y, 'size': size,
            'bbox': [round(x, 2), round(max(0, y-size), 2),
                round(min(width, x+len(text)*size*0.55), 2), round(min(height, y+size*0.25), 2)]})
    page.extract_text(visitor_text=visit)
    return sorted(result, key=lambda s: (round(s['y']/2), s['x']))


def box(spans):
    if not spans:
        return []
    return [min(s['bbox'][0] for s in spans), min(s['bbox'][1] for s in spans),
        max(s['bbox'][2] for s in spans), max(s['bbox'][3] for s in spans)]


def decimal(text):
    match = re.search(r'-?\d[\d,]*(?:\.\d+)?', text)
    if not match:
        return None
    try:
        value = Decimal(match.group().replace(',', ''))
        return value if value.is_finite() and value >= 0 else None
    except InvalidOperation:
        return None


def column_tables(spans, kind, document_id, page):
    """Read supported tables by discovered header columns, never sample values."""
    description = next((s for s in spans if re.search(r'\bDESCRIPTION\b', s['text'], re.I)
        and ('GOODS' in s['text'].upper() or 'CONTENTS' in s['text'].upper() or 'CAGE' in s['text'].upper())), None)
    if not description:
        return []
    header_y = description['y']
    header = [s for s in spans if abs(s['y']-header_y) < 14]
    def find(pattern):
        return next((s for s in header if re.search(pattern, s['text'], re.I)), None)
    columns = {'description': description}
    if kind == 'commercial_invoice':
        columns.update(quantity=find(r'^QTY$|^QUANTITY$'), unit_price=find(r'^UNIT\s*PRICE'),
            total_price=find(r'^TOTAL(?:\s+FOB)?$'), origin=find(r'^ORIGIN$'), hs_code=find(r'^HS\s*CODE$'))
        if not all(columns[k] for k in ('quantity', 'unit_price', 'total_price')):
            return []
    elif kind == 'packing_list':
        quantity = find(r'^TOTAL\s*QTY$') or find(r'^TOTAL$')
        columns.update(quantity=quantity, quantity_per_package=find(r'^QTY/PKG$'), package_count=find(r'^PKG TYPE$'), net_weight=find(r'^NET\b'), gross_weight=find(r'^GROSS\b'), dimensions=find(r'^DIMS\b'))
        if not all(columns[k] for k in ('quantity', 'net_weight', 'gross_weight')):
            return []
    elif kind == 'customs_worksheet':
        columns.update(hs_code=find(r'\(HS\)'), weight_pair=find(r'^GROSS\s*/\s*NET'),
            fob_amount=find(r'^FOB\s*SHARE'), cif_amount=find(r'^APPORTIONED'), customs_value=find(r'^CUSTOMS\s*VAL'))
        if not all(columns[k] for k in ('hs_code', 'weight_pair', 'fob_amount', 'cif_amount')):
            return []
    else:
        return []
    columns = {k: s for k, s in columns.items() if s}
    ordered = sorted(columns, key=lambda k: columns[k]['x'])
    ranges = {}
    for index, key in enumerate(ordered):
        ranges[key] = (columns[key]['x']-10, columns[ordered[index+1]]['x']-10 if index+1 < len(ordered) else float('inf'))
    if kind in {'commercial_invoice', 'customs_worksheet'}:
        anchors = [s for s in spans if s['y'] > header_y+12 and re.fullmatch(r'\d{4}(?:\.\d{2}){1,2}', s['text'])]
    else:
        lo, hi = ranges['description']
        anchors = [s for s in spans if s['y'] > header_y+12 and lo <= s['x'] < hi
            and any(abs(n['y']-s['y']) < 3 and re.fullmatch(r'\d+\s*(?:-|–)\s*\d+', n['text'])
                and n['x'] < lo for n in spans)]
    anchors = sorted(anchors, key=lambda s: s['y'])[:100]
    rows = []
    for index, anchor in enumerate(anchors):
        end = anchors[index+1]['y']-3 if index+1 < len(anchors) else anchor['y']+65
        summaries = [s['y'] for s in spans if s['y'] > anchor['y']+4 and re.search(
            r'CONSOLIDATED|TOTAL AMOUNT IN WORDS|SUBTOTAL|STENCILED|CAGE 44', s['text'], re.I)]
        if summaries:
            end = min(end, min(summaries)-3)
        row_spans = [s for s in spans if anchor['y']-3 <= s['y'] < end]
        def cell(key, multiline=False):
            if key not in ranges:
                return ''
            lo, hi = ranges[key]
            values = [s for s in row_spans if lo <= s['x'] < hi
                and (multiline or abs(s['y']-anchor['y']) < 4)]
            return ' '.join(s['text'] for s in sorted(values, key=lambda s: (s['y'], s['x'])))
        desc = cell('description', True)
        if not desc:
            continue
        quantity_text = cell('quantity', True)
        quantity = decimal(quantity_text) if quantity_text else None
        if kind == 'customs_worksheet':
            q = re.search(r'\((\d+)\s*(u|units?|pcs)\)', desc, re.I)
            quantity = Decimal(q.group(1)) if q else None
        unit = re.search(r'\b(PCS|UNITS?|KG|CTNS?|CARTONS?)\b', quantity_text, re.I)
        row = {'row_id': f'{document_id}:{page}:table:{index}', 'document_id': document_id, 'page': page,
            'description': desc, 'quantity': str(quantity) if quantity is not None else None,
            'unit': unit.group().upper() if unit else ('PCS' if kind == 'customs_worksheet' and quantity is not None else None),
            'unit_price': None, 'total_price': None, 'status': 'needs_review', 'arithmetic_matches': None,
            'row_kind': kind, 'bbox': box(row_spans), 'geometry_status': 'pdf_origins_estimated_text_extents',
            'source_reference': f'{document_id}:page:{page}:table:{index}'}
        for key in ('hs_code', 'origin', 'dimensions'):
            if key in ranges:
                row[key] = cell(key)
        for key in ('unit_price', 'total_price', 'net_weight', 'gross_weight', 'package_count', 'fob_amount', 'cif_amount', 'customs_value'):
            if key in ranges:
                value = decimal(cell(key))
                row[key] = str(value) if value is not None else None
        if kind == 'packing_list':
            row['weight_unit'] = 'kg' if any('KG' in s['text'].upper() for s in header) else 'unsupported'
        if kind == 'customs_worksheet':
            weights = re.findall(r'\d+(?:\.\d+)?', cell('weight_pair'))
            if len(weights) == 2:
                row.update(gross_weight=weights[0], net_weight=weights[1], weight_unit='kg')
        if kind == 'commercial_invoice':
            price, total = decimal(cell('unit_price')), decimal(cell('total_price'))
            if quantity is None or price is None or total is None:
                continue
            row['arithmetic_matches'] = (quantity*price).quantize(Decimal('.01')) == total.quantize(Decimal('.01'))
            row['valuation_basis'] = 'FOB' if re.search(r'FOB', columns['total_price']['text'], re.I) else 'invoice_line'
        rows.append(row)
    return rows
