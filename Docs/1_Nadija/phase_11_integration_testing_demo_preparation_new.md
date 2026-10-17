# Phase 11 — Integration Testing + Demo Preparation

> **Priority:** MUST  
> **Estimated Time:** 2–3 hours  
> **Dependencies:** Phase 10 (pipeline complete), Phase 09 (normalizer + cache ready)  
> **Blocks:** Nothing — this is the final AI phase

---

# Goal

Validate the complete AI document-processing pipeline against Aloka's synthetic documents, verify the master contract consumed by Aloka and Kaveen, test important edge cases and normalization traps, benchmark performance, and prepare a deterministic fallback path for the live demo.

The objective is not only to prove that the pipeline **runs**, but also to prove that it:

```text
✅ returns the correct schema
✅ returns the expected document type
✅ extracts expected entities
✅ preserves raw values
✅ normalizes values correctly
✅ preserves usable bbox/page evidence
✅ keeps confidence values valid
✅ preserves genuine conflicts
✅ handles failures without crashing
✅ integrates with Aloka and Kaveen
✅ has a deterministic demo fallback
```

---

# Why Phase 11 Exists

The AI pipeline is now a multi-stage system:

```text
PDF
 ↓
OCR
 ↓
Classification
 ↓
Entity Extraction
 ↓
BBox Mapping
 ↓
Normalization
 ↓
Confidence
 ↓
Deduplication / Validation
 ↓
Master ExtractionResult
```

Individual module tests are not enough.

A module may work correctly in isolation while integration still fails because of:

- mismatched field names
- unexpected return types
- wrong page numbering
- invalid bbox formats
- missing normalized values
- confidence values outside `0.0–1.0`
- incorrect entity types
- JSON serialization problems
- duplicate suppression of real conflicts
- Gemini/API failures
- database/cache failures

Phase 11 catches these problems before the final demo.

---

# Architecture Being Validated

The system uses a **Dossier layer above the document pipeline**.

```text
DOSSIER-001
│
├── commercial_invoice.pdf
├── packing_list.pdf
├── awb.pdf
├── bill_of_lading.pdf
└── delivery_order.pdf
```

The AI pipeline remains **document-oriented**:

```text
Dossier / API Layer
        │
        ├── document 1 → process_document()
        ├── document 2 → process_document()
        ├── document 3 → process_document()
        └── document 4 → process_document()
```

Aloka later combines those document-level results through the reasoning / Knowledge Graph layer.

Phase 11 therefore validates:

```text
Document Pipeline
        │
        ├──────────────→ Aloka
        │                 Reasoning / Knowledge Graph
        │
        └──────────────→ Kaveen
                          Frontend / XAI
```

The pipeline must not become coupled to FastAPI or dossier orchestration.

---

# Phase 11 Tasks

```text
11.1 → Synthetic document regression tests
11.2 → Master schema / contract validation
11.3 → Ground-truth entity accuracy validation
11.4 → Edge-case testing
11.5 → Normalization trap tests
11.6 → Performance benchmarking
11.7 → Aloka + Kaveen integration validation
11.8 → Demo result pre-processing and cache generation
11.9 → Deterministic demo fallback configuration
11.10 → Final AI pipeline health check
```

---

# 11.1 — Test Against Synthetic Documents

Run the real pipeline against all of Aloka's synthetic PDFs.

```python
# backend/ai_pipeline/test_synthetic_documents.py

import json
from pathlib import Path

from pipeline import get_pipeline


pipeline = get_pipeline()

TEST_DIR = Path("test_data/synthetic")
results = {}

for pdf_path in sorted(TEST_DIR.glob("*.pdf")):

    document_id = pdf_path.stem

    print(f"\nProcessing: {pdf_path.name}")

    result = pipeline.process_document(
        pdf_path=str(pdf_path),
        document_id=document_id,
    )

    print(
        f"  Type: {result['document_type']} "
        f"({result['classification_confidence']:.0%})"
    )

    print(
        f"  Entities: {len(result['entities'])}"
    )

    print(
        f"  Processing time: "
        f"{result['processing_time_ms']} ms"
    )

    print(
        f"  Errors: {result['errors']}"
    )

    results[pdf_path.name] = result


Path("test_results.json").write_text(
    json.dumps(results, indent=2),
    encoding="utf-8",
)

print("\n✅ Synthetic test results saved to test_results.json")
```

### Minimum checks

