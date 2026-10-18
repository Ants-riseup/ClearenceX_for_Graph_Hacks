"""Actual user-supplied layouts plus value-independent extraction regressions."""
from pathlib import Path
from decimal import Decimal
import pytest
from context_app.text_extract import extract
from context_app.fixtures import write_pdf
from reasoning.entity_resolution import resolve_documents
from reasoning.cusdec_readiness import build_cusdec_readiness


INPUTS = Path(__file__).resolve().parents[2] / 'Docs' / 'TEST FILE'


@pytest.mark.parametrize('filename,kind,expected,row_count', [
    ('Air Waybill.pdf', 'awb', {'AWB_NUMBER':'003-78419204','GROSS_WEIGHT':120,'PACKAGE_COUNT':8}, 0),
    ('Commercial Invoice (1).pdf', 'commercial_invoice', {'TOTAL_AMOUNT':15600,'INCOTERM':'CIF','INVOICE_NUMBER':'NPE-2026-9410'}, 2),
    ('Export Packing List.pdf', 'packing_list', {'GROSS_WEIGHT':120,'NET_WEIGHT':100,'PACKAGE_COUNT':8}, 2),
    ('Customs Declaration Entry Worksheet.pdf', 'customs_worksheet', {'TOTAL_AMOUNT':15600,'PACKAGE_COUNT':8,'NET_WEIGHT':100}, 2),
])
def test_supplied_pdf_headers_tables_and_provenance(filename,kind,expected,row_count):
    path = INPUTS / filename
    if not path.is_file():
        pytest.skip('Private supplied PDF is intentionally outside the source archive.')
    result = extract(path, 'source-test')
    fields = {e['entity_type']:e['normalized_value'] for e in result['entities']}
    assert result['document_type'] == kind
    for field,value in expected.items(): assert fields[field] == value
    assert len(result['line_items']) == row_count
    assert not result['missing_fields'] and result['quality_status'] == 'extracted_needs_review'
    assert all(r['page'] == 1 and len(r['bbox']) == 4 and r['status'] == 'needs_review' for r in result['line_items'])
    assert all(check['matches'] for check in result['validation_checks'])
    if kind == 'commercial_invoice':
        assert [(r['quantity'],r['unit_price'],r['total_price']) for r in result['line_items']] == [('100','75.00','7500.00'),('20','350.00','7000.00')]
        assert sum(Decimal(r['total_price']) for r in result['line_items']) == Decimal('14500')
        assert all(r['arithmetic_matches'] and r['valuation_basis']=='FOB' for r in result['line_items'])
    if kind == 'packing_list':
        assert [(r['net_weight'],r['gross_weight']) for r in result['line_items']] == [('40.00','48.00'),('60.00','72.00')]
        assert all(r['unit_price'] is None for r in result['line_items'])
    if kind == 'customs_worksheet':
        assert not resolve_documents('test', [result])
        assert all(e['resolver_eligible'] is False for e in result['entities'])
    if kind == 'awb':
        assert fields['GROSS_WEIGHT'] != 142 # chargeable weight has a separate column
        assert 'LANKA INDUSTRIAL' in fields['CONSIGNEE_NAME']
        assert 'NIPPON PRECISION' in fields['SHIPPER_NAME']


def test_label_variants_use_actual_values_not_sample_constants(tmp_path):
    path = tmp_path / 'changed.pdf'
    write_pdf(path, ['Commercial Invoice', 'INVOICE NO: OTHER-723', 'Incoterms: DAP',
        'TOTAL CIF TESTPORT: EUR 2,345.67', 'Currency: EUR', 'Gross Mass (Cage 35): 38.5 kg',
        'Net Mass (Cage 38): 30.2 kg', 'Package Count: 3', 'Packing List', 'Air Waybill: REF-888'])
    result = extract(path, 'variant')
    values = {e['entity_type']:e['normalized_value'] for e in result['entities']}
    assert result['document_type']=='commercial_invoice' # later attachments cannot win
    assert values['INVOICE_NUMBER']=='OTHER-723' and values['TOTAL_AMOUNT']==2345.67
    assert values['INCOTERM']=='DAP' and values['NET_WEIGHT']==30.2 and values['GROSS_WEIGHT']==38.5
    assert result['quality_status']=='partial' and 'CONSIGNEE_NAME' in result['missing_fields']


def test_unsupported_table_is_partial_and_blocks_export(tmp_path):
    path = tmp_path / 'unsupported.pdf'
    write_pdf(path, ['Commercial Invoice','Invoice No: UNSUPPORTED-1', 'Currency: USD',
        'Description of Goods', 'An unsupported table without a quantity or prices'])
    result = extract(path, 'unsupported')
    assert result['quality_status']=='partial' and not result['line_items']
    readiness = build_cusdec_readiness([result], resolve_documents('test',[result]))
    assert not readiness['export_allowed']
    assert 'PARTIAL_EXTRACTION' in {b['code'] for b in readiness['blockers']}


def test_unreviewed_goods_are_not_export_permission(tmp_path):
    path = tmp_path / 'rows.pdf'
    write_pdf(path, ['Commercial Invoice','Invoice No: ROW-1','Item | 3 | PCS | 2.00 | 6.00'])
    result = extract(path, 'rows')
    readiness = build_cusdec_readiness([result], resolve_documents('test',[result]))
    assert 'UNVERIFIED_GOODS' in {b['code'] for b in readiness['blockers']}

