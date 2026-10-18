# Four-PDF application verification

**Current result — 18 October 2026:** The nine subsequent runtime findings have also been fixed. The actual four-PDF flow now completes through source review and a reconciled two-item test export. See [NINE_FIXES_VERIFICATION.md](NINE_FIXES_VERIFICATION.md). Earlier observations below are preserved as history.

**Follow-up after fixes — 18 October 2026:** The new running build correctly classifies all four documents and extracts 27 assertions plus two rows each from invoice, packing list and worksheet. Original upload/extraction failures below are retained as history. The full application still has nine confirmed findings, including export validation defects and four missing export-required fields. See [LOCAL_RUNTIME_BUG_REPORT.md](LOCAL_RUNTIME_BUG_REPORT.md) for the current result. The new full selected suite passed 55 tests with one skipped.

**Date:** 18 October 2026 (Asia/Colombo)  
**Initial pre-fix verdict: NOT fully okay. Upload and protected file delivery passed; extraction accuracy failed.**

## What was actually tested

The four original files in [TEST FILE](TEST%20FILE/) were submitted together as one real upload through the running application's `http://localhost:8080/api` proxy, using the existing local account. No synthetic/demo upload, extraction substitutes, source edits or paid model calls were used. Original PDFs remain unchanged. The user's restored Overview design was not changed.

Test dossier: `6fe1e637-1cb0-408b-8956-354c09802455`. It is in the existing account's workspace, under the default title **Uploaded dossier**.

All four PDFs are one-page digital documents with readable text. Their rendered pages were visually inspected and compared with actual extraction responses. This is a check of the app's default digital parser, not a scanned-OCR test.

| Boundary | Status | Observed evidence |
|---|---|---|
| Local services | Pass | API, PostgreSQL and FalkorDB healthy; frontend running. |
| Authentication | Pass | Actual session/CSRF login returned 200; logout returned 200. |
| Four-file upload | Pass | POST `/api/upload` returned 202 with four document IDs. |
| Background processing | Pass for job completion | Status reached `done`, four of four documents processed. This does not establish correct extraction. |
| Protected source PDFs | Pass | Four authenticated downloads returned 200, with SHA-256 hashes identical to original inputs. |
| Extraction accuracy | **Fail** | Only five assertions across all four files; zero goods rows. Important visible values were omitted and one document type is wrong. |
| Downstream review/graph/agent/export | **Not signed off** | Verification stopped at the failed extraction boundary; downstream semantic correctness cannot be established from incomplete inputs. |
| Browser click-through / visual app rendering | Unverified | No browser walkthrough was performed in this check. The earlier saved/managed browser policy denial remains unresolved. |

## Findings by input

| Source | Expected from the visible PDF | Actual application result |
|---|---|---|
| [Air Waybill](TEST%20FILE/Air%20Waybill.pdf) | AWB `003-78419204`, eight packages, gross 120 kg, parties and USD. Chargeable 142 kg is distinct from gross weight. | Correct `awb` type; only currency USD extracted. AWB number, package count, gross weight and parties missing. |
| [Commercial Invoice](TEST%20FILE/Commercial%20Invoice%20%281%29.pdf) | Invoice `NPE-2026-9410`, CIF total USD 15,600, CIF delivery terms, shipper/consignee and two goods rows: 100 encoders at USD 75 and 20 PLCs at USD 350. | Correct type; invoice number and currency extracted. Invoice total, delivery terms, parties and both goods rows missing. |
| [Customs worksheet](TEST%20FILE/Customs%20Declaration%20Entry%20Worksheet.pdf) | A customs entry worksheet, not a commercial invoice; separate cage fields and two item allocations. It must be recognized separately or explicitly unsupported. | **Incorrect `commercial_invoice` classification**; only total amount 15,600 extracted. No cage/item rows. This can misattribute declaration evidence as invoice evidence. |
| [Packing List](TEST%20FILE/Export%20Packing%20List.pdf) | Eight cartons, net 100 kg, gross 120 kg, consignee and two packing rows. | Correct `packing_list` type; only package count eight extracted. Net/gross mass, consignee and rows missing. |

A processing result of `done` means the extraction process returned. Here it does **not** mean the dossier is complete or ready to declare. Parser warnings disclose narrow label/pipe-table support, but all four document `errors` lists are empty despite the omissions.

## Cause and required changes

1. **Classification uses body keyword presence rather than the document's primary heading.** Supporting-document references in the customs worksheet trigger commercial-invoice classification. Add heading-aware classification, a distinct worksheet/supporting category or an explicit unsupported state, and regression coverage for cross-references.
2. **Field patterns cover too few real label/layout variants.** Examples missed include `Gross Wt`, `Total Gross Mass (Cage 35)`, `Total Net Mass (Cage 38)`, `Incoterms`, `TOTAL CIF COLOMBO`, and party names below section headings. Add layout-aware extraction with page/box provenance; distinguish gross, net, chargeable weight and item totals. Do not hardcode these sample values.
3. **Only pipe-delimited goods rows are supported by the default parser.** These PDFs have normal column tables. Implement coordinate/table extraction and reconcile row counts, quantities, currencies and totals against source headers.
4. **Quality acceptance is too weak.** Missing required fields or unsupported layouts need explicit review-needed/partial status per document and dossier. Preserve the difference between processing completion and extraction completeness.

First add representative regression assertions for these four unchanged files and layout variants, then fix extraction. Re-upload to a new dossier and repeat the source comparison before testing graph evidence, reviewer proposals, corrections, readiness and export. A future live agent test should stay within the existing spending ceiling; this check incurred **zero OpenAI calls**.

## Evidence and scope

[Machine-readable comparison](../output/verification/four-pdf-check.json) records source hashes, expected versus extracted fields, type mismatch and download results. Private raw responses and the repeatable HTTP script are under ignored `tmp/four-pdf-check/` and `tmp/test_four_pdfs.py`; they contain extracted source details and are not included in the public source package.

The earlier 48-test result used its documented synthetic/contract cases. It does not establish accuracy on these more realistic PDFs. No source-code fix, fake extraction replacement, human approval, export, competition submission or UI redesign was performed during this verification.
