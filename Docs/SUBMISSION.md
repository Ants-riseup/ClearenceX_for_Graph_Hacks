# ClearanceX submission draft

## Project and track

**ClearanceX Context Agent — Track 01: Agents That Act on Connected Data**

## Short description

ClearanceX connects shipment documents, evidence and reviewer decisions in FalkorDB. An AI agent investigates conflicting values and proposes cited review tasks. When a supporting document changes, graph traversal identifies which approvals and memory become stale while preserving unrelated decisions.

## Problem and users

Export teams reconcile invoices, packing lists and transport documents. A changed source can invalidate a previous decision even when the saved answer still looks reasonable. Reviewers need evidence provenance and a clear indication of what must be checked again.

## Implementation and graph contribution

FastAPI stores source history, reviews and a durable outbox in PostgreSQL. A worker projects tenant-isolated, versioned FalkorDB snapshots. A bounded agent chooses typed tools for issues, evidence, rules, approved memory, change impact and pending proposals. People approve; the agent cannot do so. Source correction triggers multi-hop dependency traversal and selective invalidation.

Graph evidence gates proposals/approvals. Missing graph context does not fall back to an equivalent SQL answer. The demo shows weight approval becoming stale while unrelated invoice package approval stays current. Essential queries are in `backend/context_app/queries/`.

## Evaluation and limits

Use the final numbers in `Docs/ACCEPTANCE_EVALUATION.md` and `Docs/RELEASE_READINESS.md`. Retained model/MCP runs, regression tests and the first-run acceptance comparison are separate evidence types. Synthetic fixtures are labeled. General scanned OCR, maintained tariffs, official customs compatibility, cross-shipment learning and Company Brain are not claimed.

## Existing work and AI assistance

Earlier ClearanceX UI/domain infrastructure is retained. The graph context, dependency invalidation, bounded tools and protected review flow are documented in `Docs/GRAPH_HACKS_DELTA.md`. Codex assisted implementation, tests and documentation. Participants must identify their own meaningful contribution, review and explain the implementation, and distinguish inherited code from event-time work.

## Links and final checks

- Configured repository: `https://github.com/Ants-riseup/ClearenceX_for_Graph_Hacks` — verify the final public commit and signed-out access.
- Setup/model/queries: README and `Docs/GRAPH_MODEL.md`.
- Working video: **not recorded; supply the actual video URL**.
- Deployment: complete local Docker instructions supplied; no public deployment claimed.
- Registration, team, reuse eligibility and data/asset rights: **team verification required**.

This prepared text is not a completed official submission. Check the live form's field limits and required links.
