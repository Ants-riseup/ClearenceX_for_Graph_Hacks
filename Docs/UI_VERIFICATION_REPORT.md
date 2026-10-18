# Local UI and service verification

**Current web/password update — 18 October 2026:** Admin-created customer accounts now sign in with temporary credentials and must choose their own password before entering the shipment product. Admin confirmation/filtering, graph dependency preview, keyboard navigation and route loading are improved. **78 backend tests passed, 1 skipped; 28 frontend tests passed; 38 live customer checks and 13 graph/product checks passed.** See [the current implementation report](WEB_POLISH_REPORT.md). The original Overview and recommended competition features are retained. Earlier validation counts below describe previous stages; broad roadmap/submission gates remain open.


Date: 18 October 2026, Asia/Colombo.

## Scope and current result

The supplied screenshot shows no file selected. Upload previously stayed disabled in that state without explaining how to start. The upload action now opens the file picker when no PDFs are selected; after selection, the same action uploads and extracts them. A visible selection count explains the next step. Invalid file types, count and size limits are checked before uploading. The file input clears after an accepted upload so the same PDFs can be selected again.

The original Overview design remains intact.

**Account-management update:** Four account-screen interaction tests and 18 running account API checks now pass. Admin/User controls, disabled public signup, generated password handling, role denial, reset/disable and session invalidation are covered. See [the competition and security review](COMPETITION_AND_SECURITY_REVIEW.md). The admin screen itself has not received a new visual browser sign-off.

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
- Tariff: Chrome rendered the sample notice, sector filtering reduced the table to Textiles, selecting HS `6006.22.00` updated the calculator, and an unmatched search showed the explicit empty state. Valid/invalid calculator interaction is covered by the isolated tests below; that final browser interaction remains unverified.
- Revised upload empty-state file-picker opening remains unverified in a real browser. Its event handling, four-file submission, completion/reset/reselection, invalid drops/count and error retry passed the isolated tests below. The previous upload version already completed all four actual PDFs through Chrome.

Production TypeScript/Vite and container builds passed; the rebuilt frontend is running locally. Lint completed with existing effect/fast-refresh warnings and the build retains a large-chunk warning. The prior Computer Use session ended because it could not determine Chrome's URL reliably enough for policy enforcement; that was a tool stop, not proof these screens fail.

## Isolated UI regression tests

`npm run test:ui`: **28 passed**, using Vitest and [the documented jsdom environment](https://vitest.dev/guide/environment). This executes React event handlers in a simulated DOM with mocked API responses. It does not open a real browser, invoke an OS file chooser, upload private files, or contact a model/provider.

- Upload: empty-state action invokes the file input without an empty API request; four PDFs are submitted together; completed progress clears the input; the same files can be selected again; non-PDF drops/eleven-file selections are rejected; failed uploads preserve files and enable retry.
- Tariff: sector/HS filtering, empty results and sample selection; 1,000 kg gross with four pallets yields 910 kg net; negative/fractional pallet counts and tare exceeding gross mass disable calculation with an error.
- Audit: Refresh performs another retrieval and selected event details update.
- Batch: blockers are readable and an entirely blocked batch cannot download prepared files.
- Accounts: ordinary-user denial before fetching account data; private creation/default User role; masked/generated credential dismissal; confirmation clearing; versioned role/access changes; self-demotion controls and stale-action error handling.

Evidence: [component test results](../output/verification/ui-component-tests.json). Sources: `frontend/tests/local-workflows.test.tsx` and `frontend/tests/customer-administration.test.tsx and frontend/tests/signin-and-impact.test.tsx`. Test configuration/dependencies are included in the source archive. The builder uses Node.js 24 to match the test runner's supported runtime.

The same 28 tests passed inside the Linux frontend container build, followed by a successful production build. Dependency installation audited the frontend packages with zero reported vulnerabilities. These tests do not add runtime test dependencies to the final static application.

The latest browser attempt encountered a different access problem: Chrome exposed no targetable window, and the built-in browser rejected `http://localhost:8080` because a saved permission blocks origin access. Chat approval alone did not establish that the saved setting changed. No browser-security workaround was attempted. Final real-browser upload empty-state and calculator checks remain pending until that access is available.

## Remaining manual browser checks

1. Open `http://localhost:8080/dossiers`. With no files selected, click **Upload and extract**: the native file picker should open. Select the four PDFs in `Docs/TEST FILE`, then click **Upload and extract** again; expect all four to finish and the input to clear. Earlier Chrome testing already proved the actual four-PDF server processing path; the new empty-state activation is what remains to be observed in a browser.
2. Open **Tariff Directory**. Set gross mass to 1,000 and pallets to four: expect 910.00 kg net. Set pallets to -1, 1.5 or a tare exceeding gross mass: expect an error and disabled sample calculation. These interactions already pass in the isolated suite but have not been fully observed in the browser.

The browser tool's origin permission and URL-detection problem is outside this application's source. The report deliberately does not mark these two real-browser checks complete.

## Limits

The tariff page is an interactive demonstration with sample data, not a maintained live tariff service. Browser testing does not establish official ASYCUDA acceptance, all possible PDF layouts, production load behavior or completion of every competition roadmap item. No paid model calls were made for these checks.
