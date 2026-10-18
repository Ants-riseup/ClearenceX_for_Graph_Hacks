# Validation record

**Current web/password update — 18 October 2026:** Admin-created customer accounts now sign in with temporary credentials and must choose their own password before entering the shipment product. Admin confirmation/filtering, graph dependency preview, keyboard navigation and route loading are improved. **78 backend tests passed, 1 skipped; 28 frontend tests passed; 38 live customer checks and 13 graph/product checks passed.** See [the current implementation report](WEB_POLISH_REPORT.md). The original Overview and recommended competition features are retained. Earlier validation counts below describe previous stages; broad roadmap/submission gates remain open.

**Latest remediation — 18 October 2026:** All nine runtime findings are fixed within the tested scope. Full selected suite: **62 passed, 1 skipped**, one warning in 98.54 seconds, plus a passing focused follow-up. Actual packaged four-PDF upload/review/export passed with distinct item classifications and reconciled allocations; no paid calls. See [NINE_FIXES_VERIFICATION.md](NINE_FIXES_VERIFICATION.md). Older findings/results below are historical.

**Latest follow-up — 18 October 2026:** The extraction-fix suite completed with **55 passed, 1 skipped**, one warning in 213.55 seconds; both rebuilt app containers are running. A fresh real four-PDF upload now returns correct types, 27 assertions and six source table rows describing two goods items. Local API and synthetic negative checks found nine further defects; invalid goods totals and a nonnumeric exchange rate can reach exports in a fully populated synthetic control. See [LOCAL_RUNTIME_BUG_REPORT.md](LOCAL_RUNTIME_BUG_REPORT.md). These checks used no paid model calls and do not establish browser success.

**18 October 2026 supplied-input check:** Four original PDFs from `Docs/TEST FILE` passed upload and protected download, but failed extraction accuracy. Only five assertions and no goods rows were returned; the worksheet type was wrong. No downstream correctness or live model success is claimed for these inputs. See [FOUR_PDF_VERIFICATION_REPORT.md](FOUR_PDF_VERIFICATION_REPORT.md). This finding does not invalidate the earlier scoped synthetic results, but prevents claiming general document readiness.

Updated 17 October 2026 (Asia/Colombo). Evidence is in `output/verification/`. These are prototype measurements, not independent certification.

## Current checks

- Final selected suite: **48 passed, 1 skipped, 1 deprecation warning**, 517.57 seconds. Tests run against isolated real PostgreSQL and FalkorDB. Coverage includes tenant/role/session/CSRF boundaries, private PDFs, request limits, atomic ingestion, comparisons, migrations, settings, drafts, selective invalidation, concurrency, immutable exports, graph recovery and agent contracts. Provider contract tests use an explicitly scripted provider; separate live results follow.
- Windows stdio MCP test is skipped because its child HTTP service timed out. A **real stdio MCP -> authenticated packaged HTTP -> FalkorDB** check passed in Linux: six tools, three assertions, pending task and denied replay after logout (`packaged-mcp.json`). This does not prove every third-party MCP host works.
- Production React/TypeScript build and both container builds pass. Lint passes with warnings. A graph-library chunk remains over 500 kB. No claim of a warning-free build.
- Core/test/MCP dependency consistency and the earlier advisory check passed; optional legacy OCR dependencies were outside that check.
- Backup was restored into an isolated PostgreSQL database and separate FalkorDB container. Five dossiers, four migration records, graph readability and 16 PDF reference/hash checks passed (`restore-check.json`, `pdf-restore-check.json`). The original application database was not replaced.
- Browser verification is blocked by the app's saved/managed origin policy, even after user permission. API/container proof is not visual or click-through proof.

## Actual model and application flow

Model: `gpt-4.1-mini-2025-04-14`. Rates configured for measured estimates: $0.40 input / $1.60 output per million tokens, as listed in [OpenAI model documentation](https://developers.openai.com/api/docs/models/gpt-4.1-mini). Rates and access can change. The shared application ceiling is **$0.25**, with no automatic larger-model fallback.

`packaged-flow.json` records a successful real HTTP flow: login; model-selected issue/evidence tools and persisted proposal; protected PDF delivery; two approvals through the reviewer API; a source correction; dependent weight approval made stale while package approval remains current; export blocking; live change-impact investigation and a new proposal; logout/login and correct current memory recall. The two runs cost an estimated **$0.0082296**. Approvals were automated reviewer API requests, not human browser clicks.

Earlier live attempts failed citation/numeric validation. They are retained in usage accounting; they are not relabeled successful. The runtime now restricts citation IDs to retrieved evidence and allows at most one final-answer repair within its turn/time/budget limits. A separate initial live smoke cost $0.002608 (`live-agent-smoke.json`).

## Six-dossier / twelve-question experiment

Synthetic cases: matching values, conflicting weights, missing net weight, ambiguous carrier/consignee text, superseded approval with an unrelated current approval, and hostile document instructions. Both modes use the same model and final task prompt. The graph harness selects typed retrieval by fixed question; it is not the autonomous tool-selection experiment above. The flat baseline receives serialized dossier context.

| Retained run | Graph correct | Flat correct | Combined estimated cost | Interpretation |
|---|---:|---:|---:|---|
| v1 | 9/12 | 7/12 | $0.0240664 | Ambiguous abstention scoring and graph node-type issue discovered. |
| v2 | 11/12 | 11/12 | $0.0249128 | Same clarified prompt in both modes; stale-source case still failed. |
| v3 | 12/12 | 10/12 | $0.0271376 | Richer graph dependency/stale-artifact context. |

All runs are preserved as `evaluation-v1.json` through `evaluation-v3.json`. The dataset was used during debugging; **it is not held out**. Twelve synthetic questions do not establish a general accuracy advantage or production extraction quality. V3 graph retrieval cited 23/23 expected evidence hits; the flat run also hit those sources but included an archived source as current and failed another field-status case. Median end-to-end model latency was about 2.38 seconds in both modes; provider variability and tiny sample size limit comparison.

Latest warm graph benchmark, including the new missing-snapshot preflight: five warmups then 100 sequential evidence queries on one three-assertion synthetic dossier. Median **2.68 ms**, nearest-rank p95 **4.48 ms**, maximum **5.15 ms** (`graph-benchmark.json`). Earlier before-preflight measurements are preserved separately. This is not a load, cold-start, large-data or cross-version benchmark.

## Spending and boundaries

Recorded host evaluations/smokes total $0.0787248 estimated. The packaged application's shared ledger records $0.03133 estimated, including failed runs, with zero outstanding reservation (`application-usage.json`). Combined recorded estimate: **about $0.11**. The provider bill and remaining account credit were not independently fetched; the application's ceiling does not cover unrelated provider activity or the separate capped evaluation harness.

Digital labeled PDFs and explicit pipe-format multipage goods tables are tested. General scanned OCR, arbitrary commercial table layouts, calibrated confidence, accurate bounding boxes, maintained tariff advice, official customs acceptance, production HTTPS/load and public submission are not established. No public deployment or competition submission was performed.

## Final packaging and persistence

All four application containers were forcibly recreated with the named volumes preserved. The live-flow dossier remained at revision 10, with matching graph revision, stale weight approval, current package approval, one current memory record and four readable private PDFs (`persistence-recreate.json`).

The allowlisted source ZIP was extracted to a new folder. Fresh frontend dependency installation reported zero vulnerabilities, TypeScript/Vite build passed, Python source compilation passed, and archived backend imports passed using the packaged dependency image with networking disabled. This checks archive completeness on this host; an independent clean-machine/public-checkout review remains pending (`source-package-check.json`).