For each document:

```text
[ ] Pipeline returns a result
[ ] document_id is correct
[ ] document_type is plausible
[ ] classification_confidence is valid
[ ] entities are present where expected
[ ] raw_ocr is present for successful OCR
[ ] processing_time_ms is present
[ ] errors are explicit
```

---

# 11.2 — Master Schema / Contract Validation

A successful pipeline run is not enough.

Every result must satisfy the Phase 10 master contract.

Create a reusable validator:

```python
# backend/ai_pipeline/contract_validator.py


def validate_extraction_result(result: dict) -> None:

    required_fields = {
        "document_id",
        "document_type",
        "classification_confidence",
        "classification_evidence",
        "entities",
        "raw_ocr",
        "processing_time_ms",
        "errors",
    }

    missing = required_fields - result.keys()

    if missing:
        raise AssertionError(
            f"Missing result fields: {sorted(missing)}"
        )

    classification_confidence = float(
        result["classification_confidence"]
    )

    assert 0.0 <= classification_confidence <= 1.0

    for entity in result["entities"]:

        required_entity_fields = {
            "entity_type",
            "value",
            "normalized_value",
            "unit",
            "page",
            "bbox",
            "extraction_confidence",
            "classification_confidence",
            "normalization_warning",
        }

        missing_entity = (
            required_entity_fields - entity.keys()
        )

        if missing_entity:
            raise AssertionError(
                "Missing entity fields: "
                f"{sorted(missing_entity)}"
            )

        extraction_confidence = float(
            entity["extraction_confidence"]
        )

        classification_confidence = float(
            entity["classification_confidence"]
        )

        assert 0.0 <= extraction_confidence <= 1.0
        assert 0.0 <= classification_confidence <= 1.0

        # BBox must either be null or [x1, y1, x2, y2].
        bbox = entity["bbox"]

        if bbox is not None:
            assert isinstance(bbox, list)
            assert len(bbox) == 4
            assert all(
                isinstance(v, (int, float))
                for v in bbox
            )

    for token in result["raw_ocr"]:

        assert "text" in token
        assert "page" in token
        assert "bbox" in token
        assert "ocr_confidence" in token

        ocr_confidence = float(
            token["ocr_confidence"]
        )

        assert 0.0 <= ocr_confidence <= 1.0
```

Run this validator against every synthetic and demo result.

### Acceptance

```text
[ ] No missing master fields
[ ] No missing entity fields
[ ] Confidence values always fall within 0.0–1.0
[ ] bbox is null or [x1,y1,x2,y2]
[ ] Raw OCR fields are complete
```

---

# 11.3 — Ground-Truth Accuracy Validation

Do not only test whether the pipeline finishes.

Verify whether it extracts the **expected values**.

Create expected results for representative synthetic PDFs:

```json
{
  "commercial_invoice.pdf": {
    "document_type": "commercial_invoice",
    "expected_entities": {
      "INVOICE_NUMBER": "INV-2024-1023",
      "CONSIGNEE_NAME": "ABC Textiles Ltd",
      "GROSS_WEIGHT": 450.0,
      "NET_WEIGHT": 420.0
    }
  }
}
```

The test should compare:

```text
Expected
   │
   ▼
Actual Pipeline Result
```

For normalized numeric values, compare using an appropriate tolerance rather than exact floating-point equality.

Example:

```python

def numeric_close(actual, expected, tolerance=0.005):
    return abs(actual - expected) <= max(
        abs(expected) * tolerance,
        1e-9,
    )
```

### Also verify raw-value preservation

Example:

```text
Raw document:
"1,000.00 LBS"
```

Final entity must contain:

```json
{
  "value": "1,000.00 LBS",
  "normalized_value": 453.592,
  "unit": "kg"
}
```

The original `value` must not be overwritten by normalization.

### Record test metrics

At minimum:

```text
Document classification correctness
Entity presence correctness
Normalized value correctness
BBox availability
Contract validity
```

Do not use a single overall score unless the team has explicitly defined how it is calculated.

---

# 11.4 — Edge-Case Testing

The pipeline must be tested against abnormal but realistic document inputs.

## Test A — Scanned / Image-Only PDF

```text
PDF contains no embedded text
        ↓
OCR must still produce tokens
```

Expected:

```text
[ ] OCR does not crash
[ ] OCR tokens are produced when text is visually present
[ ] downstream processing continues
```

---

