# Local UI and service verification

Date: 18 October 2026, Asia/Colombo.

## Scope and current result

The supplied screenshot shows no file selected. Upload previously stayed disabled in that state without explaining how to start. The upload action now opens the file picker when no PDFs are selected; after selection, the same action uploads and extracts them. A visible selection count explains the next step. Invalid file types, count and size limits are checked before uploading. The file input clears after an accepted upload so the same PDFs can be selected again.

The original Overview design remains intact.

## Repairs made during this check

- Upload: actionable empty state, styled file picker, selection instructions, early validation and consistent cleared state.
- Graph: handle refresh and library-load failures visibly, cancel obsolete requests, dispose graph initialization safely, distinguish the actual canonical-field node type, and disable export until data loads successfully. JSON export no longer incorrectly claims JSON-LD.
- Screen loading: an error boundary offers application refresh instead of leaving a blank screen if a screen fails to load after an update.
- Audit: refresh now retrieves events from the server; it no longer shows a notification that implies a check occurred. Obsolete requests are cancelled and event hashes, where present, are displayed without adding fake truncation marks. This is an event history viewer, not a cryptographic integrity certification.
- Tariff: preserve reference search, sector filters, example selection and tare calculation; clearly identify the examples as unverified. Replace misleading conformity/official-calculator labels. Reject negative or fractional pallet counts and tare exceeding gross mass. Provide an empty search result and accessible input names.

## Actual running-service checks

Run: `.venv/Scripts/python.exe scripts/verify_local_screens.py` against the application at `http://localhost:8080`, using the existing private local account.

| Check | Result | Evidence |
|---|---|---|
| Graph endpoint | Passed | 79 unique nodes, 195 relationships; every relationship endpoint exists. Shipment, document, assertion, canonical-field and goods-review nodes present. |
| Audit endpoint | Passed | Six events in the browser-created QA dossier; source decision and goods-review saves present with timestamps. |
| Mixed batch | Passed | Reviewed QA dossier prepared; incomplete dossier blocked. ZIP contains exactly one two-item XML and an accurate manifest. |
| Batch retry | Passed | Repeating the same request ID returns the same saved result. |
| Upload validation | Passed | Empty submission and malformed PDF both rejected with HTTP 422. |
| App routes | Passed at HTTP layer | Upload, graph, batch, audit and tariff routes return the app shell. This alone is not browser proof. |

Machine-readable evidence: [local-screens-runtime.json](../output/verification/local-screens-runtime.json).

Test dossiers: ready `04c681ac-cbf6-444a-8dbc-8a0c1998566c`; intentionally incomplete `70228036-5821-4401-a0f5-b64ad5056c0f`. Their reviews are automated QA examples, not approval to file a declaration. The test creates a saved local batch and makes no external declaration submission.

## Browser verification

The previous Chrome session verified login, the restored Overview, four-PDF upload (4/4 complete), original PDF preview, source decision, both goods reviews, blocked export for the new dossier and a successful reviewed XML download whose SHA-256 matched the verified output.

Current Chrome checks:

- Graph: passed rendering (80 nodes, 202 relationships after the test batch added another export snapshot), clicking a canonical-field node showed Consignee Name in the inspector, and Graph JSON downloaded successfully. Its counts match the displayed graph.
- Batch: passed selecting the reviewed QA dossier, preparing a completed batch (`a264b7a8`), and downloading its ZIP in Chrome. Downloaded archive contains one XML and the completed manifest. A mixed batch's raw technical error display was identified and replaced with readable required actions and explicit dossier IDs/readiness.
- Audit: passed in Chrome. Refresh retrieved 17 saved events for the ready QA dossier; selecting a decision changed the event detail panel; JSON downloaded successfully and contains the same 17 events.
- The final batch display was observed in Chrome with readable blocker messages and explicit dossier IDs/readiness.
- Tariff and revised upload empty-state click-through are still pending in this report until observed in Chrome.

Production TypeScript/Vite and container builds passed; the rebuilt frontend is running locally. Lint completed with existing effect/fast-refresh warnings and the build retains a large-chunk warning. The prior Computer Use session ended because it could not determine Chrome's URL reliably enough for policy enforcement; that was a tool stop, not proof these screens fail.

## Limits

The tariff page is an interactive demonstration with sample data, not a maintained live tariff service. Browser testing does not establish official ASYCUDA acceptance, all possible PDF layouts, production load behavior or completion of every competition roadmap item. No paid model calls were made for these checks.
