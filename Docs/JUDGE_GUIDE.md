# ClearanceX: judge guide

**Track 01 — Agents That Act on Connected Data.**

## Try the defining behavior

1. Follow the README Docker setup and bootstrap an ordinary private demo account.
2. Open Context Agent, create a synthetic example and wait for graph synchronization.
3. With inference configured, run the investigation and inspect tools, citations and the pending proposal. Without inference, inspect graph evidence/human review; do not call that a live agent run.
4. Approve packing-list gross weight and separately approve invoice package count.
5. Correct the packing list. Weight approval becomes stale; package count stays current. Inspect the dependency preview and history.
6. Investigate again and reopen the dossier in another authenticated session. Current memory survives; stale approval is excluded.

## Inspect the implementation

FalkorDB performs decision dependency traversal, not only visualization. `backend/context_app/queries/impact.cypher` finds affected records; `service.replace_document` consumes those IDs. Outage or incomplete projection blocks graph-dependent action. PostgreSQL preserves authoritative records while an outbox projects immutable graph revisions.

The agent can propose a task but cannot approve or transmit a declaration. Retrieved evidence IDs and numeric claims are checked. Documents are untrusted input.

| Question | Evidence |
|---|---|
| Real model-selected tools? | `output/verification/packaged-flow.json` |
| Actual MCP transport and revoked-session denial? | `output/verification/packaged-mcp.json` |
| Fresh cases versus the old development set? | `Docs/ACCEPTANCE_EVALUATION.md` |
| Reproducible source? | `Docs/RELEASE_READINESS.md` |
| Existing work and AI contribution? | `Docs/GRAPH_HACKS_DELTA.md` and README disclosure |

Synthetic source PDFs have precomputed extraction; separate tests parse actual digital PDFs. General OCR accuracy, official tariffs/customs filing and the full retained roadmap are not claimed complete. See `Docs/MANUAL_ACCEPTANCE.md` for human checks still requiring observation.