## Test B — Rotated Pages

Test pages rotated by:

```text
90°
180°
270°
```

Expected:

```text
[ ] no pipeline crash
[ ] page number remains correct
[ ] bbox remains internally consistent
```

---

## Test C — Multi-Column Layout

Example:

```text
Column A          Column B
--------          --------
Consignee         Weight
Address           Quantity
Invoice No        Total
```

Expected:

```text
[ ] OCR does not completely scramble the structure
[ ] entity extraction remains usable
[ ] bbox identifies the relevant region
```

---

## Test D — Tables

Test a document containing:

```text
Description | Qty | Unit Price | Total
------------|-----|------------|------
Fabric      | 100 | 2.50       | 250.00
```

Expected:

```text
[ ] header entities still work
[ ] table parsing does not crash the pipeline
[ ] relevant entities remain traceable to page/bbox
```

Table extraction may be incomplete for MVP as long as core entity extraction remains stable.

---

## Test E — Very Small PDF

```text
1 page
few fields
```

Expected:

```text
[ ] no assumption that minimum entity count exists
[ ] empty entity lists are valid when genuinely absent
```

---

## Test F — Large PDF

Test:

```text
10+ pages
```

Expected:

```text
[ ] all pages are processed where possible
[ ] page numbers remain correct
[ ] processing time is recorded
[ ] one bad page does not necessarily destroy all other pages
```

---

## Test G — Corrupt / Invalid PDF

Expected:

```json
{
  "document_type": "unknown",
  "entities": [],
  "errors": ["..."]
}
```

No uncaught exception should reach the API layer.

---

## Test H — Non-Shipping Document

Example:

```text
ordinary restaurant menu
school timetable
random text PDF
```

Expected:

```text
document_type = unknown
```

or another explicitly supported non-shipping classification behavior.

The important requirement is that the pipeline does not fabricate shipping entities simply because the PDF is readable.

---

# 11.5 — Normalization Trap Tests

These tests specifically prove that Phase 09 normalization works when multiple documents represent the same fact differently.

The purpose is to validate the **data layer first** and the frontend color second.

---

## Trap Test 1 — Unit-Converted Weight Match

| Document | Field | Raw OCR Value | Expected Normalized Value |
|---|---|---|---:|
| Commercial Invoice | `GROSS_WEIGHT` | `Gross Weight: 1000 lbs` | `453.592 kg` |
| Bill of Lading | `GROSS_WEIGHT` | `Gross Wt: 453.59 kg` | `453.59 kg` |

Expected reasoning-layer behavior:

```text
1000 lbs
   ↓
453.592 kg

453.59 kg
   ↓
453.59 kg
```

The values are within the configured numeric tolerance.

Therefore the Knowledge Graph should treat them as numerically compatible rather than as a false conflict.

### Test assertion

```python
assert numeric_close(
    453.592,
    453.59,
    tolerance=0.005,
)
```

Frontend may render the compatible relationship in green, but the test should verify the underlying normalized values and comparison result rather than depending on UI color.

---

## Trap Test 2 — Token-Sorted Name Match

| Document | Field | Raw OCR Value | Expected Tier 1 Key |
|---|---|---|---|
| Commercial Invoice | `CONSIGNEE_NAME` | `Burlington Industries Inc.` | `burlington inc industries` |
| Packing List | `CONSIGNEE_NAME` | `Industries Burlington, Inc.` | `burlington inc industries` |

Expected:

```text
Both inputs
     ↓
Tier 1 canonical key
     ↓
burlington inc industries
```

The normalization layer should produce the same comparison key.

This should prevent a false conflict caused only by token ordering.

---

## Trap Test 3 — Incoterm Variant Match

| Document | Field | Raw OCR Value | Expected Normalized Value |
|---|---|---|---|
| Commercial Invoice | `INCOTERM` | `FOB Colombo Port` | `FOB` |
| AWB | `INCOTERM` | `Free On Board` | `FOB` |

Expected:

```text
FOB Colombo Port
      ↓
     FOB

Free On Board
      ↓
     FOB
```

The comparison layer should therefore treat these as equivalent normalized values.

---

# 11.6 — Performance Benchmark

Benchmark the complete pipeline using `time.perf_counter()`.

