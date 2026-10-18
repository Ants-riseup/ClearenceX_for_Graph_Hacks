# Local runtime bug report

**Resolution — 18 October 2026:** All nine findings below have been addressed and verified against the rebuilt local app. See [NINE_FIXES_VERIFICATION.md](NINE_FIXES_VERIFICATION.md) for the current 62-test result and actual four-PDF export. This document retains the original findings as history.

**Date:** 18 October 2026, Asia/Colombo  
**Verdict:** The application is running and the earlier extraction fixes work on the supplied PDFs, but the application is **not fully okay**. Nine findings are listed below. This is a targeted verification, not an exhaustive security audit.

## Actual validation

- Latest full selected regression run: **55 passed, 1 skipped**, one deprecation warning, 213.55 seconds. Builds passed and all four application services are running; API, PostgreSQL and FalkorDB report healthy. Passing tests do not cover every business acceptance condition.
- Uploaded all four original PDFs together through the running frontend `/api` proxy. Dossier: `70a67012-16d0-4033-9466-8efdcc8bc7d9`, in the existing account's workspace under **Uploaded dossier**.
- Processing completed. All four classifications are now correct. Extracted 27 assertions and two rows each from invoice, packing list and customs worksheet. Those six source rows describe two goods items; they are not six distinct commodities. AWB correctly has no invoice goods rows.
- The worksheet is excluded from independent canonical evidence. Graph responses contain 50 nodes and 120 edges. Evidence, fields, graph, audit, memory and readiness endpoints returned 200.
- Authenticated source downloads matched the four input hashes. Anonymous PDF access returned 401. An isolated account could not read the existing account's dossier (404). Nonfinite goods quantity was rejected (400).
- The actual four-PDF dossier remains blocked: unresolved review fields, four missing required fields, declaration metadata and unverified goods. Export correctly returned 422 for that dossier.
- Separate fault probes used isolated QA workspaces and an explicitly labeled synthetic export-control fixture. Automated reviewer approvals were test actions, not human approval of a real declaration. Locally generated invalid XML was never submitted anywhere.
- No OpenAI calls, external filing, source PDF edits or Overview design changes were made in this check. Browser clicking remains unverified after Computer Use stopped on a URL-policy check in the previous attempt; this session used API/data and serializer tests only.

## Confirmed bugs

### R01 — Required export fields remain unavailable (P1)

**Evidence:** The real four-PDF readiness response reports `MISSING_FIELD` for `COUNTRY_OF_ORIGIN`, `PORT_OF_LOADING`, `PORT_OF_DISCHARGE` and `HS_CODE`. The PDF invoice contains origin codes and loading/discharge information; extracted invoice rows already contain individual HS codes. These are not promoted into a usable declaration workflow. The extraction quality label is still `extracted_needs_review` with no missing document fields for these requirements.

**Impact:** The main four-PDF export path cannot finish through the existing evidence-selection flow. A single shipment-level HS code also cannot represent the two different item codes correctly.

**Fix:** Extract and source-link country/port values, reconcile document and export requirements, and support HS classification per goods item. Keep missing values explicit and reviewable instead of supplying defaults.

**Location:** `backend/context_app/text_extract.py`; `backend/reasoning/cusdec_readiness.py:14`.

### R02 — One incorrect goods row can allow an incomplete export (P1)

**Reproduction:** In a fully populated synthetic control with two source rows and a USD 1,000 invoice, readiness initially had only `UNVERIFIED_GOODS`. Save one row with quantity 1, unit price 1 and total 1. Readiness becomes export-allowed, POST export returns **201**, and XML download returns **200**.

**Impact:** Row arithmetic passes, but missing source rows and invoice-versus-item totals are not reconciled. A single saved row clears the all-goods verification blocker.

**Fix:** Verify every required current invoice row, reconcile count/identity and monetary totals with the declared valuation basis, and block missing or inconsistent rows. Do not treat any nonempty saved-row list as complete verification.

**Location:** `backend/reasoning/cusdec_readiness.py:105`; `backend/context_app/exports.py:23`.

### R03 — Goods source references are not validated (P1)

**Reproduction:** Save a goods row with `source_reference: DOCUMENT-DOES-NOT-EXIST:page:999:row:999`. The endpoint returns **200** and persists that string as a reviewed row.

**Impact:** The row can claim evidence that does not exist in the dossier. In the isolated synthetic control this still permits export (R02).

**Fix:** Store a structured current document/revision/page/row identity, authorize and validate it against persisted extraction, and preserve a controlled manual-evidence workflow where extraction is unsupported.

**Location:** `backend/api/routes.py:464`.

### R04 — Invalid exchange rate reaches generated XML (P1)

