"""Keep one source revision's impact separate from other historical corrections."""


def impact_envelope(document_id, revision, affected):
    if any(item.get('source_document_id') != document_id for item in affected):
        raise ValueError('Graph impact returned evidence for a different source.')
    return {'source_document_id': document_id, 'graph_revision': revision,
        'affected_decision_ids': sorted({item['id'] for item in affected if item['type'] == 'Decision'}),
        'affected_records': affected,
        'scope': 'Only dependencies of this exact source document revision. Other historical stale decisions are not part of this result.'}