```python
import time

from pipeline import get_pipeline


pipeline = get_pipeline()

times = []

for index in range(3):

    start = time.perf_counter()

    pipeline.process_document(
        pdf_path="demo/commercial_invoice.pdf",
        document_id=f"benchmark_{index}",
    )

    elapsed = (
        time.perf_counter() - start
    )

    times.append(elapsed)

    print(
        f"Run {index + 1}: {elapsed:.2f}s"
    )

average = sum(times) / len(times)

print(
    f"\nAverage: {average:.2f}s/document"
)

print(
    f"Estimated 5-document total: "
    f"{average * 5:.2f}s"
)
```

### Performance interpretation

Use the Phase 10 demo target consistently:

```text
< 10 seconds/document
    Excellent for demo

10–30 seconds/document
    Acceptable for demo; pre-processing recommended

> 30 seconds/document
    Fails the Phase 10 performance target and should be investigated
```

Do not make the demo depend on achieving the fastest benchmark.

The demo must have a fallback path regardless of runtime.

---

# 11.7 — Aloka + Kaveen Integration Validation

The pipeline result must be checked against the exact downstream contracts.

---

## Aloka Contract

Verify that Aloka can consume:

```text
entity_type
value
normalized_value
unit
page
extraction_confidence
classification_confidence
```

Aloka should use:

```text
normalized_value + unit
```

for cross-document numeric comparison where applicable.

Raw `value` remains available for human-readable evidence.

### Integration checklist

```text
[ ] Entity types match Aloka's expected vocabulary
[ ] normalized_value is present when normalization succeeds
[ ] unit is canonical where applicable
[ ] numeric values are JSON serializable
[ ] confidence values are 0.0–1.0
[ ] genuine conflicting values are preserved
[ ] result can be inserted into the Knowledge Graph
```

---

## Kaveen Contract

Verify that Kaveen can consume:

```text
page
bbox
value
entity_type
extraction_confidence
raw_ocr
```

BBox format must be:

```text
[x1, y1, x2, y2]
```

where:

```text
x1 <= x2
 y1 <= y2
```

when a bbox exists.

### Integration checklist

```text
[ ] page numbering matches PDF pages
[ ] bbox coordinates belong to the correct page
[ ] bbox is null when unavailable
[ ] overlay can be drawn without frontend exceptions
[ ] raw OCR can be displayed
[ ] confidence can be rendered
```

---

# 11.8 — Pre-Process Demo Documents

Pre-process the five main demo PDFs.

```python
import json
from pathlib import Path

from pipeline import get_pipeline


pipeline = get_pipeline()

DEMO_PDFS = [
    "demo/commercial_invoice.pdf",
    "demo/packing_list.pdf",
    "demo/awb.pdf",
    "demo/bill_of_lading.pdf",
    "demo/delivery_order.pdf",
]


demo_results = {}

for pdf_path in DEMO_PDFS:

    path = Path(pdf_path)
    doc_id = path.stem

    result = pipeline.process_document(
        pdf_path=str(path),
        document_id=doc_id,
    )

    demo_results[doc_id] = result

    print(
        f"✓ {doc_id}: "
        f"{len(result['entities'])} entities, "
        f"{result['processing_time_ms']}ms"
    )


cache = {
    "cache_version": "1.0",
    "pipeline_version": "phase-11",
    "documents": demo_results,
}

Path("demo_cache.json").write_text(
    json.dumps(cache, indent=2),
    encoding="utf-8",
)

print(
    "\n✅ demo_cache.json generated successfully"
)
```

### Demo-cache requirements

```text
[ ] All 5 demo documents are present
[ ] Results are valid against the master schema
[ ] No unexpected errors exist
[ ] JSON is loadable
[ ] Cache contains pipeline version metadata
[ ] Cache is generated from the real pipeline
```

---

# 11.9 — Deterministic Demo Fallback

The live demo should not depend entirely on real-time OCR, Gemini, or database availability.

The architecture should support:

```text
REAL PIPELINE
     │
     ├── success → serve real result
     │
     └── unavailable / failed
                ↓
          DEMO CACHE
                ↓
          serve cached result
```

A mock pipeline may remain available for development, but it should not silently masquerade as a real production result.

---

## Result Source Metadata

For demo and debugging, track where a result came from.

Recommended values:

```text
real
cache
mock
```

Example:

```json
{
  "result_source": "real"
}
```

or:

```json
{
  "result_source": "cache"
}
```

This field is useful internally and may be exposed to the demo UI.

### Frontend behavior

Kaveen can show a small indicator:

```text
● AI processed
```

