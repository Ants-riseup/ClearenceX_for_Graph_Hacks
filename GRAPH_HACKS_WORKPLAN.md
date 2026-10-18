# ClearanceX — Graph Hacks implementation work plan

**Competition release update — 18 October 2026:** A rewritten Track 01 README, judge/submission/demo materials, cross-platform setup, automated verification workflow and frozen post-development evaluation are prepared. Fresh tests: **79 backend passed/1 skipped; 29 UI passed**. Actual first comparison: **19/20 graph versus 13/20 flat**, $0.0455048 estimated, with the failure retained. See [release readiness](Docs/RELEASE_READINESS.md). Public publication, human recording/visual acceptance, eligibility and final submission remain open; guideline recommendations below are retained.

**Current web/password update — 18 October 2026:** Admin-created customer accounts now sign in with temporary credentials and must choose their own password before entering the shipment product. Admin confirmation/filtering, graph dependency preview, keyboard navigation and route loading are improved. **78 backend tests passed, 1 skipped; 28 frontend tests passed; 38 live customer checks and 13 graph/product checks passed.** See [the current implementation report](Docs/WEB_POLISH_REPORT.md). The original Overview and recommended competition features are retained. Earlier validation counts below describe previous stages; broad roadmap/submission gates remain open.



**Latest local validation — 18 October 2026:** All nine reported runtime bugs are fixed within the tested four-PDF workflow. The running app passes upload, graph-backed review and per-item XML preparation; 62 selected tests pass with one skipped. See [the verification and working test output](Docs/NINE_FIXES_VERIFICATION.md). The original Overview design is retained. Broader roadmap and submission requirements remain as documented below.

**Prepared:** 17 October 2026, Asia/Colombo
**Revised:** 17 October 2026 — stronger competition focus, guideline coverage preserved, and a balanced free/paid stack with OpenAI allowed
**Project:** ClearanceX, Team Ants
**Purpose:** Turn the existing document-reconciliation prototype into a FalkorDB-backed AI agent submission.
**Status:** Expanded local competition build implemented. Actual OpenAI investigations, graph-driven re-review, MCP transport, digital-PDF extraction, automated tests and private backup/restore have been exercised. The entire roadmap is **not yet fully complete**: browser verification is blocked by a saved policy, submission assets/external eligibility remain, and later production features retain their planned scope. See the completion report for the current evidence; original baseline findings below describe the project before these changes.

**Completion audit:** [Detailed phase, APP-01–18 and guideline coverage report](Docs/GRAPH_HACKS_COMPLETION_REPORT.md). The entire plan is **not complete**; several P0 acceptance gates and later product features remain open.

## Implementation status — 17 October 2026

| Area | Delivered implementation | Validation / remaining work |
|---|---|---|
| Operational graph | Real tenant-scoped FalkorDB snapshots, parameterized Cypher, durable PostgreSQL outbox, revision checks, graph outage blocking | Real database integration tests pass; large-scale graph retention/load remains future work. |
| Evidence and change impact | Protected synthetic PDFs, source assertions, pending human review, dependency traversal, selective stale approval and memory invalidation | Source correction invalidates the dependent weight approval and preserves the unrelated package decision in tests. Synthetic extraction is explicitly precomputed. |
| Agent actions | Actual OpenAI tool selection, six tools, per-run citation enums, numeric checks, one bounded final repair, persisted proposals and shared usage reservations | Live initial and corrected-source investigations passed through the packaged API; model is `gpt-4.1-mini-2025-04-14`, with a $0.25 configured app ceiling. |
| Memory and coordination | Persistent approved memory, current/stale states, reviewer approval, per-user drafts and six-tool stdio MCP | A real MCP client read evidence, proposed a task and was denied after logout. Multi-agent handoff and cross-shipment lessons remain future work. |
| Security | Argon2id, revocable opaque sessions, CSRF/origin checks, tenant/role checks, private PDFs, bounded uploads, credential-isolated OCR subprocess | Security integration tests pass. JWT remains the documented external-client option. Public hostile-file isolation, HTTPS, MFA and production hardening remain future work. |
| Existing app | Real sign-in, Context Agent, search/filter/sort/pagination, resumable upload monitoring, drafts, reference/type/replacement controls, versioned settings, operations and real batch preparation | Production builds and automated API checks pass. Visual checks are blocked by the browser policy; some legacy warnings and later UX work remain. |
| Extraction | Actual digital-PDF text extraction across pages, explicit pipe-delimited goods rows, private bounded parser processes, transactional completion, warnings and preserved source locations | Real digital PDF and multipage/table-format tests pass. Scanned PaddleOCR and arbitrary table layouts are not validated; unsupported evidence remains review-needed. |
| Competition evidence | Demo instructions, implementation delta, schema and validation record | Labeled live comparisons are recorded. Organizer reuse eligibility, team review, video and final submission remain team deliverables. No prize or eligibility is guaranteed. |

**Validation:** Final selected suite: **48 passed, 1 skipped**; follow-up regressions also pass; a Windows-only real-stdio test is skipped and replaced by a passing packaged Linux MCP smoke. Three live comparison rounds are preserved; the final graph run passed 12/12 specified checks and the flat baseline 10/12 on six synthetic dossiers. A separate 100-call warm graph benchmark is recorded. Paid OpenAI calls have now been made with user authorization; no public deployment or event submission has been performed. See [validation record](Docs/EVALUATION.md), [setup](Docs/LOCAL_SETUP.md), [demo](Docs/DEMO.md), and [existing-project delta](Docs/GRAPH_HACKS_DELTA.md) for exact results, cost and limitations.

**Implementation map:** `backend/context_app/` contains authentication, graph projection, queries, decisions, memory, agent, budget, uploads and MCP; `frontend/src/components/screens/ScreenContextAgent.tsx` provides the review flow; `backend/tests/` holds integration contracts; `compose.yaml` packages the local app. PostgreSQL remains the authoritative record; graph-dependent actions require the matching FalkorDB revision.

