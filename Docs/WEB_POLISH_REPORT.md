# Web quality and first-login password setup

Updated **18 October 2026**, Asia/Colombo. This report covers the requested website improvements and the additional first-login password requirement. It does not assign a guaranteed 10/10 score or establish competition eligibility, production certification or a winning result.

## Delivered behavior

The product model remains: **ClearanceX administrator adds customer accounts → customers sign in → customers process shipments in their own company workspace.** The original Overview component/design is retained, as are the competition recommendations in the work plan. No paid service or model call was added for these changes.

### Customer sign-in and passwords

1. The administrator adds a company/user and either supplies an initial password or lets ClearanceX generate one.
2. The customer signs in with that temporary password. The app opens **Choose your own password**.
3. The customer enters the current password, a new 10–128 character password, and its confirmation.
4. The server verifies the current password, stores only the new Argon2id hash, clears the first-login requirement and rotates the session/CSRF token. Other sessions are revoked.
5. The customer continues into the shipment product. The temporary password no longer works.

The first-login restriction is enforced by the API, not only by a page redirect: temporary-password sessions can use password setup, session information and sign-out, but cannot read/upload/review shipments. An administrator's password reset makes the customer complete this step again. Incorrect password attempts are throttled; CSRF/origin and strict request-schema checks apply. An audit event records the change without passwords.

Existing local accounts and the user's previously selected local passwords were preserved. Migration 8 defaults existing accounts to no forced change; new dashboard-created accounts and future administrator resets require it. Existing customers can also select **Change password** from their account menu. Public self-registration remains restricted.

The customer password minimum was subsequently adjusted from 12 to 10 characters to support the owner's requested password length, consistently in the form and API. Follow-up verification passed all 29 component tests and two focused backend integration tests covering ten-character acceptance, nine-character rejection, first-login restrictions, session rotation and old-password rejection. These tests used synthetic accounts in the isolated test database. The requested real customer onboarding through the UI remains unverified and was not performed: the browser security layer denied localhost access because of a saved permission setting.

The sign-in screen now uses a responsive two-column company/product introduction, readable form spacing, password visibility, clear failures and invitation-based access guidance. It does not claim that an email has been sent or that declarations are submitted to customs.

### Administration

- Customer creation, access changes and password resets now open a named confirmation dialog, explaining consequences and asking for the operator password. Cancel/Escape sends no mutation.
- Dialogs and navigation keep keyboard focus inside while open and return focus when closed. Pending saves cannot be dismissed accidentally.
- New customer creation automatically focuses the list search on that email, avoiding confusion when alphabetic pagination would otherwise hide the new account.
- Active/disabled/removed filters run on the server before pagination. New accounts show that first-login password setup is pending.
- New login details remain masked, dismissible and available through an explicit **Copy login details** action. Clipboard failure gives manual-copy guidance. Credentials are not stored in browser storage.
- A failed list refresh does not discard a successfully created customer's generated credentials. The list has its own visible retry action.
- Activity displays company names. Page members and shipment counts are fetched in batches instead of repeating queries for every company.

### Graph review

Context Agent now includes **What depends on this document?** Select a source and preview actual Decision, Memory, GoodsReview, ReviewTask and ExportSnapshot dependencies through the existing bounded FalkorDB tool.

The preview is read-only and uses an expected revision. A stale revision is rejected, graph failures remain visible, and changing sources clears the previous result. Counts and records come from the graph; no dependency path or impact count is invented. Empty results do not claim export readiness. Historical/stale records are labeled, and a link opens the shipment's graph explorer.

### Navigation and loading

- Screens and the authenticated header load separately. The main production entry decreased from the previously recorded **560.16 kB to approximately 315 kB**, about **44% smaller**. This is an entry-file byte comparison, not total application size, measured speed or a Lighthouse score. See the machine-readable bundle record.
- Sign-in has no signed-out shipment sidebar. Admin/customer/first-login routing remains distinct. Missing customer URLs show a recovery page, and delayed/failed chunks have loading/error boundaries.
- Account initials and company labels replace fixed initials and generic demo labels. The Overview header keeps readable controls when it changes from transparent to white while scrolling.
- Keyboard focus rings, skip-to-content, reduced-motion behavior, accessible notifications, closed-sidebar inert state and Escape/focus restoration were added. Sign-out failures are shown rather than becoming unhandled errors.

## Verification

| Check | Result / limits |
|---|---|
| Full selected backend suite | **78 passed, 1 skipped**, one existing test-client deprecation warning. Real isolated PostgreSQL/FalkorDB; live paid inference is disabled in this suite. |
| Frontend interactions | **28 passed**. Covers admin/customer denial, action confirmation/cancellation/focus, filtering, retained credentials after refresh failure, sign-in/password setup, graph preview/retry/pending state, uploads, tariffs, audit and batch behavior. APIs are mocked here. |
| Running customer flow | **38 checks passed**: actual temporary login → required password setup → rotated session → shipment access; reset repeats setup; four supplied PDFs extract; other-company access is denied. QA company access was disabled afterward. |
| Running graph/product boundaries | **13 checks passed** with the preserved local accounts. An existing reviewed packing list returned **8 graph dependencies**: 4 export snapshots, 2 goods reviews, 1 decision and 1 memory. Stale preview returned 409; source revision remained unchanged. |
| Production/container builds | Passed, including the 28 frontend tests in Linux. Migration versions 1–8 are applied locally after a private backup. No new dependency subscriptions or paid model calls. |
| Code/lint | No lint errors; existing effect/fast-refresh warnings remain. The previous main-bundle size warning is resolved by splitting routes; this is not a claim of zero technical debt. |
| Real browser visual acceptance | **Not newly signed off.** The earlier saved browser permission/URL-enforcement limitation has not been overridden. Simulated UI interactions and actual HTTP/data checks are separate evidence. |

Evidence: [frontend results](../output/verification/ui-component-tests.json), [customer flow](../output/verification/customer-runtime.json), [graph/product checks](../output/verification/web-polish-runtime.json), [bundle measurement](../output/verification/web-polish-bundle.json).

## What still prevents a credible perfect-score claim

Complete visual acceptance at desktop/mobile sizes, independent clean-machine reproduction and broader held-out document evaluation remain. The retained roadmap still includes general/scanned PDF accuracy, measured source geometry, broader agent coordination and production hardening. Tariffs remain illustrative; generated XML is not certified official customs acceptance. Competition video, final submission and event-originality evidence remain team deliverables. Existing local demonstration passwords must not become production defaults.

The supported local onboarding/password/shipment flow is implemented and tested. These results do not mark every item in the broad work plan complete.