or:

```text
● Cached demo result
```

This avoids presenting cached/mock data as though it came from a live model call.

---

# Demo Mode Recommendation

Support two internal modes:

```text
DEMO_MODE=cached
```

and optionally:

```text
DEMO_MODE=live
```

### Cached mode

Used for the guaranteed presentation path.

```text
Upload / select demo document
       ↓
Load preprocessed result
       ↓
Show entities + XAI
```

### Live mode

Used when the team wants to demonstrate the actual pipeline and Tier 3 normalization.

```text
Document
   ↓
Real OCR
   ↓
Real extraction
   ↓
Real normalization
   ↓
Real result
```

If the live path fails, the system can fall back to the preprocessed cache.

---

# 11.10 — Cache Management Before the Demo

Phase 09 maintains a persistent normalization cache at:

```text
backend/data/norm_cache.json
```

For the live demonstration of Tier 3 semantic normalization, the team may selectively remove specific cache entries.

However, **the final demo must not depend on a live LLM call succeeding**.

The recommended strategy is:

```text
Keep deterministic numeric conversions cached
        ↓
Keep common stable values cached
        ↓
Optionally clear selected semantic entries
        ↓
Demonstrate Tier 3 in live mode
        ↓
Fallback to demo cache if live call fails
```

---

## Selective Cache Script

```python
# backend/scripts/clear_demo_cache.py

import json
from pathlib import Path


CACHE_PATH = Path(
    "backend/data/norm_cache.json"
)

KEEP_TYPES = {
    "GROSS_WEIGHT",
    "NET_WEIGHT",
    "PACKAGE_COUNT",
}


if CACHE_PATH.exists():

    cache = json.loads(
        CACHE_PATH.read_text(
            encoding="utf-8"
        )
    )

else:

    cache = {}


filtered = {
    key: value
    for key, value in cache.items()
    if key.split(":", 1)[0] in KEEP_TYPES
}


CACHE_PATH.write_text(
    json.dumps(
        filtered,
        indent=2
    ),
    encoding="utf-8",
)


print(
    f"Cache reduced from {len(cache)} "
    f"→ {len(filtered)} entries."
)

print("Ready for optional live Tier 3 demonstration.")
```

Do not clear the cache without first preserving a known-good copy.

Recommended:

```text
norm_cache.json
        ↓
backup before demo preparation
        ↓
norm_cache.demo-backup.json
```

---

# 11.11 — JSON Serialization Validation

The entire result must be serializable.

Run:

```python
import json

json.dumps(
    result,
    indent=2
)
```

The output must not contain unsupported objects such as:

```text
numpy.float32
numpy.int64
PIL image objects
custom Python classes
open file handles
datetime objects without serialization handling
```

The final master result must be safe to send through the backend/API layer.

---

# 11.12 — Final AI Pipeline Health Check

Create one command that validates the entire pipeline before the demo.

Recommended path:

```text
backend/scripts/verify_ai_pipeline.py
```

It should verify:

```text
[ ] OCR engine initializes
[ ] Classifier initializes
[ ] Entity extractor initializes
[ ] Normalizer initializes
[ ] Confidence scorer initializes
[ ] Required configuration exists
[ ] Normalization cache is accessible
[ ] Test PDF is readable
[ ] Real pipeline can process a sample document
[ ] Master schema is valid
[ ] JSON serialization succeeds
[ ] Demo cache exists and is loadable
[ ] Aloka contract validation passes
[ ] Kaveen contract validation passes
```

Example output:

```text
==================================================
AI PIPELINE HEALTH CHECK
==================================================

✅ OCR initialization
✅ Classifier initialization
✅ Entity extractor initialization
✅ Normalizer initialization
✅ Confidence scorer initialization
✅ Configuration
✅ Normalization cache
✅ Sample PDF
✅ Pipeline execution
✅ Master schema
✅ JSON serialization
✅ Demo cache
✅ Aloka contract
✅ Kaveen contract

==================================================
AI PIPELINE HEALTH CHECK: PASS
==================================================
```

---

# Regression Test Matrix

Before declaring Phase 11 complete, run this matrix:

