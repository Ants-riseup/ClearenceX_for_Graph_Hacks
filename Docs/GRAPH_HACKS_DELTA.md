# Existing project and Graph Hacks implementation record

This is an existing ClearanceX project extended during this session. No earlier work is represented as newly authored and no Git history has been rewritten. The working tree contained untracked application directories at the start; their presence is not proof of event eligibility. The team must clarify reuse eligibility with the organizers and publish accurate commit history.

## Existing components retained

- React review, dossier, graph, discrepancy, audit and export screens.
- FastAPI shipment routes and PostgreSQL dossier/extraction/metadata/goods models.
- Local OCR/classification/entity extraction, normalization, source/canonical resolution, deterministic discrepancy explanations and template XML preparation.

## New implementation in this session

- `backend/context_app`: opaque authentication/CSRF, tenant authorization, versioned state, durable graph outbox, FalkorDB projection and parameterized queries, source-change dependency traversal, human review tasks/decisions, graph memory, protected PDFs, honest bounded uploads, OpenAI agent tools/usage ledger and optional MCP adapter.
- Context Agent UI, real sign-in/session guard, logout, PDF citations, precise validity states, repaired upload polling and removal of blanket upload fallback.
- Integration/agent contract tests, isolated test services, local setup/admin commands, Compose application, corrected root commands/README and supporting documents.

## Known future work retained from the plan

Broader company knowledge, multiple cooperating agents, full conversation-history management, JWT/external clients, MFA, calibrated extraction, full multipage goods extraction, scalable pagination/indexing/retention, hardened public uploads, managed production deployment, official customs validation and a final demo video remain separate deliverables. They are not claimed implemented merely because the plan recommends them.

OpenAI is allowed and potentially billable. This implementation defaults to local infrastructure with live inference disabled until explicit configuration. It creates no paid hosting subscriptions and submits nothing to the event.

Codex assisted with implementation and tests. The team must review the code, replace placeholders in final submission metadata, verify its rights to data/assets and explain the architecture and essential queries. The earlier root README is preserved as `Docs/LEGACY_ROOT_README.md` because it described a different Ants app.
