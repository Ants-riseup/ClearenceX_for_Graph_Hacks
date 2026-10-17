"""Warm graph-query timing on a new synthetic tenant; no paid model calls."""
import json
import platform
import statistics
import time
import uuid
from pathlib import Path
from database.connection import init_db, SessionLocal
from context_app.admin import create_user
from context_app.service import create_dossier
from context_app.fixtures import hero_documents
from context_app.graph import GraphRepository
from context_app.models import ContextDossier
from .cases import sync


def main():
    import os
    if not any(name in os.environ.get('DATABASE_URL', '') for name in ('clearancex_test', 'clearancex_eval')):
        raise SystemExit('Use isolated evaluation/test infrastructure.')
    init_db()
    user, _ = create_user(f'benchmark-{uuid.uuid4()}@example.test', f'Benchmark {uuid.uuid4()}')
    sid = create_dossier(user, hero_documents(), 'Warm graph benchmark')
    sync(sid)
    graph = GraphRepository(user['tenant_id'])
    field = f'shipment:{sid}:field:GROSS_WEIGHT'
    for _ in range(5): graph.evidence(sid, 1, field)
    timings = []
    for _ in range(100):
        start = time.perf_counter()
        assert len(graph.evidence(sid, 1, field)) == 3
        timings.append((time.perf_counter() - start) * 1000)
    result = {'protocol': '5 warmup then 100 sequential evidence reads; one synthetic dossier, three source assertions; no cold-start or concurrent-load claim.',
        'platform': platform.platform(), 'processor': platform.processor(), 'python': platform.python_version(), 'graph': 'FalkorDB v4.12.0',
        'calls': 100, 'median_ms': statistics.median(timings), 'max_ms': max(timings), 'p95_ms_nearest_rank': sorted(timings)[94], 'all_ms': timings,
        'paid_model_calls': 0}
    path = Path('output/verification/graph-benchmark.json'); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'all_ms'}, indent=2))


if __name__ == '__main__': main()