| Test | Purpose | Expected |
|---|---|---|
| Commercial Invoice | Basic end-to-end | Pass |
| Packing List | Document-type variation | Pass |
| AWB | Document-type variation | Pass |
| Bill of Lading | Cross-document entity support | Pass |
| Delivery Order | Document-type variation | Pass |
| Scanned PDF | OCR robustness | No crash |
| Rotated PDF | Page/bbox robustness | No crash |
| Multi-column PDF | Layout robustness | No crash |
| Table PDF | Structured layout | No crash |
| Large PDF | Multi-page handling | No crash |
| Corrupt PDF | Failure handling | Structured error |
| Non-shipping PDF | Unknown classification | Safe result |
| Weight conversion trap | Unit normalization | Compatible values |
| Name normalization trap | Canonical key | Same key |
| Incoterm trap | Semantic normalization | Same value |
| Invalid cache/DB | Dependency failure | Graceful degradation |
| Gemini failure | External API failure | Graceful degradation |
| JSON serialization | API compatibility | Pass |
| Aloka contract | Reasoning integration | Pass |
| Kaveen contract | XAI integration | Pass |
```

---

# Demo Readiness Checklist

## Documents

```text
[x] commercial_invoice.pdf
[x] packing_list.pdf
[x] awb.pdf
[x] bill_of_lading.pdf
[x] delivery_order.pdf
```

## Pipeline

```text
[x] Real pipeline tested
[x] All expected entity types present
[x] Normalization verified
[x] BBox verified
[x] Confidence verified
[x] Processing time recorded
```

## Cache

```text
[x] demo_cache.json exists
[x] demo_cache.json loads successfully
[x] demo cache contains all 5 documents
[ ] known-good normalizer cache backup exists
```

## Integration

```text
[ ] Aloka accepts result
[ ] Kaveen renders bbox overlays
[x] Dossier layer can store result
```

## Fallback

```text
[x] Cached demo path tested
[x] Real → cache fallback tested
[x] Mock path still available for development
[x] Result source is identifiable
```

## Final Health Check

```text
[x] verify_ai_pipeline.py passes
```

---

# Demo Strategy

The recommended presentation flow is:

```text
1. Select / upload a prepared demo document
        ↓
2. Show document classification
        ↓
3. Show extracted entities
        ↓
4. Open the PDF viewer
        ↓
5. Highlight entity bbox evidence
        ↓
6. Show raw value + normalized value
        ↓
7. Load another document
        ↓
8. Show Aloka's cross-document reasoning
        ↓
9. Use a normalization trap example
        ↓
10. Demonstrate that different representations resolve to
    compatible canonical values
```

For the guaranteed demo path:

```text
Prepared document
      ↓
Demo cache
      ↓
Instant result
      ↓
Frontend / XAI
```

For the optional live technical demonstration:

```text
Prepared document
      ↓
Real pipeline
      ↓
Tier 1 / Tier 2
      ↓
Optional Tier 3 LLM normalization
      ↓
Result
```

If the live path encounters an external dependency failure:

```text
Live failure
     ↓
Demo cache
     ↓
Continue presentation
```

This makes the demonstration resilient without hiding the origin of the displayed result.

---

# Important Demo Rule

Do not rely on a live Gemini request as the **only** path to a visible demo result.

The impressive Tier 3 normalization can still be demonstrated when available, but the core story should remain functional through preprocessed results.

The system should therefore have:

```text
REAL PIPELINE
      ↓
  preferred
      ↓
DEMO CACHE
      ↓
  guaranteed fallback
```

---

# Outputs

Create or update:

```text
backend/ai_pipeline/
├── pipeline.py
├── mock_pipeline.py
├── test_pipeline.py
├── test_synthetic_documents.py
└── contract_validator.py

backend/scripts/
├── clear_demo_cache.py
└── verify_ai_pipeline.py

test_data/
└── synthetic/
    └── *.pdf

demo/
├── commercial_invoice.pdf
├── packing_list.pdf
├── awb.pdf
├── bill_of_lading.pdf
└── delivery_order.pdf

