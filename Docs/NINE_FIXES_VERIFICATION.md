# Verification of the nine runtime fixes

**Date:** 18 October 2026, Asia/Colombo  
**Result:** All nine findings in `LOCAL_RUNTIME_BUG_REPORT.md` have been addressed. The rebuilt local application passed the actual four-PDF upload, processing, source review, goods verification and XML download flow. This sign-off covers those fixes and the tested input flow, not every future roadmap item or arbitrary scanned layout.

## What passed

- Full selected suite: **62 passed, 1 skipped**, one deprecation warning, 98.54 seconds. Seven new tests exercise the supplied layouts and full source-to-export behavior; a follow-up source-allocation/HS/origin/currency rejection test also passed in 7.65 seconds.
- React/TypeScript production build and both container builds passed. Lint completes with existing effect/fast-refresh warnings; the large main JavaScript chunk remains a performance warning.
- Actual HTTP through `localhost:8080/api`: four original PDFs uploaded and processed, original-download hashes preserved, graph synchronized, review decisions persisted, two invoice items verified, export created and downloaded.
- The output has item HS codes `90318000` / `85371090`, gross masses 48 / 72 kg, net masses 40 / 60 kg, and four packages per item. FOB USD 14,500 plus sourced freight USD 950 and insurance USD 150 is apportioned to CIF USD 8,068.97 / 7,531.03, totaling USD 15,600. Item statistical values use Decimal arithmetic and the test exchange rate.
- Negative runtime checks rejected invented goods references and invalid rates. A partial goods review could not export, repeat reviews did not duplicate rows or change the revision, and a no-change metadata save returned the same authoritative readiness as GET.
- Graph integration tests show that changing the packing source finds the dependent `GoodsReview` nodes, makes both affected reviews stale and blocks export; re-review restores readiness. Removing/restoring a review is auditable.
- Five ordered migrations are applied. Migration 5 preserves old rows as unverified and marks earlier artifacts stale so previous weak validation cannot silently carry forward.
- No paid model calls or external declaration submissions were made. Credentials and private backups are excluded from the source package.

The API was restarted after the successful flow: a new login still found both goods reviews current, readiness allowed, and the identical export content hash. The source archive was extracted into a fresh folder; frontend installation reported zero vulnerabilities, production build passed, and backend imports passed with packaged dependencies and networking disabled. These are same-host checks, not an independent clean-machine audit.

## Resolution matrix

| Finding | Resolution | Verification |
|---|---|---|
| R01 Missing origin, port and HS fields | Extract source-linked port/origin values; retain HS per invoice item rather than requiring one HS for a mixed shipment. | Original four-PDF flow has no missing source-field blockers; both item HS codes reach XML. |
| R02 Incomplete or inconsistent goods allowed export | Require all current invoice rows, validate source amounts and reconcile quantity/value, weight and package allocations. | Partial review returns 422 on export; completed two-row review passes and totals reconcile. |
| R03 Invented goods reference | Bind each review to a current invoice document/revision/row and its packing dependencies. | Nonexistent reference and source-value mismatches return 422. |
| R04 Invalid exchange rate | Shared finite, positive Decimal validation at save, readiness and serialization; no empty-value fallback. | Invalid text, zero, negative, NaN and infinity rejected; invalid persisted legacy rate blocks export. |
| R05 Goods remain verified after source change | Persist revision validity and project GoodsReview dependencies into FalkorDB; source impact stales affected rows. | Packing correction blocks export and re-review succeeds; history is retained. |
| R06 Duplicate rows | Unique shipment/source-row identity plus locked idempotent saving; explicit review removal and update. | Repeated body retains one row and unchanged revision. |
| R07 Inconsistent metadata save response | Use the same authoritative readiness function for mutation responses and GET, including saved goods and graph status. | Two saved rows remain in the response; no-change POST equals GET. Graph-pending is explicitly shown during actual changes. |
| R08 Repeated shipment allocation in every XML item | Serialize each reviewed item's HS, origin, packages, weights and allocated invoice amount. | Two-item XML has distinct classification and sums exactly to the shipment totals. |
| R09 False Overview Ready / temporary status switch | Read the server's export readiness; the badge opens the saved readiness screen instead of changing local-only state. | API changes from blocked to ready only after real review. Original Overview layout, styling and animations retained. |

## Use the working sample

1. Open `http://localhost:8080` and use your existing local account.
2. Find **QA validated four-PDF example (automated test review)** in Overview. Its dossier ID is `04c681ac-cbf6-444a-8dbc-8a0c1998566c`.
3. Open Context Agent for evidence/history, or click the readiness badge to open declaration readiness.
4. Goods review now shows each source item, its current verification state, classification, origin and allocation. Current reviews can be updated or removed; changing a source requires re-review.
5. Download the reviewed XML from the app or use [the test output](../output/release/TEST_ONLY_Validated_Four_PDF_Example.xml).

The sample approvals and profile were created by an automated QA script. The declarant is explicitly **AUTOMATED QA - NOT FOR FILING**. It is a demonstration artifact, not human approval or an official declaration.

Older dossiers retain their historical extraction and review state. Upload the originals as a new dossier to use the improved parser; old extracted evidence is not silently rewritten.

## Evidence and limits

- [Actual packaged-flow results](../output/verification/nine-fixes-packaged-flow.json).
- Regression sources: `backend/tests/test_nine_runtime_fixes.py`, revised export fixtures and the existing security/domain/graph tests.
- The previous bug report and pre-fix test evidence remain as historical records; their findings are closed by this report within the stated scope.
- This original sign-off used API, worker, graph, database, build and XML checks. Subsequent Chrome checks verified upload, source preview, review, export, graph, batch and audit. The remaining revised upload/tariff browser coverage and access limitation are documented in [UI verification](UI_VERIFICATION_REPORT.md); do not infer a complete browser pass from the original report.
- General scanned OCR, arbitrary table layouts, calibrated geometry/confidence, maintained tariff advice, production load/security certification, official ASYCUDA acceptance and competition submission remain outside this sign-off. The retained work plan still documents those broader items.
