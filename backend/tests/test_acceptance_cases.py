"""Validate acceptance fixture expectations against actual graph state, no model."""
import time
from evaluation.acceptance_cases import create_cases, MANIFEST
from evaluation.cases import revision
from context_app.graph import GraphRepository


def test_new_acceptance_fixture_statuses_freshness_and_impact(reviewer):
    _, user = reviewer
    graph = GraphRepository(user['tenant_id'])
    cases = create_cases(user)
    assert len(cases) == 10 and sum(len(case['questions']) for case in cases) == 20
    assert len({case['id'] for case in MANIFEST}) == 10
    for case in cases:
        sid, rev = case['shipment_id'], revision(case['shipment_id'])
        issues = {field['canonical_field_id']: field for field in graph.issues(sid, rev)}
        for name, expected, _ in case['questions']:
            fid = f'shipment:{sid}:field:{name}'
            field = issues.get(fid)
            assert (field['status'] if field else 'missing') == expected, (case['id'], name, field)
            evidence = graph.evidence(sid, rev, fid)
            assert all(assertion['document_id'] != case['old_document_id'] for assertion in evidence)
        if case['old_document_id']:
            affected = graph.impact(sid, rev, case['old_document_id'])
            assert {item['id'] for item in affected if item['type'] == 'Decision'} == set(case['affected_decision_ids'])
            memory = graph.memory(sid, rev, int(time.time()))
            assert memory and all(item['decision_id'] not in case['affected_decision_ids'] for item in memory)
