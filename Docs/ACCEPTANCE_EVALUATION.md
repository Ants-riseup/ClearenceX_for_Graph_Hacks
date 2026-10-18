# Frozen post-development acceptance evaluation

Date: 18 October 2026. Actual first-run evidence: [`acceptance-v1.json`](../output/verification/acceptance-v1.json).

## Protocol

Ten newly authored synthetic dossiers and twenty questions, evaluated once in graph and flat modes with the same model, final task prompt, facts and output limit. Cases cover fractional agreement, tolerance boundaries, one-source fields, missing weights/counts, invoice replacement, document injection, an ineligible carrier/consignee assertion, repeated corrections and inconsistent units.

The fixture expectations were checked against real PostgreSQL/FalkorDB before the first model run. This caught a benchmark taxonomy mistake: inconsistent units have the app's existing `warning` status, not `conflict`. The evaluator was corrected before model execution; application behavior was not changed to fit the cases.

The dataset, evaluator, application sources and Cypher hashes were saved before model calls. Results are never overwritten by the runner. Additional run spending was capped at $0.08 within the private configuration's total ceiling. There were no automatic retries or model upgrades.

## Actual results

| Measure | Graph | Flat |
|---|---:|---:|
| Safe outcomes under the full scoring contract | **19/20** | **13/20** |
| Expected citation hits | 36/36 | 36/36 |
| Input tokens | 30,149 | 51,461 |
| Output tokens | 3,412 | 4,626 |
| Median request latency | 1,922 ms | 2,321 ms |
| Estimated USD | $0.0175188 | $0.0279860 |

Model: `gpt-4.1-mini-2025-04-14`. Combined estimated cost: **$0.0455048**. Input tokens were approximately **41% lower** with graph context in this run. Provider billing/remaining credit was not independently fetched.

Both modes failed the repeated-correction gross-weight question by returning two historical affected decision IDs instead of only the decision tied to the specific latest replaced source. The underlying deterministic impact traversal and stale-memory assertions passed. Flat mode also failed some field status, citation-scope and unrelated-decision checks. Citation hits alone do not prove overall correctness.

## Interpretation and limits

This is a same-team authored acceptance set held aside from earlier implementation/model tuning, **not independent third-party validation**. No implementation or prompt tuning was performed after viewing these model outcomes. Now that it has been executed, it is regression data; another unseen assessment requires another frozen set.

Graph retrieval here is selected by benchmark questions. The separate packaged live-agent artifact establishes autonomous tool selection. Twenty synthetic questions and one provider sample per mode do not establish general accuracy, broad prompt-injection resistance, production latency or statistical superiority. Both modes saw identical scoring definitions, but graph mode deliberately receives derived status/dependency context: this measures the context representation, not a claim that SQL could never compute equivalent information.

Reproduce on isolated infrastructure with environment configuration as described in LOCAL_SETUP:

```sh
python -m evaluation.run --suite acceptance --live --max-spend 0.08 --output output/verification/acceptance-new-run.json
```

Run from the repository root with `backend` on `PYTHONPATH`, a private provider configuration and an isolated `clearancex_test` or `clearancex_eval` database URL. The command is billable; omit `--live` for the manifest only. Existing output files are refused. Do not call a repeat run a new held-out result.
