# Competition fit, accounts and security review

**Current password/security update:** New customer accounts and admin resets require a customer-chosen password before shipment access. Session/CSRF rotation, global session revocation and password-change throttling are tested. See [the current web/password report](WEB_POLISH_REPORT.md) for all 78 backend/28 frontend results and runtime evidence.

Reviewed and implemented on **18 October 2026**, Asia/Colombo. This assessment covers the current ClearanceX source, retained work plan, supplied Graph Hacks guide, existing verification records and new account/security tests. It is not an independent penetration test or an organizer's judging score.

## Competition match: 8/10

**Track 01 — Agents That Act on Connected Data is the strongest match.** The official event requires FalkorDB to be central. ClearanceX uses it to retrieve connected evidence, trace changed sources to dependent decisions and determine which approvals require review. This is a concrete reason to use a graph. The event allows reused general infrastructure, but the submission and main FalkorDB implementation must be new during the event; the team must establish that boundary for this existing project. A working demo video and reproducible local setup matter if no deployment is supplied. See the [official competition brief and FAQ](https://www.wemakedevs.org/hackathons/falkordb).

The **8/10 is my technical-fit assessment**, not an official rubric, eligibility ruling or prediction of winning. I would not rate the current submission 10/10.

| Dimension | Assessment from this project |
|---|---|
| Graph centrality | Strong: real FalkorDB queries, version checks and graph-dependent decisions; no successful SQL answer fallback during a graph outage. |
| Agent action | Strong: recorded real OpenAI tool selection, source citations and persisted proposed review tasks. Human approval remains required. |
| Useful graph behavior | Strong: document correction selectively stales affected decisions, memory and export artifacts. |
| Product demonstration | Good: four real digital PDFs, review, graph inspection and test XML have been exercised. Extraction remains limited to supported layouts. |
| Memory/coordination | Partial: durable approved/current/stale context and authenticated MCP exist; multiple cooperating agents and cross-shipment lessons remain unverified/future work. |
| Evidence and submission | Incomplete: held-out evaluation, remaining browser acceptance, team explanation, original-event-work evidence, final video/repository and submission need completion. |

Track 02 is a secondary possibility when the team can demonstrate memory updates and stale-context exclusion. Do not claim completed multi-agent handoffs or Company Brain features. No recommended competition features have been removed from the work plan; unimplemented ones remain explicitly scoped there.

The best route toward a stronger entry is to record one clear sequence: investigate a weight conflict → inspect actual evidence → approve a source → correct that source → show only the dependent approval becoming stale → investigate again. Compare graph and flat retrieval on a held-out set, show failure cases, and explain why the graph changed the outcome. Finish the submission assets and eligibility evidence before expanding the feature list.

## Delivered admin/customer model — corrected

The ClearanceX platform administrator adds customer User logins through `/admin/companies`. Each new customer receives an isolated company workspace and can use the existing shipment application. Customers have no platform dashboard access. The operator can edit company details, reset credentials and disable/restore/remove access while preserving shipment history. Public signup is restricted. New users cannot choose or receive platform privileges through the web API.

Platform authority is an explicit `platform_admin` database privilege; legacy workspace `admin` roles do not grant it. The operator account is routed to the customer-management dashboard and denied shipment data APIs. Password confirmation, strict payload validation, session revocation, company status checks, bound SQL and versioned edits protect management actions. Admin-created passwords can be supplied or generated and are shared privately.

Migration 7 is applied locally after a private backup. Existing company memberships, documents, Overview design and the requested local password choices are preserved. See [ADMIN_CUSTOMER_FLOW.md](ADMIN_CUSTOMER_FLOW.md) for current setup and verification. This supersedes the earlier workspace-account interpretation.

## SQL injection and security findings

**No exploitable SQL injection was found in the reviewed paths or tested payloads.** This is a scoped result, not proof that every attack is impossible. The review covered authentication, account management, dossier filtering/sorting, graph tools and fixed migration/health SQL.

| Area | Finding / protection |
|---|---|
| SQL values | SQLAlchemy binds user values. Account search also escapes SQL LIKE wildcards so search stays literal. Dossier search wildcards can broaden a permitted search but do not execute SQL. |
| SQL identifiers | Sorting uses a fixed mapping. Migrations and health SQL use fixed statements; user input is not concatenated into SQL syntax. |
| Cypher | Values are parameters; graph labels/relations are fixed. Named query templates now also require an explicit filename allowlist, preventing path traversal through template names. |
| Account creation races | Unique-email conflicts, including insertion-time conflicts, return a controlled conflict response. |
| Authorization | Operator actions re-read live platform privilege/session inside the management transaction. Customer shipment routes remain company-scoped; platform administration does not grant shipment data access. |
| Session handling | Random opaque tokens, digest storage, HttpOnly/SameSite cookies, absolute/idle expiry, logout and administrative revocation. JWT remains an optional external-client design; a second token system was not added. |
| Mutation protection | Exact allowed origin and session-bound CSRF checks; password re-entry is throttled after repeated failures. Login throttling remains active. |
| Sensitive data | Password hashes/secrets are absent from account lists/events. API responses use no-store. Private PDF access requires authorization. |
| Agent and uploads | Existing narrow tools, human approval, citation checks, bounded file parsing and private storage remain. Documents cannot request arbitrary SQL/Cypher or shell execution through tools. |

This follows OWASP's preference for bound values and fixed identifier allowlists and for server-side authorization on each request: [SQL injection prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html), [authorization guidance](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html).

Before public production use, configure HTTPS and Secure cookies; separate the runtime database role from schema-administration privileges; add MFA and complete production account-recovery protections; review log retention, load/rate limits and hostile-file isolation; and arrange an independent security assessment. Local Compose is loopback-only, and its database user currently also owns/migrates the schema. The parser subprocess is not a hardened sandbox. Login IP throttling sees the local reverse proxy address, so a public deployment needs a deliberate trusted-proxy/rate-limit design. Account events are not a tamper-proof ledger against database administrators. A provider key was previously pasted in chat: replace that exposed key before sharing/deploying the application, without publishing it in documentation.

## Verification results

Story: an administrator creates a workspace User, grants or removes access, resets credentials, and the server enforces those changes on existing sessions while preserving document history.

| Boundary/check | Result and evidence |
|---|---|
| Backend regression suite | **78 passed, 1 skipped**. Real isolated PostgreSQL/FalkorDB; the skip is the existing Windows stdio MCP case. Existing packaged Linux MCP evidence remains separate. |
| New backend account/security coverage | **15 tests passed**: onboarding and product access; platform/customer role separation; restricted signup; hashes/no-secret listing; company isolation; disable/restore and retained shipments; stale versions; password reset/session revocation; CSRF/origin and confirmation throttling; SQL/Cypher inputs and concurrent updates. |
| Frontend interactions | **28 passed**, including 4 account-page tests. Customer/legacy-admin denial before data fetch; new customer onboarding; masked/dismissible credentials; confirmation clearing; versioned access changes and stale failures. APIs are mocked here. |
| Running local API/data flow | **38 current checks passed**, including operator onboarding, new customer login/product access, password reset, company isolation and all four supplied digital PDFs. QA access was disabled afterward. The earlier 18-check workspace-account smoke is historical. |
| Container build | API/frontend rebuilt successfully; the frontend's 16 tests also passed inside Linux before compilation. |
| Migration | Running app reports ordered versions 1–8. Health/readiness succeeded after rollout. |
| Lint/build limitations | No lint errors; effect/fast-refresh warnings remain, Route splitting reduced the main entry to about 315 kB; no main-chunk size warning remains. |
| Browser acceptance | No new browser sign-off is claimed. A saved browser policy previously blocked reliable local automation. This task verifies the new UI in simulated DOM tests and the real server separately; visual admin-page acceptance remains open. |

Machine-readable evidence: [account runtime checks](../output/verification/customer-runtime.json), [frontend interaction results](../output/verification/ui-component-tests.json). Re-run the runtime smoke with `python scripts/verify_customers.py --credentials <private-json-file>`; it creates QA customer logins, tests isolation/reset, disables QA company access and logs out its operator session. It makes no paid model calls.

**Outcome:** account management and the requested scoped security checks are implemented and verified within these boundaries. The broad competition work plan is still not fully complete, and the project is not rated 10/10 or certified production-secure.
