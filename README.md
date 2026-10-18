# ClearanceX Context Agent

ClearanceX connects shipping-document evidence to reviewer decisions. It investigates conflicts using FalkorDB, proposes a source-linked review task, and identifies which approvals become stale when a supporting document changes.

Built with React/TypeScript, FastAPI, PostgreSQL, FalkorDB and optional OpenAI API inference. The default infrastructure runs locally. OpenAI is a deliberate usage-based option, disabled until configured. This is a document-review prototype; template XML generation is not verified official ASYCUDA integration.

## Start locally with Docker

Requirements: Docker with Compose, internet for initial images, and enough memory/disk for the services. OCR is an optional heavier profile. Windows setup:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-local.ps1
docker compose --env-file .env.graphhacks up --build -d
docker compose --env-file .env.graphhacks exec api python -m context_app.admin create-user --email you@example.com
```

Save the generated password privately. Open **http://localhost:8080**, sign in, open **Context Agent** from the menu, and select **Create synthetic example**. It creates actual PDF files with explicitly precomputed synthetic extraction, then projects their assertions into a real FalkorDB graph. No paid model is needed to inspect graph evidence, create review tasks, approve source values, or demonstrate source-change invalidation.

Linux/macOS: copy `.env.graphhacks.example` to `.env.graphhacks`, replace both `GENERATE_ME` passwords with distinct random hexadecimal values, then run the same Compose commands. Never commit the private file. `scripts/setup-local.ps1` preserves an existing configuration. The databases and graph browser are not published to the host; the UI binds to loopback.

## Demonstrate the graph-dependent flow

1. Create the synthetic example and wait for **Graph synced**.
2. Select **Gross Weight**. The graph retrieves the invoice/packing list at 450 kg and AWB at 440 kg. Open a source page.
3. Enter a review reason, create a review task and, once synced, approve the packing-list assertion.
4. Select **Package Count**, create a separate task and approve the invoice's 12 packages. This is the unaffected decision.
5. Apply the **synthetic packing-list correction to 440 kg**. The graph traverses dependencies. The weight approval becomes stale; the package-count decision remains current.
6. After synchronization, reopen the dossier in another session. Historical approval is retained, but stale memory is excluded. Export readiness requires re-review.
7. When configured, **Run investigation** uses real OpenAI function calls to select the graph tools and persist a pending review task. An unconfigured model reports an explicit error; it never returns a simulated agent answer.

FalkorDB is required for context queries, proposals, approvals and source-replacement impact. There is no SQL/NetworkX replacement when the graph is unavailable. Existing deterministic discrepancy code remains for the ordinary review screens.

## Enable the OpenAI agent deliberately

In private `.env.graphhacks`, configure all of:

```dotenv
ENABLE_LIVE_AGENT=true
OPENAI_API_KEY=your_private_project_key
OPENAI_AGENT_MODEL=your_supported_tool_calling_model
AGENT_BUDGET_USD=your_chosen_total_ceiling
MODEL_INPUT_USD_PER_MILLION=verified_input_rate
MODEL_OUTPUT_USD_PER_MILLION=verified_output_rate
```

Recreate the API with `docker compose --env-file .env.graphhacks up -d api`. Choose a currently available model supporting Chat Completions function calls/structured outputs; verify its current prices. Do not copy the placeholder values above literally. The previous `gpt-4o-mini` default is not assumed to be an appropriate current model.

The agent reserves a conservative per-call cost in PostgreSQL, enforces six tools, one nonparallel call at a time, 600 output tokens per request, a bounded context and at most one final-answer repair, no provider retries or model escalation. The application ledger is shared across processes. Unknown outcomes remain charged at their reserved upper bound. Prices must cover the selected model's complete billed token categories. This is a conservative application control, not a guarantee about a provider invoice or other applications using the same key. Never put keys in the frontend. [Official OpenAI pricing](https://developers.openai.com/api/docs/pricing).

## Architecture and graph model

```text
Browser -> session/CSRF/tenant checks -> FastAPI
  -> PostgreSQL: identity, immutable source history, decisions, tasks, runs, usage, outbox
  -> private PDFs: authorized page viewing
  -> outbox worker -> versioned FalkorDB snapshots
  -> bounded agent -> typed graph tools -> pending review proposal
  -> human decision -> graph dependencies -> stale approval on corrected source
