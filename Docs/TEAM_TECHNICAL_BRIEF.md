# Explain and review the implementation

This brief supports participant review; it is not a claim that the team has already reviewed or understood the code. Codex assisted with implementation and verification.

## Product claim

ClearanceX connects a review decision to its supporting shipping-document assertion. When the supporting document is replaced, a real FalkorDB traversal identifies what needs review again. A model may investigate and propose a task; it cannot approve or file a declaration.

## Data responsibilities

PostgreSQL owns users, tenant membership, sessions, immutable source history, decisions, tasks, runs, usage, exports, batches and the graph outbox. PDFs reside on a private volume. FalkorDB owns operational context snapshots used by the new tools. There is no successful SQL/NetworkX fallback for the graph tools.

The same tenant can hold multiple dossiers. Each tenant's graph name is selected by authenticated server code, not by a model argument. Every query also scopes shipment and revision. A `shipment:revision:node` key keeps versions separate. The worker publishes a graph revision only after the snapshot completes; readers refuse pending or missing snapshots.

## Essential graph path

`Decision -> DEPENDS_ON -> Assertion -> DEPENDS_ON -> Document` connects an approval to its source. `Memory -> DEPENDS_ON -> Decision` and `ExportSnapshot -> DEPENDS_ON -> Decision` extend its consequences. The change query follows bounded reverse dependencies before replacement commits. Tests prove that removing a relevant edge removes its decision from impact, and an unrelated approval stays current.

Agent runs are projected with retrieved assertions, recalled memory and proposed tasks. A saved source/decision is historical evidence; it is not automatically current truth.

## Security decisions

Opaque sessions fit a browser and one backend: the cookie is random, the database stores a digest, and logout or expiry revokes access. Passwords use Argon2id. CSRF checks require a token and exact allowed origin. Session CSRF values are stable across tabs/MCP clients and rotate with the session. JWT is a documented external-client option rather than a second unfinished authentication mechanism.

The backend rechecks membership, role, dossier ownership and source revision at action boundaries. Documents are private routes, not public static files. Uploaded files use generated names, byte/page limits and bounded parser/extraction processes. This does not establish production-grade hostile-file isolation or official customs compliance.

## Agent boundaries and costs

The configured inexpensive model is `gpt-4.1-mini-2025-04-14`. The runtime provides six typed tools, a six-tool maximum, small contexts, bounded output, a time cap, and no automatic model escalation/provider retry. Final citation IDs are constrained by the actually retrieved IDs and checked again; numeric claims are checked against cited values. One bounded final-format/grounding repair is allowed and billed through the same reservations. These checks reduce errors; they do not prove every natural-language statement true.

PostgreSQL reserves estimated cost before each request and reconciles reported usage. Unknown outcomes retain a conservative reservation/charge. The current local app ceiling is $0.25; the user's total account credit is separate and can also be used by other applications.

## Extraction and export limits

The default parser reads actual digital PDF text across pages, supports explicit field labels and a defined pipe-delimited goods format, and keeps page identity. Synthetic demo extraction is separately labeled precomputed. Scanned PaddleOCR, arbitrary table layouts and calibrated confidence are not established.

Human-entered goods arithmetic uses decimal rounding. Readiness and source revision gate XML preparation. Versioned export records and batch manifests identify prepared/blocked dossiers. The XML template has not been validated by an authorized customs acceptance process. Downloaded files cannot be remotely revoked.

## Review questions the team should answer

1. Show one actual Cypher query and explain every scope/filter/limit.
2. What fails when FalkorDB is down or its latest snapshot is missing?
3. Why does replacing the packing list invalidate weight but preserve invoice package count?
4. How do duplicate requests and simultaneous approvals avoid overwriting a decision?
5. How is stale memory excluded, and what is still missing from cross-shipment memory?
6. Which result used real OpenAI calls, which used a scripted provider, and which used precomputed extraction?
7. What did the initial failed evaluations expose, and how did the implementation change?
8. Why are public uploads, tariffs, multi-agent handoffs and official customs acceptance still limited?
9. How do RDB snapshots, the PostgreSQL outbox and restart reconstruction work together?
10. What work existed before the event, and what work was done during it?