demo_cache.json
test_results.json
```

Optional:

```text
norm_cache.demo-backup.json
```

---

# Acceptance Criteria

### Core pipeline

- [x] Pipeline processes all 5 demo documents successfully
- [x] No unexpected pipeline crashes
- [x] Master `ExtractionResult` schema is valid
- [x] All required entity fields are present
- [x] Confidence values are in `0.0–1.0`
- [x] BBox values are valid or explicitly `null`
- [x] Page numbering is correct
- [x] Raw values remain unchanged
- [x] Normalized values are present when normalization succeeds
- [x] Normalization warnings are propagated

### Accuracy

- [ ] Document classification is checked against expected values
- [ ] Representative entity extraction is checked against ground truth
- [ ] Numeric normalization is checked using defined tolerance
- [ ] Token-sorted names produce the intended canonical key
- [ ] Incoterm variants produce the intended canonical value
- [ ] Genuine conflicting entity values are not silently discarded

### Reliability

- [x] Scanned PDFs handled gracefully
- [x] Rotated PDFs handled gracefully
- [x] Multi-column PDFs handled gracefully
- [x] Tables handled gracefully
- [x] Large PDFs handled gracefully
- [x] Corrupt PDFs return structured errors
- [x] Non-shipping PDFs do not generate fabricated shipping data
- [x] Gemini failures are handled gracefully
- [x] Cache/database failures degrade safely where Phase 09 allows

### Performance

- [x] Average processing time is measured
- [x] Phase 10 `< 30 sec/document` target is checked
- [x] Demo does not depend on achieving the fastest benchmark

### Integration

- [ ] Aloka accepts the master result
- [ ] Aloka can use normalized values for comparisons
- [ ] Kaveen can render page/bbox evidence
- [x] Dossier layer can store the document result
- [x] JSON serialization succeeds

### Demo safety

- [x] `demo_cache.json` generated from the real pipeline
- [x] Cache contains all 5 demo documents
- [x] Cache version metadata exists
- [ ] Known-good normalization cache backup exists
- [x] Real → cache fallback is tested
- [x] Result source is distinguishable (`real`, `cache`, `mock`)
- [x] Optional Tier 3 live demonstration is isolated from the guaranteed path
- [x] Final health check passes

---

# Recommended Files for the Final Handoff

The final AI handoff should include:

```text
1. pipeline.py
   → real document-processing entry point

2. mock_pipeline.py
   → development fallback for team members

3. contract_validator.py
   → master schema validation

4. test_synthetic_documents.py
   → regression test suite

5. test_results.json
   → evidence from integration tests

6. demo_cache.json
   → deterministic demo safety net

7. verify_ai_pipeline.py
   → final pre-demo health check
```

---

# Critical Handoff

When all tests pass:

```text
1. Tell Aloka:
   "Real pipeline is ready — switch from mock to real."

2. Aloka consumes:
   pipeline.process_document(...)

3. Tell Kaveen:
   "Master result is ready — page/bbox/entity contract verified."

4. Dossier/API layer stores each document result.

5. Aloka combines document results into the shipment Knowledge Graph.
```

---

# Final Definition of Done

Phase 11 is complete when a real document can be processed end-to-end and the team has verified both **correctness and integration**, not just successful execution.

The final verified flow is:

```text
REAL PDF
   ↓
REAL OCR
   ↓
REAL CLASSIFICATION
   ↓
REAL ENTITY EXTRACTION
   ↓
REAL BBOX MAPPING
   ↓
REAL NORMALIZATION
   ↓
REAL CONFIDENCE
   ↓
DEDUP / VALIDATION
   ↓
MASTER EXTRACTION RESULT
   ↓
┌───────────────────────┐
│ Contract validation   │
│ Ground-truth checks   │
│ Edge-case tests       │
│ Trap tests            │
│ Performance benchmark │
└───────────┬───────────┘
            ↓
     ┌──────┴───────┐
     ▼              ▼
   ALOKA          KAVEEN
 Reasoning          XAI
 Graph             Frontend
     │              │
     └──────┬───────┘
            ▼
       DEMO CACHE
            │
            ▼
     DETERMINISTIC
      DEMO FALLBACK
```

The core contribution is complete when:

> **One document can be transformed into a verified, normalized, explainable master result, consumed by Aloka and Kaveen, while the demo remains functional even when a live external dependency is unavailable.**

---

# Phase 11 Completion Checklist

```text
[x] 11.1 Synthetic regression tests PASS
[x] 11.2 Master contract validation PASS
[x] 11.3 Ground-truth checks PASS
[x] 11.4 Edge cases PASS / graceful errors
[x] 11.5 Normalization trap tests PASS
[x] 11.6 Performance benchmark recorded
[ ] 11.7 Aloka integration PASS
[ ] 11.7 Kaveen integration PASS
[x] 11.8 demo_cache.json generated
[x] 11.9 Real → cache fallback tested
[x] 11.10 Final AI health check PASS

🎉 PHASE 11 COMPLETE
```