**Quick navigation:** [Competition strategy](#1a-competition-strategy-and-proof) · [Balanced stack and costs](#1b-balanced-stack-free-options-and-controlled-spending) · [Guideline coverage](#preserve-the-competition-recommended-features) · [Current app findings](#3-what-the-project-currently-does) · [Existing app improvements](#4a-improvement-plan-for-the-existing-clearancex-app) · [Graph architecture](#5-target-architecture-and-data-ownership) · [Agent tools](#7-cypher-and-agent-tools) · [Security and tokens](#8-security-design-opaque-sessions-and-jwt-alternative) · [Deadline sprint](#12-deadline-sprint-1718-october) · [Verification](#15-verification-plan-and-definition-of-success) · [Submission](#16-demo-story-and-submission-package)

## 1. Recommended direction

Build **ClearanceX Context Agent**, an evidence-based shipping-document review assistant that can identify when earlier decisions are no longer supported. It should investigate a dossier through FalkorDB, cite conflicting sources, propose a review task, and trace the effect of a corrected document on earlier approvals and export readiness.

Keep the existing React interface, FastAPI backend, OCR/extraction pipeline, and PostgreSQL records. Introduce FalkorDB as the operational context store that the new agent must query to investigate and act. Preserve original assertions even after a reviewer chooses a value.

**Primary target:** Track 01, Agents That Act on Connected Data. Add Track 02, Agent Memory and Coordination, only if persistent memory and its update behavior are demonstrated and tested. Do not expand into Company Brain during the deadline sprint. These are project recommendations based on the [official track descriptions](https://www.wemakedevs.org/hackathons/falkordb).

**Security decision:** Use opaque browser sessions for the initial release. Document a short-lived JWT access-token option for future external clients; implementing both systems during the sprint is unnecessary.

**Essential demonstration:** Ask “Why is this shipment blocked?”; inspect the graph-grounded answer and approve a source-backed value. Then replace the supporting document with a corrected synthetic version. The graph identifies dependent decisions, the server marks the prior approval stale, and the agent opens a justified re-review task. A new session recalls the history without treating the stale approval as current truth.

## 1A. Competition strategy and proof

The objective is to maximize the quality and credibility of the submission. No plan can guarantee a prize. The reviewed event pages do not publish numeric judging weights; the priorities below are this team's strategy, not an invented official scoring rubric.

**Proposed positioning:** “ClearanceX tracks the evidence behind a shipping decision—and tells you when a changed document means that decision needs review again.”

### Why this is a stronger entry

The existing comparison engine can already detect mismatched numbers. The new contribution should be **decision dependency tracking through changing evidence**, supported by a real agent action. A graph can connect a document revision to assertions, a human decision, remembered context and an export snapshot. Traversing those relationships is useful product behavior that can be demonstrated clearly.

| Competitive claim | Evidence judges should see | Failure that would weaken the claim |
|---|---|---|
| FalkorDB determines the agent's context | Saved Cypher, returned evidence IDs, dependency traversal and visible affected decisions. | Graph is only a visualization or a service-health gate. |
| The agent acts on connected evidence | Configured OpenAI or validated local model selects typed tools and creates a persisted re-review task from retrieved dependencies. | A fixed canned explanation or prewritten tool trace. |
| Source changes alter decisions safely | Corrected PDF revision makes the old approval/export snapshot stale; unrelated approvals remain valid. | All decisions are cleared indiscriminately or old memory is still treated as approved. |
| Explanations can be checked | Every material value links to an actual assertion and page; one-click trace from decision to source. | Unverifiable confidence percentages and unsupported claims. |
| Cost and setup are transparent | Fresh local setup, exact model/provider, measured API usage and documented optional local fallback. | Hidden paid dependencies, expiring trial reliance or missing key/setup instructions. |
| The team understands its contribution | Short model/schema explanation, before/after event-work record and honest tests. | Large generated feature list that the team cannot demonstrate. |

### Keep the submission small and memorable

- **Hero workflow:** one shipment, three synthetic PDFs, one weight conflict, one correction, one affected approval and one unaffected comparison case.
- **Required proof:** real agent tool selection, real graph traversal, persisted proposed action, source citation and correct invalidation after a source revision.
- **Security proof:** real login/session revocation and one denied cross-tenant source request; keep this brief in the main video.
- **Track choice:** Track 01 first. Treat Track 02 as earned only after memory is shown to persist, update and exclude stale context. More tracks do not automatically improve an entry.
- **Defer:** full tariff directory, real customs transmission, a polished batch-filing module, vector search, a new agent framework and multi-agent orchestration. Hosting is optional and should not displace the core demo.

### Internal readiness gates

1. **Eligible and honest:** reused/new work and registration are documented; no unsupported claim that reuse is accepted.
2. **Feasible and cost-aware:** the selected OpenAI model or local alternative can finish a real typed-tool call, with access and usage limits understood.
3. **Graph provides evidence:** removing a relevant dependency edge changes the expected affected-decision result in an isolated test; changing an unrelated edge does not.
4. **Complete user outcome:** investigation -> evidence -> review -> corrected source -> stale approval -> re-review works repeatedly.
5. **Submission can be evaluated:** clean local setup, short video, queries, test result card and limits are available.

Finish these gates before adding decorative features. Removing FalkorDB and returning an error demonstrates dependency, but is not by itself evidence that the graph improves the result.

## 1B. Balanced stack, free options and controlled spending

**Latest user preference:** use a mixture of free and paid services; OpenAI API calls are explicitly acceptable. Prefer free infrastructure where it works, pay selectively where it improves the submission, and preserve the competition-recommended features. This supersedes the earlier all-local/no-paid interpretation. No service was purchased, account changed or billable API called while revising this document.

**Recommended default:** existing React/FastAPI app + self-hosted FalkorDB/PostgreSQL + local OCR/storage/authentication + OpenAI for the agent and selected difficult extraction. This keeps paid usage focused on model capability instead of paying separately for every layer.

### Component decisions

| Need | Recommended choice | Cost treatment and upgrade gate |
|---|---|---|
| UI/API | Existing React/Vite and FastAPI, served locally through nginx. | Free local software; hosting is optional. Keep the established stack. |
| Required graph database | Self-hosted FalkorDB and official Python client, with persistent volumes. | No managed-service fee for the local plan. FalkorDB Cloud remains an optional managed alternative if it saves setup time and its current plan fits the team's budget. |
| Transactional storage | Local PostgreSQL. | Free local option. Managed PostgreSQL is optional only if hosting is selected; do not pay for a second service unnecessarily. |
| Primary agent model | OpenAI API with a supported tool-calling/structured-output model. | Usage-based and explicitly allowed. Choose the least expensive accessible model that passes the task evaluation; stronger-model escalation is explicit and capped. |
| OCR | Existing local PaddleOCR and Poppler. | Keep routine extraction local. Use OpenAI vision only for ambiguous/missing fields when its measured benefit justifies the calls. |
| Normalization and rules | Deterministic parsing, unit conversions and comparison policies first. | Free local work; use bounded model assistance for unresolved semantic cases, not arithmetic or authority decisions. |
| Search and graph context | Parameterized Cypher and bounded traversals. | No separate hosted vector database required. Optional embeddings can be local or OpenAI, with evaluation and a separate usage budget. |
| Authentication | Local opaque sessions, Argon2id and PostgreSQL memberships. | No paid auth provider required. JWT/MFA remain in the roadmap; a managed identity service is optional for a later real need. |
| File storage | Private local volume and authorized downloads. | Free local option; optional object storage only when deployed and justified by access/backup needs. |
| MCP and coordination | Local MCP adapter and persisted graph task state. | Open tools can meet the guideline features without an agent SaaS subscription. |
| Testing and observability | Local tests, structured logs and run/evaluation tables. | Free baseline. Buy observability only for an actual operational need after the event. |
| Submission hosting | Complete local setup + video first; secure deployment if time/resources permit. | A small paid host is allowed if it materially improves access and has an agreed ceiling. Do not make hosting a blocker. |
| Local model fallback | Optional Ollama with a tested quantized model. | No per-token service bill, but requires existing hardware/time. Not a mandatory migration before the demo. |

“Free local” does not mean zero electricity, internet, storage or hardware cost. Docker Desktop is free for qualifying personal/educational and other eligible use, not every organization; use an appropriate tested local runtime if the team's circumstances differ. [Docker Desktop terms](https://docs.docker.com/subscription-billing/desktop-license/). Record licenses for pinned components, including [FalkorDB](https://github.com/FalkorDB/FalkorDB/blob/master/LICENSE.txt); do not describe the entire stack as uniformly permissively licensed.

### OpenAI implementation and model-selection plan

1. Keep the established Python integration and introduce an explicit provider/capability adapter for the new agent. Avoid a large framework migration solely to change providers.
2. Select and record `OPENAI_AGENT_MODEL` after a small test of tool calling, argument validation, tool-result handling, citations and abstention. Check current account access, model support and pricing. The existing `gpt-4o-mini` default is marked deprecated in the reviewed official model page, so do not assume that old default is the right new release target. [Existing-model status](https://developers.openai.com/api/docs/models/gpt-4o-mini).
3. Use model-proposed function calls, execute authorized graph tools in FastAPI, return their results to the model and validate its final structured response. The model never receives direct database credentials. [Official function-calling guide](https://developers.openai.com/api/docs/guides/function-calling).
4. Use supported strict schemas for tool arguments/output, with application validation and citation checks. Structured formatting does not prove that the underlying claims are true. [Structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs).
5. Retain the existing working API style where supported; add the new bounded agent loop through a tested SDK version. Test capability compatibility rather than assuming every model supports the current `beta.chat.completions.parse` code unchanged.
6. Keep vision and embeddings as separate explicitly configured capabilities. A text model/local endpoint is not automatically a vision or embedding substitute.
7. Run ten short synthetic cases before UI polish: valid tool call, valid arguments, tool-result use, correct citations, missing-field abstention, hostile document text, malformed output, timeout, repeated-tool limit and denied approval. Record real results, not a claim that the model is reliable because chat works.

### Spending controls

OpenAI is the intentional potentially billable exception in an otherwise mostly free baseline. No maximum spend has been provided by the user, so this document does not invent spending authorization or a budget amount. Before executing a deployment or a large evaluation run, configure a team-selected total ceiling and estimate its cost.

- Use one explicit provider/model configuration for the recorded demo. Do not silently switch to a more expensive model or unrelated provider.
- Set a maximum of six tools, at most one malformed-output repair, bounded retries, input context and output tokens. Count all model turns and retried requests, not just the final answer.
- Keep complete PDFs out of normal agent prompts. Retrieve a small evidence subgraph and send only necessary synthetic assertions/citations. Cache extraction by content hash within tenant scope; invalidate answer context on revision changes.
- Track estimated and reported usage per run, feature and tenant. Reserve a conservative maximum cost before dispatching concurrent calls, reconcile it afterward, and stop new work when the application ceiling is reached. Provider budget alerts alone must not be assumed to be hard cutoffs.
- Configure a separate allowance for agent inference, optional vision and optional embeddings. Do not add paid web search, hosted file search or unrelated built-in tools to a workflow already grounded in FalkorDB.
- Verify prices for the selected model/service tier on the day of implementation. A planning estimate is `sum(input_tokens × input_rate + output_tokens × output_rate) / 1,000,000`, plus applicable image/cache/tool charges. Include every request and a margin; rates and billable categories depend on the model. [Official pricing](https://developers.openai.com/api/docs/pricing).
- Keep keys backend-only and out of Git, logs, frontend bundles and model prompts. Use a dedicated project key with the least available privileges and rotate it if exposed.
- On rate limits, quota exhaustion or a reached app budget, show an explicit unavailable status and preserve deterministic evidence review. Use the optional local model only if it has passed the same tests and the switch is visible.

### Audit the existing provider paths

| Existing code | Planned change |
|---|---|
| `backend/ai_pipeline/openai_client.py` | Keep OpenAI available; make model/capabilities explicit, enforce shared usage limits, and avoid old defaults or unbounded retries. |
| `entity_extractor.py` | Keep local extraction first. Use bounded OpenAI vision for unresolved evidence; expose warnings and preserve source coordinates. |
| `table_extractor.py` | Fix or disable its inconsistent `_model` check and synthetic-row fallback. A failed paid/free model call must return missing rows or review-needed state, never plausible invented goods. |
| `reasoning/semantic_fallback.py` | Avoid repeated embedding calls for simple exact comparisons. Use deterministic matching first; only enable embeddings if evaluated and budgeted. |
| `classifier.py`, `normalizer.py` | Remove implicit extra-provider behavior. Keep deterministic paths and one deliberate configured model provider; do not let leftover Gemini keys activate unexpected calls. |
| Provider test scripts | Make network tests explicit and bounded; default unit tests use mocks. Separate mocked contract tests from live-model evidence. |
| Frontend assets and diagnostics | Prefer bundled required assets and local logs. A paid CDN/analytics service is unnecessary for the demo. |

An SDK package alone does not create charges. The executed endpoint/model and account configuration determine cost.

### Optional free/local fallback

If OpenAI access, connectivity or quota is unreliable, test Ollama with `qwen3:4b-instruct-2507-q4_K_M`; the listing specifies a 2.5 GB quantized download and Apache-2.0. Record its digest and runtime version. File size is not total RAM required, and this review did not establish the machine's RAM/GPU. [Model listing](https://ollama.com/library/qwen3:4b-instruct-2507-q4_K_M).

Start with 4,096-token context, one concurrent request and sequential OCR/inference on constrained hardware. Verify actual tool calls and schema behavior. Use an initial configurable 120-second CPU test cap, then measure and tune. Set `OLLAMA_NO_CLOUD=1` for this local profile and bind inference to loopback or a private container network; no public inference port. [Ollama FAQ](https://docs.ollama.com/faq), [tool calling](https://docs.ollama.com/capabilities/tool-calling).

Local mode must ignore cloud credentials, download models during setup and pass an external-network-disabled runtime test. OpenAI mode needs an API key and network access and must be labeled accordingly. Local mode is an option, not a condition for completing the OpenAI-backed entry. Do not call a canned replay a live local agent.

### Cost/value checkpoints

| Expense | Decision for this submission |
|---|---|
| OpenAI agent calls | Allowed; high value if they make graph-tool selection dependable. Use a small measured model budget. |
| OpenAI vision | Allowed selectively; do not redo every page when local OCR already extracted the required field. |
| Managed hosting/graph/database | Optional, not automatically forbidden. Use only if it saves material setup time or improves judge access enough to justify the known cost. |
| Paid auth, observability, workflow SaaS, vector database | Usually unnecessary for this scope; retain as future options rather than buying them now. |
| Free APIs/free-tier hosting | Optional after verifying current limits and data handling. Do not rely on expiring credits or quotas without a fallback. |

The team can submit a local app backed by OpenAI plus a working video; “local setup” does not mean inference must be offline. Document the API dependency honestly, keep the key private, and let evaluators use their own key or the validated local profile. [Submission rules](https://www.wemakedevs.org/hackathons/falkordb/rules).

## 2. Competition constraints and the existing-project question

The supplied `GRAPH HACKS Everything you need to build.txt` is an 850-line collection of FalkorDB learning resources. It covers setup, Docker, authentication, persistence, Browser, clients, Cypher, algorithms, and integrations. It is useful technical background, but it is not a complete competition rulebook. Its sample commands are reference examples, not instructions to execute against this project.

The official event runs 15–18 October 2026. Submission closes **18 October 2026, 11:59 p.m. IST**, which is also **11:59 p.m. in Sri Lanka (UTC+05:30)**. Target submission by 9:00 p.m. Sri Lanka time for a buffer. [Official schedule](https://www.wemakedevs.org/hackathons/falkordb/schedule).

The rules require FalkorDB to be central, permitted data, a public repository, setup and graph-model documentation, essential queries/algorithms, a working demo video, deployment or complete local instructions, declared tracks, and disclosure of AI coding assistance. Teams may have up to four members. Event work must be distinguishable from earlier work. [Official rules](https://www.wemakedevs.org/hackathons/falkordb/rules).

The FAQ permits reuse of general infrastructure and templates but requires a new submission and main FalkorDB implementation built during the event. This does **not** establish that an existing domain application is automatically eligible. [Existing-project FAQ](https://www.wemakedevs.org/hackathons/falkordb).

### Immediate eligibility tasks

- [ ] Confirm registration, actual team membership, and submission-form fields.
- [ ] Ask organizers whether ClearanceX's existing OCR/UI/domain code can be reused as the foundation for a new graph-agent submission. Include an honest description of the existing app and proposed new work. The team should send this question; no message has been sent as part of this planning task.
- [ ] Save the organizer response and cite it in the submission notes if relevant.
- [ ] Create an honest baseline inventory and a `docs/GRAPH_HACKS_DELTA.md` recording old components, new event work, contributors, and commit references. Do not backdate work or present earlier code as new.
- [ ] If reuse is disallowed, build a small standalone graph investigation agent using new code and newly authored synthetic fixtures. Keep the existing app as background research, not the submitted implementation.

These tasks can proceed alongside technical work. Eligibility remains unconfirmed until the organizer resolves the reuse question; this plan makes no eligibility guarantee. Older CodeSplash documents in this repository are historical context, not Graph Hacks requirements. No judging weights or official video duration were established from the reviewed event pages.

### Preserve the competition-recommended features

The user explicitly wants the guideline recommendations retained. The table keeps them in the plan with free implementation paths and delivery gates. **Mandatory rules**, **track emphasis**, and **resource examples** are different: a resource mentioning a library/algorithm does not require every library/algorithm to be implemented. The official tracks describe connected-data actions, persistent/shared memory and company knowledge. [Track descriptions](https://www.wemakedevs.org/hackathons/falkordb).

| Guideline feature | Free implementation in ClearanceX | Delivery commitment / proof |
|---|---|---|
| FalkorDB is primary and central | Self-hosted persistent graph used by investigation and change-impact tools. | P0; genuine query output and action dependency. |
| Multi-hop reasoning | Document revision -> assertion -> decision -> review task/export dependency paths. | P0; affected/unaffected decisions are correctly identified. |
| Graph queries and algorithms as tools | Cypher evidence queries and bounded dependency traversal. | P0 queries/traversal; add a documented BFS/path procedure only if it improves a tested query. Retain centrality/community algorithms as exploration, not padding. |
| Tool selection through MCP | Local MCP server exposing the existing narrow typed tools. | P1 after direct tools pass; contract parity and auth tests. MCP is preserved in the roadmap, not falsely claimed implemented. |
| Actions based on graph evidence | Pending review/re-review task with validated evidence IDs and idempotency. | P0; stored action and visible human approval boundary. |
| Explainable answers | Source citations, rule versions, graph paths and concise tool trace. | P0; every material claim can be checked. |
| Episodic memory | Persist investigation, approval and source-change events. | P0 minimal event history and session resume. |
| Semantic/procedural memory | Approved scoped facts and versioned review procedures. | P1; prove expiry/supersession before Track 02 claims. |
| Conversation history across sessions | Persist bounded user questions and validated answers linked to runs. | P1; show correct user/tenant access and redaction/retention. |
| Shared state and handoffs between agents | Later investigator/reviewer-assistant roles share graph task IDs and revisions. | P2; same permissions, explicit handoff and conflict tests; not required to add multiple models now. |
| Concurrent reads/writes | Version checks, idempotent graph projection, per-dossier ordering and concurrent approval tests. | P0 for correctness; P1 measured concurrency/load results, with no untested scale claim. |
| Separate memory per tenant/user | Trusted graph selection plus object and membership checks. | P0; two-tenant negative tests. |
| Company Brain: people, ownership, docs and decisions | Later scoped party/team/owner nodes linked to authorized sources. | P2, retained for Track 03 exploration; no new private-data imports for this event. |
| Knowledge freshness | Source revision events mark dependent approvals and memory stale. | P0 flagship demonstration. |
| Browser and graph exploration | Local FalkorDB Browser plus focused existing graph UI. | P0 developer inspection; do not expose Browser publicly. |
| Official clients, GraphRAG SDK and integrations | Official Python client now; evaluate local GraphRAG-SDK/MCP adapters after core proof. | Retain in reference/backlog. No need to duplicate existing structured extraction. |
| Docker, authentication, persistence and resource limits | Authenticated local Compose services, volumes, bounded queries and tested restart. | P0 setup and recovery evidence. |
| Full-text/vector indexes | Start with identifier/range indexes and explicit relationships; later local or budgeted OpenAI embeddings if needed. | P2 query-quality/latency test; retain the guideline feature without adding an unnecessary service. |

All three track directions remain documented. Submit only tracks whose claimed behavior is complete and demonstrable. Recommendation coverage is preserved without promising unfinished features in the entry.

## 3. What the project currently does

### Observed architecture

```text
React + TypeScript + Vite frontend
    -> FastAPI upload and shipment routes
    -> local PDF storage
    -> PaddleOCR / classification / extraction / normalization
    -> PostgreSQL dossier records and extraction JSON
    -> canonical-field and source-assertion resolution
    -> NetworkX graph + deterministic discrepancy evaluation
    -> explanations, reviewer overrides, readiness checks, XML download
```

The key domain idea is valuable: a **source assertion** is separate from a **canonical shipment field**. Multiple documents can assert different gross weights without deleting the disagreement. A proposed consensus is evidence for review, not proof of physical truth.

### Evidence-based baseline

Paths below are relative to the repository root for portability.

| Area | Source inspected | Current state and planning consequence |
|---|---|---|
| UI and navigation | `frontend/src/App.tsx`, `frontend/src/components/screens/` | Screens exist for dossiers, review, graph, discrepancies, audit and export. Reuse the relevant review flow; existence does not prove all screens are operational. |
| API client | `frontend/src/utils/api.ts` | Calls real shipment endpoints, but upload falls back to a legacy route after any error. Remove that behavior so auth or server failures cannot become misleading success. |
| Upload | `backend/api/upload_router.py` | Multiple PDF upload and background processing exist. Extension checks alone, client-supplied filenames and unbounded reads need hardening. |
| OCR and extraction | `backend/ai_pipeline/pipeline.py`, `entity_extractor.py`, related modules | OCR, classification, extraction, normalization and heuristic confidence exist. The orchestrator can return errors inside a result instead of raising. |
| Processing status | `backend/ai_pipeline/dossier_manager.py`, `backend/api/routes.py` | Manager marks returned pipeline results done without inspecting their errors; filesystem status fallback can report completion without successful extraction. |
| Data | `backend/database/models.py`, `connection.py`, `backend/schema.sql` | PostgreSQL models exist for dossiers, extractions, reviewer resolutions, metadata and goods rows. Tenant ownership, users and browser sessions are absent from the inspected models. |
| Reconciliation | `backend/reasoning/entity_resolution.py` | Canonical values retain individual source assertions; reviewer overrides exist. Preserve this behavior during migration. |
| Graph | `backend/reasoning/knowledge_builder.py` | Builds an undirected in-memory `networkx.Graph`; no persistent FalkorDB implementation was found in the inspected application code. |
| Rules | `backend/reasoning/rule_evaluator.py` | Numeric mismatch uses an absolute 0.01 threshold; string checks use semantic similarity. Documentation's 0.5% weight rule is not the same rule. Resolve this explicitly. |
| Explainability | `backend/reasoning/xai_compiler.py`, `counterfactual.py` | Existing provenance, explanation and correction-proposal code can supply structured evidence to the new agent. These are not already an autonomous tool-calling agent. |
| Authentication | `frontend/src/components/screens/ScreenAuth.tsx` | Login is explicitly simulated and accepts any credentials; PKI is also simulated. Replace or hide those claims. |
| Document access | `backend/main.py` | `/uploads` is a public static mount. Route documents through authorization before any hosted/private-data use. |
| Audit | `backend/reasoning/audit_trail.py`, API audit/discrepancy routes | In-memory events and a synthesized demo trail are used. A truncated individual event hash does not make this a durable or tamper-proof audit log. |
| Export | `backend/reasoning/cusdec_readiness.py`, `cusdec_xml.py` | Readiness checks and template-based XML serialization exist. The serializer names a user-confirmed template; the route docstring contains older contradictory wording. Official import compatibility was not verified. |
| Tests | `backend/reasoning/test_*.py`, `backend/ai_pipeline/test_*.py`, `backend/test_workflow.py` | Useful unit and mocked workflow tests exist. They were inspected, not executed for this planning task. |
| Packaging | root files, Dockerfiles, file inventory | Root README/package describe an unrelated Ants competition hub. Frontend/backend Dockerfiles exist; no Compose file was found. Most ClearanceX directories are currently untracked in Git. |

### Scope of this review

This was a static architecture and implementation review of the principal paths, plus the supplied text file and official sources. It did not start services, install dependencies, run OCR, call paid model APIs, inspect customer PDFs, validate credentials, run a security scanner, or verify deployment. Existing benchmark and presentation claims remain unverified.

## 4. Priorities and scope boundaries

| Priority | Deliverable | Why it matters |
|---|---|---|
| P0 | Honest eligibility/baseline record and correct project entrypoint | Prevent a misleading or unreproducible submission. |
| P0 | Authenticated FalkorDB instance, persisted graph, and tested Cypher tools | Establish meaningful use of the required technology. |
| P0 | One agent that investigates a conflict and proposes re-review after a source correction | Demonstrate an action driven by graph relationships, with controlled OpenAI usage or validated local inference. |
| P0 | Evidence citations, human approval and stale-context checks | Keep proposals separate from approved values. |
| P0 | Opaque sessions, authorization, private PDFs, bounded uploads | Establish the security floor for the demonstrated workflow. |
| P0 | Durable decisions and explicit failure states | Avoid fabricated completion, lost reviewer decisions and synthetic audit claims. |
| P0 | Synthetic demo, reproducible setup, tests and submission assets | Let judges verify the work. |
| P0 | Invalidate a dependent approval when its source revision is superseded | The central competitive demonstration; keep unrelated decisions unchanged. |
| P1 | Memory retrieval across later shipments and richer replay | Strengthen a Track 02 entry if the P0 path is complete. |
| P1 | Restartable OCR worker, better extraction coverage and calibration | Improve reliability after the graph-agent path works. |
| P2 | MFA, external-client JWTs, extensive multi-agent coordination, vector search | Useful later; not prerequisites for the focused submission. |

Do not add a second frontend framework, replace the established Python stack, build a general-purpose chatbot, or attempt all three tracks during the deadline sprint. GraphRAG-SDK is optional: structured extraction already exists, so direct parameterized Cypher tools are the shortest integration path. Do not claim a customs authority integration, certified compliance, live filing, or measured time savings without supporting evidence.

## 4A. Improvement plan for the existing ClearanceX app

The Graph Hacks extension should improve the application people already use. This is the full product backlog, not a commitment to finish every row before submission. **P0** means fix or safely remove/disable the issue on the demonstrated path; **P1** follows once that path is stable; **P2** is later product development. Estimates are indicative person-hours after the baseline runs, not guarantees. Work overlapping the security/graph phases is counted once. For the deadline, hide unsupported settings/screens instead of building them, and use clearly disclosed extraction fixtures if live OCR fixes would displace the graph-agent proof.

### Findings from the existing screens and pipeline

Further source inspection identified concrete improvement opportunities:

- `ScreenDossiers.tsx` polls inside an unbounded loop. A server `error` status throws inside an inner `try`, then the inner `catch` logs it and continues polling. A permanently failed dossier can therefore leave the screen waiting indefinitely. The progress percentage also increases with polling rather than completed work.
- `ScreenSettings.tsx` keeps tolerance and an auto-submit-related option in component state; its save action only displays a toast. The displayed tolerance is not connected to the backend's current comparison rule.
- `ScreenBatchFiling.tsx` uses hardcoded demonstration rows and a timer before navigation. Its current “prepared” message does not represent a persisted batch job.
- `ScreenTariffDirectory.tsx` contains static sample tariff content and toast-only synchronization/validation actions. Those controls must not imply verified regulatory updates or clearance approval.
- `useShipment.tsx` persists a selected shipment ID in sessionStorage but exposes no clear-selection action. Selection needs to be cleared/revalidated at logout, membership change and dossier deletion.
- `pipeline.py` collects extraction warnings and receives telemetry but omits them from its normal returned payload. It supplies entity fields without the OCR/bbox inputs expected by `ConfidenceScorer`, which can then overwrite confidence using defaults.
- The missing-field vision fallback in `entity_extractor.py` uses page 1. The orchestrator also renders PDF pages separately, so image conversion should be reviewed for duplication and bounded resource use.
- Deduplication currently keeps one entity for a field/value pair. Preserve additional source locations where a repeated value appears on different pages; those locations are useful evidence even when the value is identical.

These are source-level findings, not a claim that all affected runtime paths were exercised.

### Prioritized app backlog

| ID | Priority | Improvement and expected behavior | Suggested owner | Effort | Acceptance check |
|---|---|---|---|---:|---|
| APP-01 | P0 | Fix dossier polling: terminal errors stop, transient failures retry within a limit, unmount cancels requests, and timeout offers resume/retry. | Kaveen | 2–3 h | A failed upload exits loading; navigating away stops polling; resume uses the same dossier ID. |
| APP-02 | P0 | Replace misleading percentages with stages and completed-document counts. Keep extraction, review and export states separate. | Nadija + Kaveen | 2–3 h | A failed document cannot produce “100% complete”; extracted data is not labeled approved. |
| APP-03 | P0 | Remove blanket upload fallback and fake-success actions from the normal workflow. Label or hide sample-only screens. | Kaveen | 1–2 h | Server/auth failure stays a failure; no real action succeeds only by displaying a toast. |
| APP-04 | P0 | Display raw/normalized values, units, competing sources and unknown/low-quality evidence together in review. | Kaveen | 2–4 h | A reviewer can compare both sides of the demo conflict and reach the exact source page. |
| APP-05 | P0 | Preserve warnings and extraction method; stop presenting default-derived confidence as measured certainty. | Nadija | 2–3 h | Warning reaches UI; a field with missing score inputs is visibly uncalibrated/unknown. |
| APP-06 | P0 | Resolve tolerance mismatch: one versioned comparison policy per field/unit; show its version in the result. Disable unsaved settings. | Aloka + Kaveen | 2–4 h | Backend decision, displayed rule and saved configuration agree at boundary values. |
| APP-07 | P0 | Clear/revalidate active dossier on logout, tenant switch and missing/deleted ID. Use a real empty-selection screen. | Kaveen | 1–2 h | No stale dossier is displayed under another session; no automatic `demo-shipment` substitute. |
| APP-08 | P1 | Add dossier search, sorting, status filters and pagination backed by the API. | Kaveen | 3–5 h | Search/filter remains correct across pages and never mixes tenants. |
| APP-09 | P1 | Add dossier title/reference, document-type correction and replace/reprocess actions with version history. | Nadija + Kaveen | 4–6 h | Replacing a PDF preserves the old revision and invalidates dependent proposals. |
| APP-10 | P1 | Improve multipage header extraction and wire validated table extraction into the persisted contract. | Nadija | 8–14 h | A known field on page 2 and multi-page goods rows retain correct page/row citations. |
| APP-11 | P1 | Add goods-row editing, decimal arithmetic, unit/currency validation and reconciliation of totals. | Nadija + Aloka | 5–8 h | Quantity × unit price and totals follow documented rounding; incompatible units are flagged. |
| APP-12 | P1 | Add review filters, next unresolved field, keyboard navigation, draft autosave and correction history. | Kaveen | 4–6 h | Reviewer resumes a draft; prior approvals remain visible; keyboard-only review works. |
| APP-13 | P1 | Persist authorized workspace settings with validation, audit and explicit impact on recomputation. | Aloka + Kaveen | 3–5 h | Save survives reload, unauthorized edits fail, rule changes mark old results stale. |
| APP-14 | P1 | Make batch export operate on real selected dossiers with per-dossier readiness and output status. | Aloka + Kaveen | 5–8 h | One blocked dossier cannot be silently exported; results identify every success/failure. |
| APP-15 | P1 | Improve export preview with source references, missing-data blockers, template version and reviewer identity. | Aloka + Kaveen | 3–5 h | Preview and downloaded file use the same approved revision; missing fields block both. |
| APP-16 | P1 | Add practical performance work: avoid duplicate rendering, lazy-load PDF pages/graph UI, index lists, bound graph results. | Team | 4–8 h | Before/after measurements show improvement without losing citations or state. |
| APP-17 | P2 | Replace tariff samples with maintained, licensed, versioned reference data and domain review. | Domain reviewer + Aloka | Research first | Every rule has a source/effective date; no sample simulator claims official clearance. |
| APP-18 | P2 | Add operational dashboards, retention controls, user onboarding and configurable notifications. | Team | Split after discovery | Actual status/metrics shown; users control notifications; retention covers all stores. |

### Better end-to-end user journey

1. **Sign in:** enter the actual tenant workspace; show the signed-in user and role.
2. **Create dossier:** add a human-readable reference and allowed PDFs. Show limits, file names, sizes and detected duplicate content before submitting.
3. **Process:** display queued, OCR, extraction, validation and graph-sync stages with per-document errors. Let the user leave and return without losing progress.
4. **Review overview:** show missing required fields, conflicts, uncertain values and already reviewed fields. Keep “processed,” “ready for review,” and “ready to export” distinct.
5. **Resolve a field:** present side-by-side source values and source pages. Offer an agent investigation when helpful; require a reviewer reason for changing the selected value.
6. **Save review:** store a versioned decision, update readiness and show whether graph context is current. Preserve the original assertion history.
7. **Prepare export:** show exact blockers, source-linked goods rows and template preview. Download only the reviewed revision.
8. **Resume later:** reopen the dossier with its real status, saved draft and approved history. Retrieve prior decisions through the graph when an agent question requires them.

### Extraction and reconciliation quality work

**Contract improvements:** Return `warnings`, extraction telemetry, source method, source revision and explicit processing outcome. Define `success`, `partial`, `failed` and `needs_review` semantics once and use them in the worker, API and frontend. Partial extraction must not become automatic approval.

**Evidence improvements:** Keep all meaningful page locations for repeated values; standardize bbox coordinates and record page dimensions/orientation. Test mapping at multiple zoom levels. If no reliable location exists, link the document/page and say the location is unavailable.

**Confidence improvements:** Preserve original extractor confidence separately from any combined score. Pass measured OCR and bbox-match inputs when available; display missing inputs as unknown. Later calibrate against labeled data before calling the score a probability.

**Comparison improvements:** Define field-specific policies: counts as integers, weights with units and a documented tolerance, currency totals with decimal rounding, identifiers with controlled formatting normalization, and party names with role awareness. Shared policy code must drive clustering and discrepancy checks so one module does not call a pair equal while another calls it conflicting.

**Table improvements:** Keep document/page/row IDs, capture quantity/unit/price/total separately, identify continuation rows and never merge two distinct goods rows just because they share a description. Retain reviewer edits and recompute totals without overwriting source evidence.

**Cost improvements:** Reuse OCR/page renders within a document revision, call vision only for missing/ambiguous fields, cap rendered pixels and pages, and cache only within authorized tenant/version boundaries. Record per-stage duration and model usage for measurement.

### Screen completion policy

| Existing screen | Submission treatment | Later completed behavior |
|---|---|---|
| Overview | Display actual dossiers and true processing/review state. | Search, pagination, actionable filters and measured workload summary. |
| Dossiers | Repair polling/error behavior and use safe bounded upload. | Versioned replacement, reprocessing, duplicate detection and resumable jobs. |
| Review workspace | Main demo screen: source comparisons, citations and human decisions. | Efficient keyboard workflow, autosaved drafts and correction history. |
| Knowledge graph | Display the persisted FalkorDB result and selected evidence path. | Search/focus/filter large graphs with bounded loading. |
| Discrepancies | Show actual rule evaluations with field/version and review status. | Sorting by review urgency and grouped root causes, with clear reasoning. |
| Audit trail | Display real stored events; remove synthesized histories for real dossiers. | Filtered export, retention and independently reviewed integrity guarantees. |
| Settings | Disable unsupported saves; show the actual effective rule configuration. | Authorized, versioned settings with recomputation and audit. |
| Batch filing | Clearly labeled demo or hidden from the main path. | Persisted real batch jobs and readiness-controlled exports. |
| Tariff directory | Label as sample reference content or hide it; remove authoritative success claims. | Maintained references with source/effective-date and validation process. |
| ASYCUDA gateway | Readiness and template export preparation only. | Compatibility verified through an authorized test process before broader claims. |

### Improvement delivery order

- **Deadline sprint:** APP-01–07 on the demonstrated path, combined with the authentication/private-file work already planned. They fit into phases 2, 3, 6 and 7; reduce other scope if they threaten the deadline.
- **First post-event iteration:** APP-08–09 and APP-12–13 for reliable daily review, plus APP-16 measurements to choose the most valuable performance fixes.
- **Second iteration:** APP-10–11 and APP-14–15 for better extraction, line items and real batch preparation.
- **Later:** APP-17–18 after data access, licensing, domain expertise and operational needs are established.

Track improvements using failed-job recovery rate, field-level extraction accuracy, missing-evidence rate, time to resolve a known conflict, number of unsaved/lost decisions, and p95 screen/API latency. Establish a baseline first. Do not claim fewer customs rejections from an app-only test.

## 5. Target architecture and data ownership

```mermaid
flowchart TD
    U[Reviewer] --> UI[Existing React review workspace]
    UI --> API[FastAPI: session and authorization checks]
    API --> PG[(PostgreSQL: identity, source records, approvals, outbox)]
    API --> FILES[Private PDF storage]
    FILES --> OCR[Existing extraction and normalization]
    OCR --> PG
    PG --> SYNC[Idempotent graph projection worker]
    SYNC --> F[(FalkorDB: evidence relationships and agent memory)]
    API --> AGENT[Bounded investigation agent]
    AGENT --> MODEL[OpenAI model or optional local model]
    MODEL --> TOOLS[Typed tools with scope and permission checks]
    TOOLS --> F
    TOOLS --> RULES[Deterministic rule evaluation]
    TOOLS --> PROPOSALS[Persist proposed review task]
    PROPOSALS --> PG
    AGENT --> ANSWER[Answer with evidence paths and action proposal]
    ANSWER --> UI
    UI --> APPROVE[Human approval endpoint]
    APPROVE --> PG
```

### Store responsibilities

- **PostgreSQL:** users, memberships, sessions, dossier metadata, immutable extraction revisions, authoritative approvals, task status, audit events and a graph-update outbox.
- **Private file storage:** original PDFs, content hashes, retention metadata; no public directory listing or unauthenticated document URL.
- **FalkorDB:** searchable relationships between shipments, documents, assertions, fields, rule evaluations, approved decisions and agent runs. It is the agent's required context store.
- **NetworkX:** retain as a reference/test helper, or adapt a graph-derived subgraph for existing rule code. It must not silently replace FalkorDB in the new agent workflow.

PostgreSQL remaining the transactional source does not prevent FalkorDB being the primary graph database. The new investigation, context retrieval and memory features must actually depend on persisted FalkorDB relationships. With FalkorDB unavailable, those operations return a clear unavailable state; they must not rerun the old SQL/NetworkX path and claim graph-backed success.

### Synchronization and freshness

1. Save extraction or approval changes and an outbox event in one PostgreSQL transaction.
2. Project an event into FalkorDB using stable IDs and idempotent writes. Record the event/version applied.
3. Acknowledge the outbox only after the graph update succeeds. Retry failures with bounded backoff; persist an actionable failure after the retry limit.
4. Track `source_revision` and `graph_revision` per dossier. Build multi-step projections under a new revision and expose it only when complete.
5. An investigation requires a complete graph revision matching the source revision. If the graph lags, report `context_pending` and retry later; do not answer from an incomplete projection.
6. Bind each review proposal to the dossier revision and evidence IDs. Approval rechecks both under a transaction/lock; stale proposals return a conflict and require investigation again.
7. Rebuild a tenant graph from source records and approved events when needed. Verify counts and selected relationships before marking the rebuilt projection ready.

**Source-change transaction:** retain the earlier document revision and its assertions. On correction/withdrawal, first block new exports and approvals until synchronization completes. The worker queries the prior complete graph for dependencies on that revision, records exactly the affected decisions as `validity_state=stale` in PostgreSQL, and projects those changes. Historical approval status/actor/time remain intact. Active memory derived from stale decisions is withdrawn. Only after the new complete projection is ready can the agent investigate and propose re-review. Idempotent event IDs prevent repeated invalidation or duplicate tasks. If traversal fails or exceeds its result budget, keep the dossier pending; never assume an empty impact set.

For the sprint, one small polling worker and a PostgreSQL outbox are enough. A new queue service is unnecessary. Worker restart/retry and duplicate delivery still need a test.

## 6. Graph schema

Use one graph per tenant as the initial isolation strategy. The backend obtains its graph name from authenticated membership and a trusted server mapping. Neither the browser nor the LLM may supply an arbitrary graph name. Separate graph names alone are not an authorization system: enforce access in every tool and use scoped database credentials where the selected FalkorDB version supports them.

### Nodes

| Label | Required properties | Purpose |
|---|---|---|
| `Shipment` | `id`, `tenant_id`, `source_revision`, `graph_revision`, `status` | Root for each dossier investigation. |
| `Document` | `id`, `shipment_id`, `type`, `content_hash`, `revision` | Source identity without embedding file bytes or private storage paths. |
| `Assertion` | `id`, `field_type`, `raw_value`, typed normalized value, `unit`, `page`, bbox coordinates, `extraction_version` | Preserve what a source actually says. |
| `CanonicalField` | `id`, `field_type`, `proposed_value`, `approved_value`, `status`, `revision` | Separate computed consensus from reviewed outcome. |
| `Rule` | `id`, `version`, `comparison`, `tolerance`, `unit`, `authority_status` | Versioned prototype checks; do not label local assumptions as customs law. |
| `RuleEvaluation` | `id`, `revision`, `result`, `delta`, `evaluated_at` | Persist how a particular rule applied to evidence. |
| `ReviewTask` | `id`, `status`, `field_id`, `expected_revision`, `reason` | An agent-proposed action with a review lifecycle. |
| `Decision` | `id`, `shipment_id`, `status`, `validity_state`, `value`, `reason`, `actor_id`, `decided_at`, `revision` | Historical human approval/rejection plus separately tracked current/stale validity. |
| `ExportSnapshot` | `id`, `shipment_id`, `revision`, `status`, `created_at` | Optional prepared-file snapshot; block regeneration/use when its evidence dependencies are stale. |
| `AgentRun` | `id`, `actor_id`, `status`, `model`, `prompt_version`, `graph_revision`, `started_at` | Trace graph tools and outcomes for a bounded investigation. |
| `Memory` | `id`, `kind`, `summary`, `scope`, `status`, `created_at`, `expires_at` | Curated reusable context, initially approved decisions only. |

Optional later nodes: `Party`, `LineItem`, `Container` and an explicitly reviewed `Procedure`. Avoid name-only entity merges. Verify stable identifiers and role before linking parties across shipments.

### Relationships

```text
(Shipment)-[:HAS_DOCUMENT]->(Document)
(Shipment)-[:HAS_FIELD]->(CanonicalField)
(Document)-[:CONTAINS]->(Assertion)
(Assertion)-[:ASSERTS_VALUE_FOR]->(CanonicalField)
(RuleEvaluation)-[:EVALUATES]->(CanonicalField)
(RuleEvaluation)-[:USES_RULE]->(Rule)
(RuleEvaluation)-[:SUPPORTED_BY]->(Assertion)
(AgentRun)-[:INVESTIGATES]->(Shipment)
(AgentRun)-[:PROPOSED]->(ReviewTask)
(ReviewTask)-[:ABOUT]->(CanonicalField)
(Decision)-[:RESOLVES]->(ReviewTask)
(Decision)-[:BASED_ON]->(Assertion)
(Memory)-[:DERIVED_FROM]->(Decision)
(AgentRun)-[:RECALLED]->(Memory)
(Decision)-[:SUPERSEDES]->(Decision)
(Assertion)-[:DEPENDS_ON]->(Document)
(Decision)-[:DEPENDS_ON]->(Assertion)
(ReviewTask)-[:DEPENDS_ON]->(Assertion)
(Memory)-[:DEPENDS_ON]->(Decision)
(ExportSnapshot)-[:DEPENDS_ON]->(Decision)
```

`DEPENDS_ON` consistently points from a derived artifact to its evidence. The same trusted projection creates these edges and the descriptive relationships above; they cannot be arbitrary model-written links. All actionable dependent nodes carry `shipment_id`. For the smallest demo, use Decision and Memory dependencies and the existing export-readiness gate; add `ExportSnapshot` only if a prepared file is actually generated.

### Modeling rules

- Stable IDs include the document/extraction revision so re-extraction does not overwrite earlier evidence. Existing assertion IDs based on list position need versioning before they become permanent references.
- Use directed relationships with documented meanings. Preserve the old UI node/edge response shape through an adapter.
- Flatten nested extraction structures into supported scalar/list graph properties or separate nodes. Do not assume arbitrary PostgreSQL JSONB is a valid graph property.
- Store both raw and normalized values and the normalization version. Compare compatible units and currencies only.
- Record missing, uncertain, conflicting and approved as different states. An absent field is not a matching field.
- Scope every traversal to an authorized shipment and revision, even inside a tenant graph.
- Add supported indexes for label/ID lookups. Check constraint and index syntax against the pinned server version; do not assume Neo4j feature parity.
- Serialize writes per dossier/revision or enforce an equivalent tested strategy. `MERGE` by itself is not a complete concurrent uniqueness guarantee.

## 7. Cypher and agent tools

Save production query templates as reviewable `.cypher` files. Use parameter binding, fixed labels/relationships, explicit result limits and timeouts. The examples below are proposed contracts, **not queries executed during this review**. Test syntax and behavior with the selected FalkorDB release. [FalkorDB Cypher reference](https://docs.falkordb.com/cypher/).

### Query A: evidence for one field

```cypher
MATCH (s:Shipment {id: $shipment_id})-[:HAS_FIELD]->(f:CanonicalField {id: $field_id})
MATCH (s)-[:HAS_DOCUMENT]->(d:Document)-[:CONTAINS]->(a:Assertion)-[:ASSERTS_VALUE_FOR]->(f)
WHERE s.graph_revision = $revision AND f.revision = $revision
RETURN f.id, f.status, d.id, d.type, a.id,
       a.raw_value, a.normalized_value, a.unit, a.page
ORDER BY d.id, a.id
LIMIT 50
```

The projection contract must ensure the returned document/assertion links belong to that active revision. Return full citation metadata through the tool response; fetch additional pages using a bounded cursor rather than silently discarding evidence beyond 50 rows.

### Query B: explain a failed rule through its sources

```cypher
MATCH (s:Shipment {id: $shipment_id})-[:HAS_FIELD]->(f:CanonicalField)
MATCH (e:RuleEvaluation)-[:EVALUATES]->(f)
MATCH (e)-[:USES_RULE]->(r:Rule)
MATCH (e)-[:SUPPORTED_BY]->(a:Assertion)<-[:CONTAINS]-(d:Document)<-[:HAS_DOCUMENT]-(s)
WHERE e.result = 'conflict' AND e.revision = $revision
  AND f.revision = $revision AND s.graph_revision = $revision
RETURN f.id, e.id, e.delta, r.id, r.version, d.id, a.id, a.page
LIMIT 100
```

### Query C: recall approved memory for a selected field

```cypher
MATCH (s:Shipment {id: $shipment_id})-[:HAS_FIELD]->(f:CanonicalField {id: $field_id})
MATCH (m:Memory)-[:DERIVED_FROM]->(d:Decision)-[:RESOLVES]->(t:ReviewTask)-[:ABOUT]->(f)
WHERE m.status = 'active' AND d.status = 'approved'
  AND d.validity_state = 'current'
  AND m.expires_at > $now
RETURN m.id, m.summary, d.id, d.reason, d.revision, d.decided_at
ORDER BY d.decided_at DESC
LIMIT 5
```

Same-field session memory is the MVP. Later cross-shipment memory needs explicit party/rule/scope matching and permission filtering; a similar old shipment is not permission to reuse its numbers.

### Query D: find decisions affected by a changed source

```cypher
MATCH (s:Shipment {id: $shipment_id})-[:HAS_DOCUMENT]->(source:Document {id: $source_revision_id})
MATCH (affected)-[:DEPENDS_ON*1..4]->(source)
WHERE affected.shipment_id = $shipment_id
RETURN DISTINCT affected.id, labels(affected), affected.status
ORDER BY affected.id
LIMIT 101
```

This is a proposed bounded traversal to test on the pinned FalkorDB release. Run it against the last complete dependency graph before projecting the source replacement. The 101st result is an overflow signal for a 100-result budget: refuse partial invalidation or use a tested paging/batching strategy. Filter allowed affected node types server-side. Assertions need not be returned as actionable artifacts; Decision/Memory/ReviewTask/ExportSnapshot IDs are the useful results.

**Proof fixture:** Decision A depends on assertion A1 in the corrected packing-list revision. Decision B depends only on a separate invoice field. A and its derived memory become stale; B remains current. In an isolated test copy, remove A's dependency edge and observe that the traversal no longer finds A. This exposes the graph's actual contribution; restore the fixture before other tests.

### Typed tool allowlist

| Tool | Inputs supplied by model | Server-enforced behavior |
|---|---|---|
| `list_dossier_issues` | Authorized shipment ID | Return field states and rule evaluations from current graph revision. |
| `get_field_evidence` | Shipment ID, field ID | Query A; return source IDs, values, pages, coordinates and retrieval metadata. |
| `get_rule_explanation` | Shipment ID, evaluation ID | Query B or a narrower template; return computed rule facts. |
| `recall_approved_decisions` | Shipment ID, field ID | Query C; exclude expired, superseded and unauthorized memory. |
| `get_change_impact` | Shipment ID, source revision ID | Query D; return affected artifacts and path evidence from an authorized complete graph. |
| `propose_review_task` | Field ID, evidence IDs, reason, suggested value, expected revision | Validate against retrieved evidence; persist a pending proposal idempotently. Never approve it. |
| `get_run_status` | Run ID | Return only a run visible to the caller. |

Inject tenant, actor and permissions from the session; they are not model-controlled arguments. Begin with Python tools directly invoked by the existing backend. MCP is an optional adapter after the tool contracts work, not a requirement to rewrite the application.

### Bounded agent loop

1. Authorize the user and dossier; check extraction and graph readiness.
2. Create an `AgentRun` tied to a fixed graph revision.
3. Provide the user's question and the tool schemas to the model.
4. Allow at most six tool calls, bounded model tokens/retries and a separate short graph-query timeout. Start with a configurable 60-second total investigation cap for the API profile and 120 seconds for local CPU experiments; tune from measurements. Display progress/cancel and enforce section 1B's usage limits; do not promise a response time before testing.
5. The agent selects an issue, retrieves evidence and rule results, and optionally recalls an approved decision.
6. It may create a pending review task with cited evidence. Validate all model output with strict schemas and recheck permissions at execution time.
7. Validate that every returned citation ID was retrieved for this run. Reject unsupported numerical claims or request a corrected structured response once; then fail clearly if invalid.
8. Return a concise explanation, structured action, citations, unresolved questions, and run ID. Persist tool events and finish status.
9. Require a human to approve/reject through a separate authenticated endpoint. Approval uses current evidence and may invalidate older proposals.

Persist concise evidence and action records, not hidden model chain-of-thought. When inference is unavailable or its configured budget is reached, show the deterministic evidence report with an explicit “agent unavailable” status. Never label a canned response as live inference. Provider/model switching must be deliberate, visible and budgeted; OpenAI is allowed.

## 8. Security design: opaque sessions and JWT alternative

### Decision table

| Question | Opaque server session | Short-lived JWT access token |
|---|---|---|
| What does the client hold? | A random identifier; session details stay server-side. | Signed claims; ordinary signed JWT contents are readable, not encrypted. |
| Revocation | Revoke the session record and reject the next request. | Expiry limits exposure; immediate revocation needs additional state/checks. |
| Current fit | Recommended for this browser and one FastAPI backend. | Consider when multiple services or external clients need token verification. |
| Cost | A session lookup and database availability. | Signing-key lifecycle, strict verification and a refresh/revocation design. |

Both are bearer credentials unless separately bound to a client. Neither replaces object authorization, HTTPS, safe storage or CSRF/XSS controls. Use maintained libraries rather than writing cryptography. [OWASP session guidance](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), [JWT best current practices](https://www.rfc-editor.org/rfc/rfc8725.html).

### P0 opaque-session implementation

- Add `users`, `tenants`, `memberships` and `sessions` tables. The graph must never store passwords or session tokens.
- Seed reviewer and read-only evaluator accounts through a local setup command with generated credentials. Disable public signup for the sprint; do not ship a known shared admin password.
- Use a maintained Argon2id password library and generic login failures. Rate-limit account and IP attempts; allow logout even when expensive processing is throttled.
- Generate 32 random bytes per session. Store a SHA-256 digest of the random token, user ID, timestamps, expiry and revocation state; return the original token only in the cookie. Passwords require password hashing, not this token-digest method.
- Suggested policy: 30-minute idle timeout, 8-hour absolute timeout; no long-lived “remember me” during the sprint. Rotate on login and privilege changes; revoke on logout, account disable and password change.
- Hosted cookie: `__Host-clearancex_session`, `Secure`, `HttpOnly`, `SameSite=Lax`, `Path=/`, no `Domain`. Use a clearly separate development cookie/profile for loopback HTTP; never carry that relaxation into hosted settings.
- Prefer same-origin UI/API routing through nginx with API base `/api`. Validate a session-bound CSRF token and allowed Origin on state-changing requests, including login/logout as applicable. SameSite and CORS are supplemental controls.
- Do not place credentials in localStorage, query strings, logs, graph nodes, analytics or model prompts. Return `Cache-Control: no-store` for session and sensitive dossier responses.
- Use a shared authentication dependency on protected routers. Return 401 for missing/expired authentication, 403 for denied actions, and a consistent 404 policy for inaccessible object identifiers.
- UI route guards improve experience; API checks provide security. The old legacy upload route must receive the same checks or be disabled.

The cookie/session controls follow [OWASP session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html); the expiry values above are project design defaults to validate.

### Optional P2 JWT profile

If external consumers justify JWTs, start with a maintained security library or suitable self-hosted OAuth/OIDC solution; consider paid identity only when a later requirement justifies it. Verify a fixed allowed signing algorithm, signature, issuer, audience, expiry and applicable time claims; reject unsigned tokens and token-type confusion. Pin trusted keys and support rotation. Keep document data and secrets out of claims. [RFC 8725](https://www.rfc-editor.org/rfc/rfc8725.html).

Suggested project settings: 5–10 minute access-token lifetime; opaque, hashed refresh tokens with rotation, token-family tracking and reuse detection. Browser access tokens stay in memory; refresh cookies need CSRF protection. Logout revokes refresh sessions, but existing JWT access tokens remain usable until expiry unless the API checks a revocation/session record. Document that tradeoff explicitly. Permission changes still require current server-side authorization. Do not add a custom JWT issuer merely to claim JWT support.

### Authorization matrix

All permissions are limited to current tenant membership and authorized dossiers.

| Action | Viewer | Reviewer | Tenant admin | Agent tool identity |
|---|---:|---:|---:|---:|
| Read allowed dossier/evidence | Yes | Yes | Yes | Only within initiating user's scope |
| Upload synthetic demo dossier | No | Yes | Yes | No |
| Investigate / propose review | No | Yes | Yes | Proposal only |
| Approve a value / edit declaration metadata | No | Yes | Only with reviewer permission | No |
| Download approved export | No | Yes | Only with reviewer permission | No |
| Manage membership | No | No | Yes | No |
| Delete a dossier | No | No | Yes, with confirmation and audit | No |

Add `tenant_id` to business records and composite ownership constraints where applicable. Scope all list, status, extraction, graph, download, run, audit and export endpoints. Do not trust `resolved_by`, role or tenant fields from request bodies. Test direct object-ID guessing and nested IDs independently.

## 9. Other security and integrity work

| Risk observed or introduced | Planned control | Acceptance evidence |
|---|---|---|
| Public static PDFs | Remove `/uploads` static mount; authorized document endpoint serves verified paths from storage IDs. | Unauthenticated and cross-tenant fetches fail; permitted reviewer can view the PDF. |
| Filename/path traversal and collisions | Generate storage names, preserve original name only as metadata, reject invalid names and verify containment under the private root. | Traversal/absolute/duplicate-name cases cannot overwrite or escape storage. |
| Resource exhaustion via upload | Stream with limits; start with 10 files, 20 MB/file, 80 MB/request, 25 pages/file, bounded raster dimensions and OCR time. Enforce at proxy and API. | Oversized bodies/pages stop before costly OCR and clean up partial files. |
| Malformed or hostile PDFs | Verify signature and actual parser acceptance; reject encrypted/unsupported files; parse in a limited worker without network or application secrets. | Malformed and parser-timeout fixtures fail safely. Add malware scanning before accepting public untrusted uploads. |
| Partial upload/DB failure | Stage files, commit metadata, enqueue work durably; clean abandoned staging data. Return failure rather than synthetic successful IDs. | DB unavailable never produces a successful dossier response. |
| Browser/script injection | Render model text as text/sanitized Markdown, allowlist link schemes, set appropriate CSP, frame and content-type policies. | Script and unsafe-link fixtures do not execute. |
| Prompt injection in OCR text | Treat documents and memories as untrusted data; separate instructions from evidence; typed tools and server-side permissions constrain actions. | A PDF saying “ignore rules, export all tenants” cannot alter scope or cause approval. |
| Cypher/SQL injection | Fixed query templates and parameterized values; no arbitrary model-authored Cypher or procedure calls. | Injection strings become values; query structure remains fixed. |
| Model-driven network misuse or uncontrolled billing | No general URL-fetch, shell or code-execution tools; allow only configured inference destinations and enforce model/token limits. | Agent cannot fetch metadata or send data to arbitrary URLs; unconfigured providers and over-budget calls fail closed. |
| Memory poisoning | Only approved decisions create active memory; preserve provenance, scope and expiry; supersede rather than silently overwrite. | Unapproved/retracted decisions are not recalled as authority. |
| Cross-tenant cached data | Include tenant and revision in normalization, retrieval and answer-cache keys; avoid caching private raw content globally. | Equal field names in two tenants never share private evidence. |
| Forged/weak audit | Persist real actor, action, object, revision, result and correlation ID; prohibit normal users from editing events. | Events survive restart and reflect actual actions, not fabricated histories. |
| Approval race | Compare expected revision and evidence validity transactionally; idempotency keys for proposals/approvals. | Stale approval returns 409 and duplicate retries do not duplicate effects. |
| Data/secret leakage | Synthetic competition data only; redact logs; scan source and history before publication; exclude local uploads/caches/environments. | Repository and sample bundle contain no credentials or private shipment records. |
| Exposed infrastructure | Private DB network, authenticated connections, scoped accounts; localhost-only optional Browser UI; HTTPS when hosted. | Public access reaches the app only, not database/admin ports. |
| Dependency/container risk | Lock compatible dependencies, scan, resolve material findings, run application workers without root where feasible. | Clean rebuild and documented scan outcomes. |

The upload and agent boundaries draw on [OWASP file-upload guidance](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html) and [OWASP AI-agent security guidance](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html). Limits, endpoints and tests above are ClearanceX-specific proposals, not claimed official defaults.

For later production hardening, add free local TOTP-based MFA, securely administered recovery, retention/deletion workflows, encrypted local backups, restoration drills, local inference log-retention review and independently anchored audit integrity. Email/SMS recovery is not required. A hash chain is tamper-evident only under its stated trust assumptions; it is not an immutable ledger against a privileged administrator.

## 10. API and frontend changes

### Proposed API additions

| Endpoint | Purpose / contract |
|---|---|
| `POST /api/auth/login` | Verify credentials, rotate session, set cookie. |
| `GET /api/auth/me` | Current identity, tenant and effective permissions. |
| `GET /api/auth/csrf` | Obtain the appropriate CSRF token without exposing session credentials. |
| `POST /api/auth/logout` | Revoke current session and expire cookie. |
| `GET /api/documents/{document_id}/content` | Authorize and stream a PDF with safe headers. |
| `POST /api/shipments/{id}/agent-runs` | Create bounded investigation; return run ID and initial status. |
| `GET /api/shipments/{id}/agent-runs/{run_id}` | Poll status, validated answer, citations and tool events. |
| `POST /api/shipments/{id}/review-tasks/{task_id}/decision` | Reviewer approval/rejection with expected revision, reason and idempotency key. |
| `GET /api/shipments/{id}/context-status` | Source/graph revision and synchronization state. |
| `GET /health/live`, `GET /health/ready` | Distinguish process alive from required services ready; expose no secrets. |

Keep existing routes where compatible, but apply the same authorization and revision rules to every alternative mutation path. Polling is enough for the sprint; streaming is optional.

### Proposed agent response fields

```json
{
  "run_id": "run_example",
  "status": "completed",
  "graph_revision": 3,
  "answer": "The transport document disagrees with the packing list. Review the cited source before approving a value.",
  "citations": [
    {"document_id": "doc_example", "assertion_id": "assertion_example", "page": 1}
  ],
  "proposed_action": {"type": "review_field", "task_id": "task_example"},
  "uncertainties": ["Document agreement alone cannot establish the measured weight."]
}
```

Example IDs are illustrative. A real response must include the actual relevant evidence on both sides of a conflict. Return structured bbox data only when measured; do not invent a highlight for an unsupported source location.

### UI tasks

- Replace simulated authentication and remove misleading PKI/government-authentication messages.
- Add authenticated loading, expired-session and denied-permission states.
- Add an “Investigate with context” panel to the existing review workspace, with suggested questions.
- Show concise tool activity: evidence retrieved, rule checked, memory recalled, review proposed. Do not expose credentials or private internal reasoning.
- Clicking a citation opens the authorized PDF at the cited page and highlights a valid bbox when available.
- Let users inspect the relevant graph path instead of forcing them to navigate the entire graph.
- Show pending/synced/stale graph context, pending review and approved/rejected decisions distinctly.
- Keep approval separate from the agent response; display the proposed value, source, reason and evidence revision before confirmation.
- Show honest extraction/agent failure states. Remove automatic upload fallback on every error.
- Clear tenant-specific UI state on logout or tenant switch. Verify keyboard operation and readable narrow-screen layouts.

## 11. Implementation phases and acceptance gates

Owner labels follow the existing team folders as a **suggested allocation**, not confirmed availability: **Nadija** = extraction/integration; **Aloka** = graph/reasoning; **Kaveen** = API security/UI. Share integration and testing; reduce scope if fewer people are available.

| Phase | Tasks and concrete outputs | Lead | Depends on | Acceptance gate |
|---|---|---|---|---|
| 0. Baseline and feasibility | Record existing/new work; resolve root project mismatch; check reuse eligibility; run configured model + graph capability gate. | Team | None | Correct entrypoints and a real tool call returning graph evidence; API access/cost or local resources documented. |
| 1. Runnable services | Add Compose, authenticated FalkorDB, PostgreSQL, API/UI, persistent volumes, environment template and authenticated health checks. | Aloka + Kaveen | 0 | Fresh setup reaches app; database state survives restart; graph port is not publicly exposed. |
| 2. Security foundation | Add users/membership/sessions, protected API dependencies, private PDF delivery, upload limits and CSRF. | Kaveen | 0–1 | Login/logout, role denial and two-tenant isolation tests pass. |
| 3. Correct ingestion | Fix false done states and legacy fallback; validate extraction results; preserve immutable revisions and stable source IDs. | Nadija | 1 | Known failed OCR is reported as failed; valid fixture persists with provenance. |
| 4. Graph migration | Add schema, query templates, graph repository, outbox worker, projection versioning and UI adapter. | Aloka | 1, 3 | Cypher retrieves exact evidence; repeated ingestion/retry does not duplicate facts. |
| 5. Agent and action | Implement bounded tool loop, structured results, evidence validation and pending review task creation. | Aloka + Nadija | 2, 4 | Live agent uses graph tools and persists a justified task; usage and provider are recorded. |
| 6. Review and changed evidence | Connect approval, dependency edges, corrected source, precise invalidation and re-review; resume without stale memory. | Kaveen + Aloka | 2, 5 | Changed source invalidates its dependent approval; unrelated decision survives; new session uses current context. |
| 7. Verification | Run regression/security checks, API-limit/outage tests, restart, dependency-edge ablation and graph-vs-flat comparison. Test offline runtime separately only for a shipped local-model profile. | Team | 1–6 | Evidence sheet records actual outcomes, usage, timings, hardware and known failures. |
| 8. Submission | Correct README; publish permitted source, essential Cypher, model diagram, AI disclosure, delta notes and video; verify links signed out. | Team | 7 | Submission fields complete and submitted before deadline. |

All phases are planned. Do not mark a phase complete based only on code presence.

## 12. Deadline sprint: 17–18 October

Assumption: roughly three contributors can work concurrently. The old **40–55 person-hour estimate is not reliable enough to promise**: agent integration, authentication, graph persistence and source-change handling are unverified. Treat this as a gated sprint for one complete demonstration. Re-estimate after the first 60–90 minutes, and retain the broader improvements/guideline features as a documented roadmap. OpenAI avoids making local-model installation a critical-path requirement. Check the actual local time; the blocks below do not imply all of them fit the remaining window.

| Block | Approximate elapsed duration | Deliverable |
|---|---:|---|
| A | 60–90 minutes | Configured model chooses a tool, FalkorDB query returns known evidence, usage controls and baseline/eligibility recorded. |
| B | 3–5 hours | One synthetic dossier -> graph -> real investigation -> cited answer -> persisted pending task. Auth/private-file work runs in parallel. |
| C | 3–5 hours | Human approval -> corrected source -> graph dependency traversal -> affected approval stale -> re-review task. |
| D | 2–3 hours | Minimal review UI, context resume, precise failure states and one security-denial demonstration. |
| E | 3–4 hours | Clean local setup with documented inference dependency, restart, edge ablation, source-change, budget and permission checks; fix blockers. |
| F | At least 3 hours reserved | Record real demo, finish README/results/queries, test public links and submit. |

**Checkpoint targets for 18 October (Sri Lanka time):** by noon, the complete source-change loop should run; by 3:00 p.m., tests and clean setup should be repeatable; **freeze features by 6:00 p.m.**; submit by **9:00 p.m.**; official deadline is **11:59 p.m.** If a checkpoint slips, cut optional scope immediately. Do not remove required competition artifacts or relabel unfinished features as complete.

**Dependencies that cannot be skipped:** graph projection before graph-backed agent output; authorization before exposing any data route; evidence/version validation before approval; a working demo before recording success claims.

### Cut lines

1. If FalkorDB integration is late, demonstrate one document field and one rule with a complete evidence path. Defer additional document types and vector retrieval.
2. If OCR setup is unreliable, use newly authored synthetic extraction fixtures with clear labels; still execute real ingestion into FalkorDB, real graph queries, real agent tools and real review persistence. Do not represent fixture loading as live OCR.
3. If memory quality is incomplete, submit Track 01 only and keep basic same-dossier decision persistence. Do not claim tested cross-shipment learning.
4. Use local setup plus video as the default low-cost submission. Add secure hosting only if it improves judge access enough to justify time/cost; never expose the unauthenticated prototype publicly.
5. If only one contributor is available, use the single-field local demo and cut optional UI polish, MCP, cross-shipment memory and new extraction work. Keep security and graph dependence.
6. Preserve the final three hours before the 9:00 p.m. team target for final checks, recording and submission. Avoid adding features in that window.
7. If direct Python tools work and time remains, add the local MCP adapter and contract-parity tests. Otherwise keep MCP explicitly planned; do not delete it from the guideline-coverage table or claim it is present.

## 13. File-level implementation backlog

Names in the “new” rows are proposals and do not yet exist.

| Path | Planned change |
|---|---|
| `README.md`, root `package.json`, root build configuration | Replace unrelated Ants hub setup with explicit ClearanceX entrypoints; preserve historical material separately if needed. |
| `.gitignore`, `backend/.dockerignore`, new `frontend/.dockerignore` | Exclude environments, caches, virtualenvs, uploads and generated private outputs; keep intentional synthetic fixtures. |
| New `compose.yaml` | Application, API/worker, PostgreSQL, FalkorDB, internal network and persistent data. |
| `.env.example` | Document provider/model, backend-only OpenAI key, usage limits, optional local-only profile and generated local credentials. |
| `backend/main.py` | Remove public file mount; configure protected routes, readiness and explicit modes. |
| `backend/api/routes.py`, `upload_router.py` | Authorization, request schemas, safe uploads, honest errors, common mutation checks and disabled unsafe legacy path. |
| New `backend/security/` | Password verification, session lifecycle, CSRF, membership and permission dependencies. |
| `backend/database/models.py`, new `backend/migrations/` | Identity/tenancy, revisions, tasks, run records, durable audit and outbox schema. Use migrations rather than relying on `create_all()` for upgrades. |
| `backend/ai_pipeline/dossier_manager.py`, `pipeline.py` | Validate success/error result contracts, durable status, versioned extraction and graph update events. |
| `backend/ai_pipeline/normalizer.py` | Tenant-scoped caches, normalization versions and privacy-safe logs. |
| New `backend/llm/provider.py`, optional `local_client.py`, existing `ai_pipeline/openai_client.py`, `classifier.py`, `normalizer.py`, `reasoning/semantic_fallback.py` | Explicit provider/capability interface, OpenAI tool loop, shared usage controls and optional tested local mode; remove accidental extra-provider calls. |
| New `backend/graph/client.py`, `repository.py`, `projection.py`, `queries/` | FalkorDB connection, trusted graph selection, Cypher templates, idempotent revision projection. |
| `backend/reasoning/knowledge_builder.py`, `rule_evaluator.py` | Keep reference behavior; adapt graph data to deterministic rules, version tolerances and distinguish proposed/approved fields. |
| `backend/reasoning/audit_trail.py` | Replace synthesized histories on real routes with durable actual events. |
| New `backend/agents/` and `backend/api/agent_router.py` | Typed tools, prompt, bounded runtime, schema validation, budget tracking and run endpoints. |
| New `backend/mcp_server/` | P1 local MCP wrapper over those same tools; preserve access controls and verify contract parity. |
| New `backend/api/auth_router.py`, `document_router.py` | Real sign-in/session and protected PDF access. |
| `frontend/src/utils/api.ts`, `App.tsx`, `ScreenAuth.tsx` | Session/CSRF handling, route states and removal of simulated success and blanket retry. |
| `ScreenReviewWorkspace.tsx`, `ScreenKnowledgeGraph.tsx`, `ScreenAuditTrail.tsx` | Agent panel, evidence paths, approval version, graph context status and real event display. |
| `ScreenDossiers.tsx`, `frontend/src/hooks/useShipment.tsx` | Bounded cancellable polling, explicit failure/retry and safe selection reset. |
| `ScreenSettings.tsx`, `ScreenBatchFiling.tsx`, `ScreenTariffDirectory.tsx` | Honest unsupported/demo states first; persisted settings, real batches and maintained reference content in later iterations. |
| `backend/ai_pipeline/confidence.py`, `entity_extractor.py`, `table_extractor.py` | Measured confidence inputs, multipage extraction, retained source locations and integrated goods-row contracts. |
| `frontend/src/types/index.ts` | Contracts for sessions, runs, citations, tasks and graph revisions. |
| New `backend/tests/integration/`, `backend/tests/security/` | Real database/query tests, authorization, uploads, agent constraints and restart/retry cases. |
| New `docs/GRAPH_HACKS_DELTA.md`, `docs/GRAPH_MODEL.md`, `docs/DEMO.md`, `docs/EVALUATION.md`, `docs/LOCAL_SETUP.md` | Honest event work, model/queries, repeatable offline demo, measured results, model/hardware/digest record and judge evidence map. |

Do not blindly stage the currently untracked directories. Review which files are source, allowed sample data, private uploads, environment artifacts and generated caches before publishing.

## 14. Infrastructure, setup and operational checks

### Minimum local topology

- Frontend/nginx serves the UI and proxies `/api` to FastAPI on one origin.
- API owns authentication and permission checks; a worker processes the graph outbox and, where implemented, queued OCR jobs.
- PostgreSQL and FalkorDB are reachable on the internal Compose network only. Optional developer ports bind to loopback.
- OpenAI mode allows only the configured provider endpoint and requires a backend key. Optional Ollama runs as a host service or internal container; test reachability and never publish an unauthenticated inference port. Keep local OCR/inference sequential if memory is constrained.
- Private uploads and database storage use named volumes. FalkorDB uses authenticated connections and persistence; a Browser container/profile is optional for developers.
- Choose compatible image/client versions, test them, then pin tags/digests. Do not copy `latest`, sample passwords or `allkeys-lru` blindly from the supplied guide. For persistent context use a tested non-evicting configuration and handle memory exhaustion as an explicit failure.
- Health checks must authenticate correctly. A health check alone does not restart an unhealthy running container; configure retries/restart policy and document the recovery path.
- Size query, upload, OCR and model limits; track latency, failures and tokens without logging sensitive content. Local app hosting avoids a hosting fee even when model API usage is billable.

Docker image choices, authentication and persistence options are documented in the [FalkorDB Docker guide](https://docs.falkordb.com/operations/docker). The network, memory and health-check choices above are deployment decisions to validate in this project.

### Configuration contract to add

| Variable/group | Policy |
|---|---|
| `APP_ENV`, `DEMO_MODE` | Explicit local/demo/hosted configuration; demo fixtures cannot silently replace real errors. |
| `DATABASE_URL` | Server-only; required in normal mode; do not expose in logs. |
| `FALKORDB_HOST`, `FALKORDB_PORT`, username/password or secret reference | Server-only, fail fast when required credentials are absent. |
| `FALKORDB_TLS` | Enable/verify TLS for connections across untrusted networks. |
| `SESSION_IDLE_MINUTES`, `SESSION_MAX_HOURS` | Document timeout policy and tests. |
| `ALLOWED_ORIGINS`, trusted proxy settings | Exact expected origins/hosts, no broad credentialed wildcard. |
| Upload/OCR/query/model limits | Enforce positive bounded values and expose safe defaults. |
| `LLM_PROVIDER`, `LOCAL_ONLY` | Proposed app settings; default planned provider `openai`. Optional `LOCAL_ONLY=true` selects validated local inference and blocks all hosted calls. |
| `OPENAI_API_KEY`, `OPENAI_AGENT_MODEL`, optional vision/embedding model settings | Backend-only credentials; explicit supported models and enabled capabilities. No secrets in `VITE_` variables. |
| App-level total/per-run token and spend ceilings | Proposed settings, required before large live evaluations; stop new requests at the configured ceiling and account for concurrency/retries. |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | Backend-only configured local destination and pinned/recorded model identity; never a user/model-supplied URL. |
| `OLLAMA_NO_CLOUD` | For the optional local profile, configure `1` in the actual Ollama server process and verify after restart. |
| `EMBEDDINGS_MODE`, `VISION_FALLBACK` | Proposed capability settings; deterministic/OCR-first, then optional budgeted OpenAI assistance. Missing evidence remains explicit. |
| `VITE_API_URL` | Public value; prefer `/api` with same-origin proxy. |

Planned evaluator flow: clone, prepare images/OCR weights, configure OpenAI with the evaluator's key and usage limit (or download the tested optional local model), generate local credentials, start Compose, apply migrations/seed synthetic data, sign in, run the investigation and source-change scenario. Provide separate documented modes for live OCR and precomputed synthetic extraction. Include an idempotent reset of the named demo fixture only; never reset arbitrary user data. Document exact tested commands and measured startup resources after implementation. The current repository does not yet provide this complete flow.

## 15. Verification plan and definition of success

Run existing relevant tests first to record the baseline. Separate deterministic tests from tests requiring OCR/model downloads, external credentials or running services. A mocked workflow test is not proof of end-to-end OCR or live agent behavior.

| Check | Input/action | Required result |
|---|---|---|
| Existing domain regression | Canonical resolution, role exclusion, readiness and XML fixtures | Existing intended behavior preserved or a deliberate change documented. |
| Honest processing state | Missing DB, OCR errors, unknown documents, pipeline `errors[]` | Explicit unavailable/failed/review-needed state; never false completion. |
| Graph projection | Same revision/event delivered twice | Stable counts and relationships; no duplicate decisions/tasks. |
| Evidence retrieval | Known synthetic conflict | Correct documents, assertions, values, pages and rule version returned. |
| Graph centrality | Stop FalkorDB during a new investigation | Agent cannot complete its investigation/action; UI reports graph unavailability. Ordinary login need not fail. |
| Source-change impact | Replace the source of approved Decision A; Decision B uses unrelated evidence | A and its dependent memory become stale; B remains current; agent proposes a new review task. |
| Dependency-edge ablation | In an isolated fixture graph, remove A's source-dependency edge while keeping the source facts | Impact retrieval changes as expected; report the lost affected-decision result. This tests graph value, not merely service availability. |
| Persistence | Restart API/worker/FalkorDB preserving volumes | Context and approved decision survive; new session retrieves them. |
| Live agent action | Ask why shipment is blocked | Model selects graph tools and creates a pending, evidence-supported review task. |
| Citation integrity | Unsupported/out-of-scope source IDs in model output | Output rejected or safely corrected; no fabricated source link. |
| Approval race | Change evidence after a proposal | Stale approval rejected; no value silently overwritten. |
| Memory lifecycle | Approve, resume, then supersede/expire | Recall includes valid approved context and excludes invalidated context. |
| Session security | Wrong password, expiry, logout, replay | Authentication enforced; revoked opaque token cannot be reused. |
| CSRF | Cross-origin state-changing request without valid token | Request denied even if browser sends a cookie. |
| Tenant isolation | Tenant A IDs used by tenant B across every endpoint/tool | No data or action access, including list/status/PDF/audit/export paths. |
| Upload abuse | Oversized, fake PDF, traversal name, parser timeout | Rejected/contained, bounded resource use and no abandoned public files. |
| Prompt injection | Malicious instructions in document/memory | No scope escalation, arbitrary query or autonomous approval. |
| Model outage/budget | Timeout, provider failure, tool-call limit | Run terminates with explicit status and bounded retries/cost. |
| Spending boundary | Concurrent runs approach the configured app ceiling | Reservation/usage accounting prevents new over-budget dispatch; no silent model/provider escalation. |
| Optional local profile | External network disabled after setup; cloud-key variables present | Shipped local profile completes with local inference only, or is clearly documented as unavailable/unimplemented. |
| Clean evaluator setup | Fresh environment from submitted files | Documented commands work without local untracked dependencies. |

### Evaluation dataset and metrics

Minimum deadline dataset: **six newly authored synthetic dossiers and 12 questions**, covering matching values, numeric conflict, missing field, ambiguous party role, superseded decision and hostile document text. Include the hero source-change case with one affected and one unaffected decision. Use a second tenant with similarly named fields for isolation tests. Define expected field state, required citation IDs, permitted action and abstention outcome before running each case. Expand to 20+ dossiers and 40+ questions after the event. Do not imply these small samples establish production accuracy.

Compare graph-backed retrieval with a reasonable flat-text retrieval baseline using the same model, source facts, question set and comparable context budget. Do not withhold the corrected source from the baseline or deliberately weaken its prompt. Report evidence-source recall, supported-answer rate, incorrect action count, abstention behavior, latency and tokens. Evaluate multi-hop questions separately from direct lookups; include examples where either approach fails. If graph retrieval does not outperform it, report that honestly and explain the demonstrated provenance/update benefits rather than inventing an accuracy gain.

Publish individual results and numerators/denominators, for example `correct impact decisions / expected impact decisions`, rather than only a percentage. For 12 questions report median and maximum observed latency; do not present a tiny sample as a reliable p95 benchmark. If reporting p95, run and document a separate repeat protocol (for example 100 warm graph-tool calls), including dataset size, hardware and cache state.

Proposed release targets, **not measured results**:

- 100% of returned citation IDs resolve to authorized evidence from the run.
- Zero cross-tenant disclosures or unauthorized approvals in the defined tests.
- All six demo cases produce their specified safe outcomes; an abstention is correct when evidence is missing.
- Every numeric rule fact matches a deterministic recomputation.
- All replay/restart tests preserve approved decisions and reject stale proposals.
- Aim for bounded graph-tool latency below 500 ms on the small fixture dataset; validate through the repeat protocol before claiming it. Measure end-to-end OpenAI/local investigation latency separately and set the timeout accordingly. The 60/120-second starting caps are operational limits, not achieved performance or service guarantees.

Do not use the confidence heuristic as a calibrated probability, claim 99% accuracy, claim universal customs compliance, or repeat older time-saving estimates without a measured protocol.

## 16. Demo story and submission package

Use a synthetic shipment with invoice/packing list gross weight **450 kg** and transport-document gross weight **440 kg**. A reviewer checks cited evidence and approves a selected value with a reason. Then upload a corrected packing-list revision stating **440 kg**. The graph follows the old source's dependencies, invalidates the approval that relied on it, excludes the stale decision from current memory and drives a re-review proposal. Keep an unrelated approved field to show that invalidation is precise. Do not auto-approve 440 kg just because the correction arrived. The initial conflict exceeds both the current tiny absolute threshold and a proposed 0.5% tolerance, but the final rule still needs one documented version/unit policy.

### Suggested 3–4 minute video outline

This duration is a recommendation; confirm any submission-form limit.

1. **0:00–0:20:** Show the conflict and the product promise: a changed source can make an old decision unsafe to reuse. Start in an already authenticated synthetic workspace; avoid spending the opening on login.
2. **0:20–1:10:** Ask why the shipment is blocked. Show a real model-selected graph tool, the multi-hop path, both source citations and the persisted pending task. State the model/provider and clearly label precomputed extraction if used.
3. **1:10–1:40:** Open the source and approve a value with a reason and visible evidence revision.
4. **1:40–2:30:** Introduce the corrected packing list. Show affected approval/memory turning stale, the unrelated decision remaining valid, export readiness blocking and the agent creating a re-review task.
5. **2:30–3:00:** Open a new session; demonstrate that context persists but the old approval is not reused as current evidence.
6. **3:00–3:30:** Show a compact measured-results card, API usage/cost record and one cross-tenant denial or graph-unavailable state.
7. **3:30–4:00:** Point to the setup/query/test files and state the limits: synthetic data, human approval, template export preparation, no claimed live customs filing.

Adjust these suggested timestamps to any actual submission-form limit. Show a real run; edited pauses must not imply an unmeasured response speed.

### Judge evidence map to complete before submission

The following paths/test names are planned deliverables. Fill in real commands, links and video timestamps after implementation; do not leave nonexistent artifacts in the final README.

| Claim | Repository evidence | Executable or visible proof |
|---|---|---|
| Graph drives the action | `docs/GRAPH_MODEL.md`, evidence/change-impact `.cypher` files | Known path result and persisted re-review task. |
| Changed evidence invalidates precisely | Source-change fixture and integration test | A stale, B current; video source-replacement segment. |
| Agent is real and bounded | Agent run/tool-event record, model/provider configuration | Live function call, validated arguments, six-tool cap and denied direct approval. |
| Memory stays current | Session-resume and invalidation tests | Historical approval visible; stale context excluded from active recall. |
| Access is enforced | Session/tenant/PDF security tests | One denied cross-tenant request plus logout replay denial. |
| Costs are controlled | `docs/EVALUATION.md` usage ledger and app-budget tests | Tokens/calls per run and stopped over-budget dispatch. |
| Setup is reproducible | `docs/LOCAL_SETUP.md`, tested Compose/configuration/seed commands | Fresh setup with explicit OpenAI-key dependency or validated optional local mode. |
| Guideline recommendations are retained | Coverage table in this plan and final README scope table | Every feature marked implemented, tested, or planned; no roadmap feature claimed complete. |

After the core submission is ready, optionally publish a technical write-up using the repository or an available free publishing platform. Explain the dependency query, source-change result, tradeoffs and failures. The event lists a blog side prize, but a blog must not displace the working submission. [Event overview](https://www.wemakedevs.org/hackathons/falkordb).

### Final package checklist

- [ ] Public repository contains all required application source and intentional synthetic fixtures.
- [ ] README starts with ClearanceX and the actual setup, architecture, graph model and limitations.
- [ ] Essential `.cypher` templates and their purpose are easy to find.
- [ ] Existing work versus event work is documented honestly, with relevant organizer clarification.
- [ ] Track selection matches demonstrated capabilities.
- [ ] Video shows the working graph and agent action, not only slides/UI.
- [ ] Deployment works, or local setup is complete and the working video is accessible.
- [ ] Test/evaluation report contains actual results, environment, remaining failures and fixture/live distinctions.
- [ ] Provider/model, API-key setup, observed usage and application spending controls are documented; OpenAI is not mislabeled free.
- [ ] Guideline coverage table preserves graph tools, MCP, memory, coordination, concurrency, isolation and company-knowledge directions with honest completion states.
- [ ] AI tools, third-party libraries and permitted data sources are disclosed and licensed appropriately.
- [ ] No secrets, local virtualenv, customer PDFs or private caches are published.
- [ ] Repository/video/deployment links work in a signed-out browser.
- [ ] Team submits through the official panel before the deadline and saves confirmation.

## 17. Risks and fallback decisions

| Risk | Response |
|---|---|
| Existing app reuse is not accepted | New standalone graph-agent submission; do not rebrand historical work as event work. |
| Short remaining window | One conflict type, one agent, one review action; defer extra tracks and infrastructure. |
| FalkorDB compatibility or concurrency issue | Pin a tested version; use supported query templates; serialize per-dossier writes; test replay. |
| Graph not current when asked | Block graph-dependent actions with `context_pending`; retry/rebuild visibly. |
| OCR dependency/model download failure | Clearly disclosed synthetic extraction fixtures for the graph-agent demonstration. |
| Provider rate limit or high cost | Small contexts, capped tools/tokens, app-level spending ceiling and explicit failure; optional tested local fallback, no fake live response. |
| Majority consensus is wrong | Require source review, preserve alternatives and let the system abstain. |
| Rule threshold inconsistency | Version prototype rules and align implementation, fixtures and UI; obtain domain review later. |
| XML output mistaken for official acceptance | Describe it as template-based preparation; do not claim authority validation or submit real declarations. |
| Private data in local folders | Publish new synthetic fixtures only; verify source and history before staging. |
| Current source omitted from Git | Review and add intended application files; prove clean-clone setup. |

## 18. After the event: production roadmap

These are later stages, not commitments for 18 October.

| Stage | Work | Exit condition |
|---|---|---|
| Week 1: reliability | Durable OCR jobs, retry/cancel, full migrations, backup/restore, retention/deletion propagation, service metrics. | Restart/recovery and restore drills pass on realistic workloads. |
| Week 2: extraction quality | Multipage/table integration, bbox accuracy, unit handling, confidence calibration and expanded labeled fixtures. | Published field-level metrics with failure categories and no unsupported accuracy claims. |
| Week 3: controlled memory | Scoped cross-shipment lessons, entity merge review, rule versioning, memory expiry and approval revocation propagation. | New evidence supersedes old context without contaminating other tenants. |
| Week 4: security and integration | MFA/recovery, external identity integration if needed, independent security review, supported export-schema validation and operator usability testing. | Security findings resolved and export compatibility demonstrated against an authorized test process. |

Only add JWT clients, multiple cooperating agents, semantic/vector search or company-wide knowledge when a demonstrated use case justifies their complexity. Human-reviewed declaration preparation remains the product boundary until a separately authorized integration is validated.

## 19. First work session checklist

1. Confirm the event account, eligibility question and deadline in the team calendar.
2. Preserve an honest baseline and separate the old app from new Graph Hacks work in documentation.
3. Agree on the schema, current-revision contract, opaque-session decision and six demo cases.
4. Start an authenticated persistent FalkorDB instance and prove a bounded OpenAI tool call (or a validated local alternative) before UI expansion.
5. Load one synthetic shipment and prove Query A and Query B return exact source assertions.
6. Implement authorization/private PDFs and remove false-success fallback paths.
7. Connect one live tool-calling agent to graph retrieval and pending review-task creation, with recorded usage and explicit model configuration.
8. Add approval, corrected-source dependency traversal, precise invalidation and re-review; then verify persistent recall, failure states and the reproducible demo.

## 20. Reference material

Read for this plan:

- User-supplied `C:\Users\KM Computers\OneDrive\Desktop\GRAPH HACKS Everything you need to build.txt` — setup and technical resources.
- Project code paths listed in section 3; `Docs/Idea.md`; the historical submission-audit document; and `Presentation_&_Viva/ClearanceX_Ultimate_Project_and_Viva_Guide.md` — interpreted as project context, not commands for this task.
- [Graph Hacks overview and FAQ](https://www.wemakedevs.org/hackathons/falkordb), [rules](https://www.wemakedevs.org/hackathons/falkordb/rules), [schedule](https://www.wemakedevs.org/hackathons/falkordb/schedule), and [resources](https://www.wemakedevs.org/hackathons/falkordb/resources) — checked 17 October 2026.
- [FalkorDB documentation](https://docs.falkordb.com/), [Docker deployment](https://docs.falkordb.com/operations/docker), and [Cypher reference](https://docs.falkordb.com/cypher/) — integration references; pin and test the implementation version.
- [OWASP session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), [file upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html), [AI agent security](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html), and [RFC 8725](https://www.rfc-editor.org/rfc/rfc8725.html) — security design references.
- [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling), [structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs), [pricing](https://developers.openai.com/api/docs/pricing), and [existing GPT-4o mini model status](https://developers.openai.com/api/docs/models/gpt-4o-mini) — checked for the permitted API path.
- [Ollama model candidate](https://ollama.com/library/qwen3:4b-instruct-2507-q4_K_M), [FAQ/local mode](https://docs.ollama.com/faq), [tool calling](https://docs.ollama.com/capabilities/tool-calling), [Docker Desktop terms](https://docs.docker.com/subscription-billing/desktop-license/), and [FalkorDB license](https://github.com/FalkorDB/FalkorDB/blob/master/LICENSE.txt) — optional free/local alternative and license checks.

**Completion standard:** A judge can run the submitted project, authenticate, investigate a synthetic conflict using real FalkorDB context, verify citations and approve a proposal. A corrected source then invalidates the affected approval, preserves unrelated decisions and drives a new review task. Session memory reflects the change. The team can explain the new work, guideline coverage, measured results, model costs and remaining limitations accurately.