**Reproduction:** Save `currency_rate: NOT-A-NUMBER`. The endpoint returns **200**. With other requirements satisfied in the synthetic control, readiness remains allowed and export returns **201**. The invalid literal is present in XML; numeric statistical-value calculation falls back to an empty value.

**Impact:** An export can be marked prepared with malformed valuation metadata.

**Fix:** Validate exchange rates as finite positive Decimal values at save and export time; validate other typed metadata rather than accepting arbitrary nonempty strings. Return actionable validation errors.

**Location:** `backend/api/routes.py:389`; `backend/reasoning/cusdec_readiness.py:140`; `backend/reasoning/cusdec_xml.py:122`.

### R05 — Reviewed goods stay verified after a source revision (P1)

**Reproduction:** Save rows tied to the invoice, then create a source revision through document-type correction. The original invoice moves out of current documents, but two saved rows referencing that old source still appear as verified. The rows have no validity/revision state.

**Impact:** Header decisions can become stale while the associated goods remain trusted. Historical goods may carry forward into a later export after header re-review.

**Fix:** Add goods-to-source revision dependencies, stale affected reviewed rows when sources change, and enforce current row validity in readiness and export. Preserve history without treating it as current approval.

**Location:** `backend/context_app/service.py:210`; `backend/context_app/exporting.py:11`.

### R06 — Saving the same row twice creates duplicates (P2)

**Reproduction:** Submit the same invoice-row body and source reference twice. Both requests return **200**, and the saved list contains two matching rows with distinct row numbers.

**Impact:** A retry or double submission can duplicate goods and valuation. There is no row-edit/delete recovery in this flow.

**Fix:** Use stable source-row identity and idempotency keys, reject conflicting duplicates, and provide explicit reviewed-row update/removal.

**Location:** `backend/api/routes.py:502`.

### R07 — Metadata-save response disagrees with readiness GET (P2)

**Reproduction:** Save a goods row, then save declaration metadata. The POST response's readiness has **zero** saved goods and reports `UNVERIFIED_GOODS`; after synchronization the dedicated GET contains the saved row and omits that blocker.

**Impact:** The UI can display incorrect blockers or lose the visible row list immediately after saving details, even though the stored data remains present.

**Fix:** Use the shared authoritative readiness function for mutation responses, including saved rows, revision and graph-pending/stale checks.

**Location:** `backend/api/routes.py:451`; `backend/context_app/exporting.py:18`.

### R08 — Multi-item XML repeats shipment-level HS, weight and packages (P1)

**Evidence:** A direct test of the actual serializer supplied two synthetic rows with different HS codes, gross weights 48/72 and four packages each. Output assigned the first shipment HS code, **120 gross mass and eight packages to both items**. The combined item totals therefore become 240 gross mass and 16 packages.

**Impact:** Multi-item declarations cannot preserve item-level classification and allocation. This affects the two-item structure of the supplied dossier even after missing-field extraction is improved.

**Fix:** Persist and verify item-specific classification, origin, weight/package allocation and valuation; serialize each item's own values and reconcile sums to the header. Do not blindly repeat shipment totals in each item.

**Evidence boundary:** This is a local serializer-level proof using explicit synthetic values, not an exported version of the original dossier.

**Location:** `backend/reasoning/cusdec_xml.py:125`.

### R09 — Overview's Ready label ignores declaration readiness (P2)

**Evidence:** The running API lists the real four-PDF dossier as processing `done`, while its readiness is blocked and export returns 422. The restored Overview code maps every `done` dossier to its green **Ready** channel. Its channel button changes only component state, so a page reload discards that choice.

**Impact:** Users can see Ready for a dossier that cannot be exported, and a local-only toggle looks like a saved review change.

**Fix:** Keep the user's design and connect the badge to authoritative readiness/review state. Separate extraction completion from declaration readiness; make changes persistent or label them as local view controls.

**Evidence boundary:** API behavior and current UI source were checked. No successful browser interaction is claimed.

**Location:** `frontend/src/components/screens/ScreenOverview.tsx:276`.

## Recommended order

1. Fix export gates, source validation and exchange-rate validation (R02–R04).
2. Add goods source/revision validity and item-level export data (R05, R08).
3. Finish the required-field extraction/manual review path (R01).
4. Add duplicate protection and consistent save responses (R06–R07).
5. Correct Overview status behavior while preserving its design (R09).

The current checks list defects; they do not fix them. Existing passing tests should be expanded with these negative cases before any public or official declaration use.

## Evidence

[Machine-readable local results](../output/verification/local-runtime-check-2026-10-18.json) contain the HTTP statuses, retained synthetic controls and serializer comparison. Detailed raw source responses and scripts remain in ignored `tmp/four-pdf-retest/`, `tmp/local_bug_probes.py` and `tmp/synthetic_export_probes.py`. Generated invalid-control XML stays in private application storage. Source files and credentials have not been published.
