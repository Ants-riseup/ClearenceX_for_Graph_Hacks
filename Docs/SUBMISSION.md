# ClearanceX submission draft

## Project and track

**ClearanceX Context Agent — Track 01: Agents That Act on Connected Data**

## Short description

ClearanceX connects shipment documents, evidence and reviewer decisions in FalkorDB. An AI agent investigates conflicting values and proposes cited review tasks. When a supporting document changes, graph traversal identifies which approvals and memory become stale while preserving unrelated decisions.

## Problem and users

Export teams reconcile invoices, packing lists and transport documents. A changed source can invalidate a previous decision even when the saved answer still looks reasonable. Reviewers need evidence provenance and a clear indication of what must be checked again.

## Implementation and graph contribution

### Copy-ready answer: How did you use FalkorDB?

FalkorDB is ClearanceX's connected context and dependency engine. We model shipments, document revisions, extracted assertions, review decisions, tasks, approved memory and export snapshots as nodes linked by evidence and dependency relationships. Tenant-scoped, parameterized Cypher retrieves current evidence and traverses dependencies across multiple hops. A bounded AI agent selects graph tools, explains conflicting values with source citations and proposes a review task; it cannot approve its own answer.

Our key use case is selective invalidation: correcting a packing list makes the weight approval that depended on it stale, while an unrelated invoice package-count approval remains current. The graph also excludes stale approved memory from later sessions. PostgreSQL retains authoritative records and a durable projection outbox; missing or unsynchronized FalkorDB context blocks graph-dependent actions rather than falling back to invented answers. An authenticated MCP adapter exposes the narrow tools. In a frozen, same-team synthetic acceptance comparison, graph context scored 19/20 safe outcomes versus 13/20 for flat context, with one repeated-correction reasoning failure retained and disclosed.

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
- Deployment: https://clearencexforgraphhacks.vercel.app/ — invitation-only customer workspaces. PostgreSQL, FalkorDB and the API are hosted; readiness and administrator sign-in were verified. Arrange a customer account for judges and retain the complete local Docker setup. See `Docs/HOSTING_STATUS.md` for free-tier limits and verification scope.
- Registration, team, reuse eligibility and data/asset rights: **team verification required**.

This prepared text is not a completed official submission. Check the live form's field limits and required links.