```

`Shipment -> Document -> Assertion -> CanonicalField` retains contradictory evidence. `Decision -> DEPENDS_ON -> Assertion -> DEPENDS_ON -> Document` makes change impact queryable. `Memory -> DEPENDS_ON -> Decision` excludes invalidated conclusions. Each tenant gets a graph selected by the authenticated backend, with shipment/revision filtering inside every query.

Essential queries: [`backend/context_app/queries/`](backend/context_app/queries/). Full model: [Docs/GRAPH_MODEL.md](Docs/GRAPH_MODEL.md). Setup, recovery and optional MCP: [Docs/LOCAL_SETUP.md](Docs/LOCAL_SETUP.md).

## Security and data boundaries

- Generated local accounts; Argon2id passwords; random opaque sessions stored as digests; expiry, rotation, logout revocation and membership/role checks.
- CSRF verification and exact allowed origins on mutations. Local HTTP uses clearly named development cookies. Set `COOKIE_SECURE=true` only behind correctly configured HTTPS; hosting requires the corresponding origin/proxy configuration.
- All dossier, graph, status, audit, PDF and export routes enforce tenant ownership. Historical unowned uploads are preserved but not automatically exposed or assigned to an account.
- PDFs use generated storage names, signature/parser/page limits, per-file/request limits and private downloads. Local OCR executes in a bounded credential-isolated subprocess. This is not a hostile-file sandbox; public upload requires additional isolation and review.
- Model documents are untrusted input; no arbitrary Cypher, URLs, shell or approval tools. Output citation IDs and numerical claims are checked against retrieved evidence.
- Pending graph projection blocks graph-dependent actions. Expected revision checks and idempotency prevent stale or repeated decisions.
- Real events are stored; synthesized audit histories are no longer returned for application dossiers. This is not a tamper-proof ledger against database administrators.

## Test

Use an isolated Python environment and the explicit test services:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend/requirements-test.txt
npm --prefix frontend ci
npm run test:infra
npm test
npm run build
npm run lint
```

Linux/macOS: create `.venv` with `python3 -m venv .venv` and install through `.venv/bin/python`. Test services use loopback ports **5449** (PostgreSQL) and **6399** (FalkorDB); application databases are separate. `npm test` explicitly selects integration and compatible domain tests; older standalone print-and-exit scripts are not silently treated as pytest suites.

The tests exercise real database/graph queries, selective invalidation, dependency-edge ablation, replay/stale requests, private PDFs, sessions/tenant denial, graph outage, usage reservations and the agent loop with a clearly labeled scripted provider. Live paid-model and real OCR quality checks are separate. See [Docs/EVALUATION.md](Docs/EVALUATION.md) for observed validation and limits.

## Existing app improvements and honest scope

Implemented: real sign-in, private sources, graph-backed context screen, persistent decisions/memory/events, source replacement, real graph visualization, upload error handling, bounded polling, explicit OCR failures, shared spending controls and reproducible Compose configuration.

The dossier list supports search, filters, sorting and pagination. Upload monitoring cancels on navigation and can resume or retry saved jobs. Review drafts autosave privately per user; source replacement/type corrections preserve history. Administrators can save versioned workspace settings; weight-policy changes make affected approvals stale. Real batch preparation persists each dossier's result and downloads available reviewed XML files with a manifest. Export snapshots record their source revision, reviewer and dependencies and become stale after relevant changes.

Digital PDFs are parsed locally from actual text, including labeled fields across pages and explicitly pipe-delimited goods tables. Scanned documents still require the optional PaddleOCR profile; arbitrary layouts and calibrated extraction quality are not claimed. Tariff references remain samples. JWT, MFA, managed hosting, multiple cooperating agents, company-wide knowledge and full production retention remain roadmap items.

The packaged MCP smoke uses a real stdio client, authenticated HTTP and FalkorDB; source reading, proposal creation and logout denial passed. Live initial and corrected-source OpenAI investigations also passed through the packaged API. See the [completion report](Docs/GRAPH_HACKS_COMPLETION_REPORT.md) for exact scope and remaining items.

## Submission materials

- [Work plan and guideline coverage](GRAPH_HACKS_WORKPLAN.md)
- [Existing/new-work record](Docs/GRAPH_HACKS_DELTA.md)
- [Demo script](Docs/DEMO.md)
- [Evaluation report](Docs/EVALUATION.md)
- [Completion report](Docs/GRAPH_HACKS_COMPLETION_REPORT.md)

Primary intended track: Agents That Act on Connected Data. Enter memory/other tracks only for demonstrated capabilities. Confirm existing-project reuse eligibility with the organizers. The team must register, verify licensing/data permissions, record the actual working demo and submit; no submission or public deployment is performed by this repository.

AI assistance disclosure: Codex assisted with this implementation and tests. Team members must inspect, verify and understand the submitted code. Earlier project components are retained and identified in the delta record.


Latest four-PDF verification: [nine runtime fixes and tested output](Docs/NINE_FIXES_VERIFICATION.md). The current local build supports source-linked per-item goods review, stale-review invalidation, Decimal valuation allocation and authoritative Overview readiness while retaining the original Overview design.
