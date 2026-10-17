# Full Project Architecture — AI Shipping Document Intelligence System

> **Purpose:** Complete technical architecture for the document-processing and reasoning platform.
>
> **Core principle:** Keep document processing, dossier orchestration, reasoning, storage, and frontend/XAI concerns separated while connecting them through stable contracts.

---

# 1. System Overview

The project is an AI-powered shipping-document intelligence system.

A user uploads a set of shipping documents as a **Dossier**. Each document is processed independently by the AI pipeline. The pipeline converts an unstructured PDF into a structured, normalized, confidence-aware and bbox-aware `ExtractionResult`. Aloka's reasoning engine then combines results from multiple documents into a shipment-level Knowledge Graph and detects relationships, matches, inconsistencies and conflicts. Kaveen's frontend/XAI layer visualizes the extracted information and traces results back to the original PDF evidence.

The main processing chain is:

```text
User
 │
 ▼
Frontend
 │
 ▼
FastAPI / Backend API
 │
 ├─────────────────────────────┐
 ▼                             ▼
Dossier Service             File Storage
 │                             │
 ├── document 1                 │
 ├── document 2                 │
 ├── document 3                 │
 └── document N                 │
 │
 ▼
AI Pipeline
 │
 ├── OCR
 ├── Classification
 ├── Entity Extraction
 ├── BBox Mapping
 ├── Normalization
 ├── Confidence
 ├── Deduplication / Validation
 └── Master ExtractionResult
 │
 ├───────────────────────┐
 ▼                       ▼
Aloka                   Kaveen
Reasoning               Frontend / XAI
 │                       │
 ▼                       ▼
Knowledge Graph         PDF Evidence Viewer
 │                       └── bbox overlays
 ├── Cross-document         └── confidence UI
 │   matching
 ├── Conflict detection
 ├── Consistency checks
 └── Higher-level reasoning
```

---

# 2. High-Level Architecture

```text
┌─────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                               │
│                                                                     │
│ Upload Dossier | Document List | PDF Viewer | XAI | Results        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTPS / JSON
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                              FASTAPI                                │
│                                                                     │
│ Auth / Upload / Dossier / Document / Result / Health / Demo APIs  │
└──────────────┬──────────────────────────┬──────────────────────────┘
               │                          │
               ▼                          ▼
┌──────────────────────────┐    ┌────────────────────────────────────┐
│      DOSSIER SERVICE     │    │            PERSISTENCE             │
│                          │    │                                    │
│ Creates dossier_id       │    │ PostgreSQL                         │
│ Creates document_id      │    │ Dossier metadata                   │
│ Tracks processing state  │    │ Document metadata                  │
│ Orchestrates documents   │    │ Processing records                 │
└─────────────┬────────────┘    │ Normalization cache                │
              │                 └────────────────────────────────────┘
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         AI PIPELINE                                 │
│                                                                     │
│  PDF → OCR → Classifier → Extractor → BBox → Normalizer            │
│                                  → Confidence → Dedup/Validation     │
│                                  → Master ExtractionResult           │
└───────┬─────────────────────────────────────────┬───────────────────┘
        │                                         │
        ▼                                         ▼
┌──────────────────────────┐          ┌──────────────────────────────┐
│        ALOKA             │          │           KAVEEN              │
│                          │          │                              │
│ Reasoning Engine         │          │ Frontend / XAI Layer         │
│ Knowledge Graph          │          │ PDF Evidence                 │
│ Cross-document matching  │          │ BBox overlays                │
│ Conflict detection       │          │ Entity/confidence display    │
└──────────────────────────┘          └──────────────────────────────┘
```

---

# 3. Core Architecture Principles

## 3.1 Document-oriented AI pipeline

The AI pipeline processes **one document at a time**.

```python
result = pipeline.process_document(
    pdf_path="/uploads/invoice.pdf",
    document_id="doc_001"
)
```

The AI pipeline does not need to understand the entire dossier.

## 3.2 Dossier above document pipeline

A dossier groups related documents.

```text
DOSSIER-001
│
├── doc_001 → commercial_invoice.pdf
├── doc_002 → packing_list.pdf
├── doc_003 → awb.pdf
├── doc_004 → bill_of_lading.pdf
└── doc_005 → delivery_order.pdf
```

The dossier/upload layer owns `dossier_id` and `document_id` creation.

## 3.3 Stable master contract

Every downstream component consumes the same `ExtractionResult` contract.

This prevents Aloka and Kaveen from depending on internal OCR, Gemini, normalization or cache implementation details.

## 3.4 Preserve raw evidence

Raw OCR values are never overwritten by normalized values.

```text
raw value = what the document says
normalized value = what the system uses for comparison
bbox = where the evidence came from
```

## 3.5 Fail gracefully

An individual document or stage should not unnecessarily crash the API layer.

Errors are recorded in the result contract.

## 3.6 Explainability by construction

XAI is not added at the end. Evidence is preserved from OCR through entity extraction:

```text
OCR text
 +
OCR bbox
 +
OCR confidence
 ↓
Entity
 +
entity bbox
 +
extraction confidence
 ↓
Frontend evidence visualization
```

---

# 4. Component Map

```text
backend/
│
├── api/
│   ├── routes/
│   │   ├── upload
│   │   ├── dossier
│   │   ├── document
│   │   ├── results
│   │   └── health
│   └── dependencies/
│
├── services/
│   ├── dossier_service
│   ├── document_service
│   ├── storage_service
│   └── processing_service
│
├── ai_pipeline/
│   ├── ocr_engine.py
│   ├── classifier.py
│   ├── entity_extractor.py
│   ├── confidence.py
│   ├── normalizer.py
│   ├── pipeline.py
│   ├── mock_pipeline.py
│   └── test_pipeline.py
│
├── reasoning/
│   ├── knowledge_graph.py
│   ├── conflict_detection.py
│   ├── matching.py
│   └── reasoning_engine.py
│
├── scripts/
│   ├── verify_ai_pipeline.py
│   ├── clear_demo_cache.py
│   └── benchmark_pipeline.py
│
├── data/
│   └── norm_cache.json            # development/demo fallback cache if used
│
├── demo/
│   ├── commercial_invoice.pdf
│   ├── packing_list.pdf
│   ├── awb.pdf
│   ├── bill_of_lading.pdf
│   └── delivery_order.pdf
│
└── test_data/
    ├── synthetic/
    ├── edge_cases/
    └── traps/
```

> Exact directory names can differ from the repository, but the architectural responsibilities should remain separated.

---

# 5. End-to-End Data Flow

```text
                         USER
                          │
                          │ Upload documents
                          ▼
                    ┌─────────────┐
                    │   FRONTEND  │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  FASTAPI    │
                    └──────┬──────┘
                           │
               creates dossier/document IDs
                           │
            ┌──────────────┴──────────────┐
            ▼                             ▼
     ┌──────────────┐              ┌──────────────┐
     │ File Storage │              │ PostgreSQL   │
     │ PDFs         │              │ metadata     │
     └──────┬───────┘              └──────┬───────┘
            │                             │
            └──────────────┬──────────────┘
                           ▼
                 process_document()
                           │
                           ▼
                         OCR
                           │
                           ▼
                    Classification
                           │
                           ▼
                    Page Extraction
                           │
                           ▼
                     BBox Mapping
                           │
                           ▼
                      Normalization
                           │
                           ▼
                    Confidence Score
                           │
                           ▼
                 Dedup / Validation
                           │
                           ▼
                  ExtractionResult
                    /            \
                   /              \
                  ▼                ▼
              PostgreSQL        Kaveen
                  │                │
                  ▼                ▼
               Aloka           PDF/XAI
                  │
                  ▼
           Knowledge Graph
                  │
                  ▼
        Cross-document reasoning
```

---

# 6. Dossier Layer

The Dossier layer is responsible for document grouping and orchestration.

## Responsibilities

```text
✅ Create dossier
✅ Create document records
✅ Generate IDs
✅ Store file references
✅ Track document status
✅ Invoke document pipeline
✅ Persist results
✅ Hand document results to reasoning layer
```

## It should not own

```text
❌ OCR internals
❌ Gemini extraction prompts
❌ Entity normalization algorithms
❌ BBox mapping algorithms
❌ Knowledge graph reasoning logic
```

## Example

```python
for document in dossier.documents:
    result = pipeline.process_document(
        pdf_path=document.path,
        document_id=document.id,
    )

    save_result(result)
```

---

# 7. Document Lifecycle

A document can move through states such as:

```text
UPLOADED
   ↓
QUEUED
   ↓
PROCESSING
   ↓
OCR
   ↓
CLASSIFYING
   ↓
EXTRACTING
   ↓
NORMALIZING
   ↓
VALIDATING
   ↓
COMPLETED
```

Failure path:

```text
any stage
   ↓
FAILED
```

The pipeline records technical errors in `errors[]`; the service layer can map those errors to document/dossier status.

---

# 8. AI Pipeline Architecture — Phase 10

The AI pipeline is the master document-processing orchestrator.

```text
PDF
 │
 ▼
┌─────────────────┐
│ 1. OCR          │
└────────┬────────┘
         │ text + bbox + confidence
         ▼
┌─────────────────┐
│ 2. Classification│
└────────┬────────┘
         │ document type + evidence
         ▼
┌─────────────────┐
│ 3. Extraction   │
└────────┬────────┘
         │ raw entities
         ▼
┌─────────────────┐
│ 4. BBox Mapping  │
└────────┬────────┘
         │ entity + evidence location
         ▼
┌─────────────────┐
│ 5. Normalization│
└────────┬────────┘
         │ canonical values + units
         ▼
┌─────────────────┐
│ 6. Confidence   │
└────────┬────────┘
         │ confidence metadata
         ▼
┌─────────────────┐
│ 7. Dedup/Valid. │
└────────┬────────┘
         │ clean entities
         ▼
┌─────────────────┐
│ 8. Master Result│
└─────────────────┘
```

Single entry point:

```python
pipeline.process_document(pdf_path, document_id)
```

---

# 9. Phase 02 — OCR Engine

The OCR engine converts PDF pages into structured OCR output.

## Input

```text
PDF path
```

## Output

```text
OcrOutput
│
├── file_path
├── total_pages
└── pages[]
    ├── page_number
    ├── width
    ├── height
    └── tokens[]
        ├── text
        ├── page
        ├── bbox
        └── confidence
```

Conceptually:

```text
PDF page
   ↓
PaddleOCR / OCR engine
   ↓
text regions
   +
bounding boxes
   +
OCR confidence
```

## Why OCR is important

OCR provides the raw evidence layer required for:

- entity extraction
- classification
- bbox mapping
- Layer 1 XAI
- confidence calculation

---

# 10. Phase 03 — Document Classification

The classifier identifies which shipping-document type is being processed.

Example:

```json
{
  "document_type": "commercial_invoice",
  "confidence": 0.97,
  "evidence": [
    "invoice",
    "unit price",
    "total amount"
  ],
  "all_scores": {}
}
```

Classification is performed from OCR-derived document content and can use rule/keyword logic plus model-based fallback depending on the implementation.

Possible document types include:

```text
commercial_invoice
packing_list
awb
bill_of_lading
delivery_order
unknown
```

---

# 11. Entity Extraction

The entity extractor receives:

```text
Page image
+
Document type
+
OCR tokens
```

Conceptual flow:

```text
Page Image ──────────────┐
                         │
OCR Tokens ──────────────┼──► Entity Extractor
                         │        │
Document Type ───────────┘        ▼
                            Raw Entity JSON
```

The extractor can use Gemini Vision or the project's configured extraction model.

## Extractor responsibilities

```text
✅ Identify entity type
✅ Preserve raw value
✅ Produce extraction confidence
✅ Map entity to OCR evidence/bbox
✅ Handle multi-token values
✅ Return empty list when appropriate
✅ Fail safely
```

## Extractor does NOT normalize

```text
❌ unit conversion
❌ date canonicalization
❌ identifier canonicalization
❌ semantic name normalization
```

Those belong to Phase 09.

---

# 12. BBox Mapping / Layer 1 XAI

The system retains spatial evidence for each entity.

Canonical bbox format:

```text
[x1, y1, x2, y2]
```

Example:

```json
{
  "entity_type": "CONSIGNEE_NAME",
  "value": "ABC Textiles Ltd",
  "page": 1,
  "bbox": [50, 100, 300, 130]
}
```

## Multi-token example

OCR might return:

```text
ABC        [50,100,100,115]
Textiles   [105,100,200,115]
Ltd        [205,100,240,115]
```

The entity bbox can cover the complete phrase:

```text
[50,100,240,115]
```

If a reliable bbox cannot be determined:

```json
"bbox": null
```

Never fabricate coordinates.

---

# 13. Phase 09 — Normalization Architecture

Normalization transforms heterogeneous document values into canonical representations for downstream comparison.

```text
RAW VALUE
   │
   ▼
Entity-Type Router
   │
   ├──────────────────────────┐
   │                          │
   ▼                          ▼
Deterministic              Semantic
Entities                   Entities
   │                          │
   ▼                          ▼
Python Rules             Tier 1 Key
   │                          │
   │                          ▼
   │                     PostgreSQL/cache
   │                          │
   │                    ┌─────┴─────┐
   │                    │           │
   │                   HIT         MISS
   │                    │           │
   │                    │           ▼
   │                    │        Gemini
   │                    │           │
   │                    │           ▼
   │                    │        Save cache
   │                    │
   └────────────────────┴───────────┘
                    │
                    ▼
            Normalized Entity
```

## Raw-value preservation

Example:

```json
{
  "entity_type": "GROSS_WEIGHT",
  "value": "1,000.00 LBS",
  "normalized_value": 453.592,
  "unit": "kg",
  "normalization_warning": false
}
```

The string `"1,000.00 LBS"` remains unchanged.

---

# 14. Normalization Tiers

## Tier 1 — Deterministic normalization

Use Python rules for entities with deterministic transformations.

Examples:

```text
weights
unit conversions
package counts
amount parsing
known formats
```

These should not need an LLM call.

## Tier 2 — Cache lookup

Before calling Gemini for semantic normalization, check the persistent cache.

Example canonical key:

```text
ENTITY_TYPE:normalized_input
```

Example:

```text
CONSIGNEE_NAME:burlington inc industries
```

## Tier 3 — LLM fallback

For semantic entities not found in the cache:

```text
Tier 1
  ↓
Tier 2 cache miss
  ↓
Gemini
  ↓
canonical result
  ↓
save cache
```

---

# 15. Normalization Output Contract

A normalization result should conceptually contain:

```python
{
    "normalized_value": ..., 
    "unit": ...,
    "warn": False,
}
```

Possible outcomes:

### Successful deterministic conversion

```text
value = "1000 lbs"
normalized_value = 453.592
unit = "kg"
warn = false
```

### Successful semantic normalization

```text
value = "FOB Colombo Port"
normalized_value = "FOB"
unit = None
warn = false
```

### Unable to normalize

```text
value = "unknown expression"
normalized_value = None
unit = None
warn = true
```

---

# 16. Phase 08 — Confidence Architecture

Confidence is multi-dimensional.

```text
OCR confidence
       │
       ├── text reading reliability
       │
       ▼
BBox / mapping quality
       │
       ▼
Extraction confidence

Classification confidence
       │
       ▼
Document-type reliability
```

Each entity carries at least:

```text
extraction_confidence
classification_confidence
```

Values should be normalized to:

```text
0.0 – 1.0
```

Example:

```json
{
  "extraction_confidence": 0.94,
  "classification_confidence": 0.97
}
```

The actual confidence-scoring method must match the project's Phase 08 implementation.

---

# 17. Entity Deduplication and Validation

After extraction and normalization, identical accidental duplicates can be controlled.

A candidate deduplication identity can use:

```text
entity_type + normalized_value
```

Example:

```text
INVOICE_NUMBER + INV1023
```

## Important conflict rule

Do not silently merge different values.

```text
GROSS_WEIGHT = 450 kg
GROSS_WEIGHT = 448 kg
```

These are not duplicates. They are potentially conflicting observations and should remain available to Aloka's reasoning layer.

---

# 18. Master `ExtractionResult` Contract

The document pipeline returns one master result:

```json
{
  "document_id": "doc_001",
  "document_type": "commercial_invoice",
  "classification_confidence": 0.97,
  "classification_evidence": [
    "invoice",
    "unit price",
    "total amount"
  ],
  "entities": [
    {
      "entity_type": "GROSS_WEIGHT",
      "value": "450.00 KG",
      "normalized_value": 450.0,
      "unit": "kg",
      "page": 2,
      "bbox": [120, 240, 410, 290],
      "extraction_confidence": 0.94,
      "classification_confidence": 0.97,
      "normalization_warning": false
    }
  ],
  "raw_ocr": [
    {
      "text": "Gross Weight: 450.00 KG",
      "page": 2,
      "bbox": [100, 230, 430, 300],
      "ocr_confidence": 0.98
    }
  ],
  "processing_time_ms": 3200,
  "errors": []
}
```

---

# 19. Entity Contract

Every successfully extracted entity should contain:

```text
entity_type
value
normalized_value
unit
page
bbox
extraction_confidence
classification_confidence
normalization_warning
```

## Rules

### Raw value

Never overwrite.

### Normalized value

Canonical value used by reasoning/comparison where available.

### Unit

Canonical unit where applicable.

### Page

1-based PDF page number.

### BBox

`[x1, y1, x2, y2]` or `null`.

### Confidence

Numeric values between `0.0` and `1.0`.

### Warning

Signals unsuccessful or uncertain normalization.

---

# 20. Raw OCR Contract

Each raw OCR item should contain:

```text
text
page
bbox
ocr_confidence
```

Example:

```json
{
  "text": "Gross Weight: 450.00 KG",
  "page": 2,
  "bbox": [100, 230, 430, 300],
  "ocr_confidence": 0.98
}
```

This is the evidence layer used for visual traceability.

---

# 21. Error Handling Architecture

The pipeline should prefer structured errors over uncaught exceptions.

```text
                     Pipeline
                         │
       ┌─────────────────┼──────────────────┐
       │                 │                  │
       ▼                 ▼                  ▼
      OCR           Classification      Extraction
       │                 │                  │
      fail              fail               fail
       │                 │                  │
       ▼                 ▼                  ▼
 return result       record error       record error
```

## OCR failure

OCR is foundational.

```text
OCR fails
 → return error result
```

## Classification failure

When possible:

```text
classification = unknown
confidence = 0.0
evidence = []
```

and continue where meaningful.

## Extraction failure

Record the page-specific error and continue remaining pages where possible.

## Normalization failure

Do not crash the entire document.

```json
{
  "normalized_value": null,
  "unit": null,
  "normalization_warning": true
}
```

## Database/cache failure

Normalization should degrade gracefully when possible instead of destroying the whole pipeline.

---

# 22. Processing Time

Use a high-resolution timer:

```python
start_time = time.perf_counter()

# process document

processing_time_ms = int(
    (time.perf_counter() - start_time) * 1000
)
```

Demo performance target:

```text
< 30 seconds / document
```

Suggested interpretation:

```text
< 10 sec       excellent
10–30 sec      acceptable for demo
> 30 sec       needs optimization or cache/pre-processing
```

---

# 23. Singleton / Model Reuse

Heavy components should not be reconstructed unnecessarily for each request.

```text
Application instance
       │
       ▼
   AIPipeline
       ├── OcrEngine
       ├── DocumentClassifier
       ├── EntityExtractor
       ├── EntityNormalizer
       └── ConfidenceScorer
```

The pipeline factory can reuse the same initialized components:

```python
_pipeline_instance = None


def get_pipeline():
    global _pipeline_instance

    if _pipeline_instance is None:
        _pipeline_instance = AIPipeline()

    return _pipeline_instance
```

This avoids unnecessary model initialization when supported by the runtime.

---

# 24. Aloka — Reasoning Engine Architecture

Aloka operates at the **multi-document reasoning layer**.

```text
Document 1 ExtractionResult
            │
Document 2 ExtractionResult
            │
Document 3 ExtractionResult
            │
Document N ExtractionResult
            │
            ▼
      Entity Aggregation
            │
            ▼
     Knowledge Graph
            │
     ┌──────┼────────┐
     ▼      ▼        ▼
   Match  Conflict  Relation
     │      │        │
     └──────┼────────┘
            ▼
        Reasoning
            │
            ▼
      Shipment-level
         findings
```

---

# 25. Why the Knowledge Graph Uses Normalized Values

Suppose three documents contain:

```text
Invoice:
1000 lbs

Bill of Lading:
453.59 kg

Packing List:
453.6 KG
```

Normalization gives:

```text
1000 lbs → 453.592 kg
453.59 kg → 453.59 kg
453.6 KG → 453.6 kg
```

Aloka can then compare numeric values using configured tolerance rules.

This avoids false conflicts caused only by different units or formatting.

---

# 26. Cross-Document Conflict Handling

A conflict should mean the normalized observations are materially different according to the reasoning rules, not merely differently formatted.

Example:

```text
Invoice          → GROSS_WEIGHT = 453.592 kg
Bill of Lading   → GROSS_WEIGHT = 453.59 kg
```

These are numerically very close.

Example of a potentially meaningful discrepancy:

```text
Invoice          → GROSS_WEIGHT = 450 kg
Bill of Lading   → GROSS_WEIGHT = 480 kg
```

The pipeline preserves both values; Aloka decides how the relationship should be interpreted.

---

# 27. Kaveen — Frontend / XAI Architecture

Kaveen consumes the document-level evidence generated by the pipeline.

Important fields:

```text
page
bbox
value
entity_type
extraction_confidence
classification_confidence
normalization_warning
```

Conceptual UI:

```text
┌────────────────────────────────────────────────────┐
│ PDF Viewer                                         │
│                                                    │
│  Page 2                                            │
│                                                    │
│  Gross Weight: 450.00 KG  ← highlighted bbox      │
│  ┌───────────────────────────────┐                 │
│  │                               │                 │
│  └───────────────────────────────┘                 │
│                                                    │
├────────────────────────────────────────────────────┤
│ Entity: GROSS_WEIGHT                               │
│ Raw: 450.00 KG                                     │
│ Normalized: 450.0 kg                               │
│ Confidence: 94%                                    │
│ Source: Page 2                                     │
└────────────────────────────────────────────────────┘
```

---

# 28. Three XAI Layers

The architecture supports three useful explainability levels.

## Layer 1 — Visual evidence

```text
Entity
 ↓
Page + bbox
 ↓
Original PDF
```

Answers:

> Where did this value come from?

## Layer 2 — Extraction reasoning metadata

```text
Entity
 ↓
Extraction confidence
Classification confidence
Normalization warning
Evidence
```

Answers:

> How reliably was the value extracted and normalized?

## Layer 3 — Cross-document reasoning

```text
Multiple entities
 ↓
Knowledge graph
 ↓
Matches / conflicts / relationships
 ↓
Reasoning output
```

Answers:

> Why did the system identify these documents/fields as consistent or inconsistent?

---

# 29. API Layer

FastAPI should be a thin orchestration layer.

Potential responsibilities:

```text
POST /dossiers
POST /dossiers/{id}/documents
GET  /dossiers/{id}
GET  /documents/{id}
GET  /documents/{id}/result
GET  /documents/{id}/pages
GET  /health
GET  /demo/status
```

The exact route names can differ.

The important separation is:

```text
HTTP handling
     ↓
Service layer
     ↓
AI Pipeline / Persistence
```

FastAPI should not directly implement OCR or normalization logic.

---

# 30. Storage Architecture

## File storage

Stores original uploaded PDFs and optionally rendered page images.

```text
Storage
│
├── dossiers/
│   ├── DOSSIER-001/
│   │   ├── invoice.pdf
│   │   ├── packing_list.pdf
│   │   └── awb.pdf
│   └── ...
```

## PostgreSQL

Used for structured application metadata and persistent normalization cache where configured.

Conceptual data:

```text
dossiers
  │
  └── documents
        │
        ├── processing status
        ├── storage path
        ├── document type
        └── extraction result reference

norm_cache
  │
  ├── entity type
  ├── normalized input key
  ├── normalized value
  ├── unit
  └── metadata
```

---

# 31. Database / Normalization Cache Architecture

```text
Entity Normalizer
       │
       ▼
 deterministic?
   ┌───┴────┐
  YES       NO
   │         │
   ▼         ▼
Python     Cache lookup
rules         │
              ├──── HIT ────► return
              │
              └── MISS ─────► Gemini
                                 │
                                 ▼
                              save cache
                                 │
                                 ▼
                               return
```

The cache is an optimization and reliability mechanism. The pipeline should not expose cache internals to downstream consumers.

---

# 32. Demo Architecture

The demo must have a deterministic fallback path.

```text
                 LIVE DEMO
                    │
                    ▼
             Demo Processing
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
      Real Pipeline        Demo Cache
          │                   │
          ▼                   ▼
      success?             serve result
          │
     ┌────┴────┐
    YES        NO
     │          │
     ▼          ▼
 Real result  Cache fallback
```

The demo should not depend entirely on a live LLM/network request.

---

# 33. Result Source Metadata

For demo/fallback observability, results can carry internal metadata such as:

```text
result_source = real
result_source = cache
result_source = mock
```

This should be visible to the system but does not need to be part of the external master contract unless the team decides to formalize it.

The frontend should never silently present mock data as real AI output.

---

# 34. Mock Pipeline Architecture

The mock pipeline exists to unblock parallel development.

```text
Aloka / Kaveen
      │
      ▼
 MockPipeline
      │
      ▼
Same ExtractionResult schema
      │
      ▼
Develop reasoning + frontend
```

Later:

```text
MockPipeline
     ↓ replaced by
AIPipeline
```

The consumer contract should remain stable.

---

# 35. Demo Cache Architecture

Pre-process the selected demo documents:

```text
commercial_invoice.pdf
packing_list.pdf
awb.pdf
bill_of_lading.pdf
delivery_order.pdf
```

Generate:

```text
demo_cache.json
```

The cache should contain:

```text
document_id
result
pipeline/cache version metadata if used
```

This gives a deterministic demo path even when live inference is slow or temporarily unavailable.

---

# 36. Phase 11 — Integration Testing Architecture

Phase 11 validates the complete stack rather than only individual modules.

```text
Synthetic PDFs
     │
     ▼
Real Pipeline
     │
     ▼
Schema Validation
     │
     ▼
Ground Truth Validation
     │
     ▼
Edge Cases
     │
     ▼
Normalization Trap Tests
     │
     ▼
Performance Benchmark
     │
     ├───────────────┐
     ▼               ▼
Aloka Contract   Kaveen Contract
     │               │
     └───────┬───────┘
             ▼
        Demo Cache
             │
             ▼
       Final Health Check
```

---

# 37. Integration Test Categories

## 37.1 Synthetic document regression

Test all known synthetic shipping documents.

## 37.2 Schema validation

Verify all required master-contract and entity fields.

## 37.3 Ground-truth validation

Compare actual extracted values against expected values for controlled synthetic PDFs.

## 37.4 Edge-case testing

Test:

```text
scanned image-only PDF
rotated pages
multi-column layout
tables
1-page minimal PDF
10+ page PDF
corrupt PDF
non-shipping PDF
```

## 37.5 Contract integration

Verify Aloka and Kaveen can consume the actual result format.

## 37.6 Performance

Measure processing time across repeated runs.

---

# 38. Trap Test Architecture

Trap tests deliberately create values that look different but should normalize to the same canonical value.

## Trap 1 — Weight conversion

```text
Commercial Invoice
1000 lbs
     ↓
453.592 kg

Bill of Lading
453.59 kg
     ↓
453.59 kg
```

Then Aloka's tolerance logic can determine the values are sufficiently close.

## Trap 2 — Name token ordering

```text
Burlington Industries Inc.
           vs
Industries Burlington, Inc.
```

Both can normalize to a common semantic cache key when Phase 09 rules support this form.

## Trap 3 — Incoterm variants

```text
FOB Colombo Port
      ↓
FOB

Free On Board
      ↓
FOB
```

These tests validate that the normalizer prevents false conflicts caused by representation differences.

---

# 39. Performance Strategy

Primary optimization points:

```text
1. Reuse initialized models
2. Render PDF pages only once per processing run
3. Avoid duplicate Gemini calls
4. Use deterministic normalization where possible
5. Use cache for semantic normalization
6. Pre-process demo PDFs
```

The main expensive stages are likely to be OCR, image processing, Gemini inference and uncached semantic normalization.

---

# 40. Security Boundaries

The architecture should enforce:

```text
Frontend
   ↓ HTTPS
FastAPI
   ↓
Authenticated service
   ↓
File storage / DB / AI services
```

Sensitive implementation details should not be returned unnecessarily through public APIs.

Examples:

```text
API should return structured processing errors
not full Python tracebacks.
```

Logs may contain diagnostic details while client responses stay controlled.

---

# 41. Failure Containment

The architecture should contain failures by layer.

```text
Gemini failure
    ↓
Extractor records error
    ↓
Pipeline continues page processing where possible
    ↓
Master result still returned
```

```text
Cache failure
    ↓
Normalizer attempts fallback path
    ↓
Document processing continues when possible
```

```text
Demo live inference failure
    ↓
Demo cache
    ↓
Frontend remains operational
```

---

# 42. Interface Boundaries

The most important contracts are:

## Upload → Dossier

```text
dossier_id
document_id
file reference
status
```

## Dossier → Pipeline

```text
pdf_path
document_id
```

## Pipeline → Aloka

```text
ExtractionResult
```

## Pipeline → Kaveen

```text
ExtractionResult fields related to page/bbox/evidence
```

## Normalizer → Pipeline

```text
normalized_value
unit
warn
```

These interfaces reduce coupling.

---

# 43. Complete Sequence — One Document

```text
User
 │
 │ upload invoice.pdf
 ▼
FastAPI
 │
 ├── create document_id = doc_001
 ├── store PDF
 └── call processing service
          │
          ▼
pipeline.process_document()
          │
          ▼
       OCR
          │
          ▼
   classification
          │
          ▼
  convert PDF to images
          │
          ▼
  extract entities/page
          │
          ▼
   map bbox/evidence
          │
          ▼
     normalize
          │
          ▼
      confidence
          │
          ▼
   dedup/validation
          │
          ▼
 ExtractionResult
      │         │
      │         └────────► Kaveen
      │                     │
      │                     └── PDF bbox/XAI
      │
      └──────────────────► Aloka
                            │
                            └── document reasoning
```

---

# 44. Complete Sequence — Dossier

```text
User uploads 5 files
         │
         ▼
      Dossier
         │
   ┌─────┼────────┬─────────┬─────────┐
   ▼     ▼        ▼         ▼         ▼
Invoice Packing  AWB       B/L       D/O
   │     │        │         │         │
   ▼     ▼        ▼         ▼         ▼
process_document() × 5
   │     │        │         │         │
   └─────┴────────┴─────────┴─────────┘
                  │
                  ▼
         Multiple ExtractionResults
                  │
                  ▼
               Aloka
                  │
                  ▼
          Knowledge Graph
                  │
        ┌─────────┼──────────┐
        ▼         ▼          ▼
      matches  conflicts  relations
                  │
                  ▼
          shipment-level result
```

---

# 45. Recommended Internal Data Relationships

Conceptually:

```text
Dossier
│
├── dossier_id
├── metadata
└── documents[]
      │
      ├── document_id
      ├── file_path / storage reference
      ├── document_type
      ├── status
      └── extraction_result
             │
             ├── classification
             ├── entities[]
             ├── raw_ocr[]
             ├── processing time
             └── errors[]
```

Aloka builds additional graph relationships above the document results.

---

# 46. Repository Responsibility Matrix

| Component | Primary responsibility | Should know about |
|---|---|---|
| FastAPI | HTTP/API handling | services/contracts |
| Dossier Service | group/manage documents | storage + pipeline |
| Storage Service | PDF persistence | storage provider |
| OCR Engine | text + bbox | PDF/OCR engine |
| Classifier | document type | OCR output |
| Entity Extractor | structured entities | page image + OCR + document type |
| BBox Mapping | evidence location | OCR tokens + extracted entities |
| Normalizer | canonical values | entity type + cache + rules/LLM |
| Confidence Scorer | confidence metadata | extraction/OCR signals |
| Pipeline | orchestration | all AI modules |
| Mock Pipeline | development fallback | master contract |
| Aloka | reasoning | multiple ExtractionResults |
| Knowledge Graph | cross-document relationships | normalized entities |
| Kaveen | visualization/XAI | bbox/page/entity data |
| PostgreSQL | persistent structured state/cache | DB schema |
| Demo Cache | deterministic demo fallback | serialized results |

---

# 47. What the Pipeline Owns vs Does Not Own

## Pipeline owns

```text
✅ Stage order
✅ Module invocation
✅ Error aggregation
✅ Page/image coordination
✅ Entity normalization invocation
✅ Result assembly
✅ Timing
✅ Dedup/validation orchestration
```

## Pipeline does not own

```text
❌ Dossier creation
❌ HTTP routing
❌ User authentication
❌ Long-term business reasoning
❌ Frontend rendering
❌ Shipment-level knowledge graph semantics
❌ Replacing raw values with normalized values
```

---

# 48. Critical Invariants

These rules should remain true throughout the system.

### Invariant 1 — Raw value preservation

```text
entity.value
```

must preserve the extracted raw representation.

### Invariant 2 — Normalization before downstream comparison

Aloka should prefer:

```text
normalized_value + unit
```

for comparison when available.

### Invariant 3 — Honest bbox

```text
bbox = real coordinate
OR
bbox = null
```

Never fabricate it.

### Invariant 4 — Confidence range

```text
0.0 ≤ confidence ≤ 1.0
```

### Invariant 5 — Conflicts are preserved

Different entity values should not be silently overwritten merely because they have the same entity type.

### Invariant 6 — Stable document-level contract

All real and mock pipelines should return compatible schema structures.

### Invariant 7 — JSON serializable result

Final results must contain ordinary JSON-compatible data types.

---

# 49. Testing Pyramid

```text
                    ┌───────────────────┐
                    │ Demo / E2E        │
                    │ Full dossier      │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Integration       │
                    │ Pipeline + Aloka  │
                    │ Pipeline + Kaveen │
                    └─────────┬─────────┘
                              │
                 ┌────────────▼────────────┐
                 │ Module tests            │
                 │ OCR / classifier / etc │
                 └────────────┬────────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Pure logic tests  │
                    │ normalization     │
                    │ parsing           │
                    └───────────────────┘
```

---

# 50. Final AI Pipeline Definition

The complete AI pipeline is:

```text
                        ONE PDF
                           │
                           ▼
                        OCR
                           │
                    text + bbox + conf
                           │
                           ▼
                    CLASSIFICATION
                           │
                type + confidence + evidence
                           │
                           ▼
                   PAGE EXTRACTION
                           │
                       raw entities
                           │
                           ▼
                    BBOX MAPPING
                           │
                    source evidence
                           │
                           ▼
                    NORMALIZATION
                           │
                canonical value + unit
                           │
                           ▼
                   CONFIDENCE SCORE
                           │
                           ▼
                DEDUP / VALIDATION
                           │
                           ▼
                  EXTRACTION RESULT
                           │
          ┌────────────────┴────────────────┐
          ▼                                 ▼
       KAVEEN                            ALOKA
    Visual / XAI                    Reasoning / KG
          │                                 │
          ▼                                 ▼
      PDF evidence                   Cross-document
      bbox overlay                   matching/conflicts
                                            │
                                            ▼
                                      Shipment-level
                                         reasoning
```

---

# 51. Final Dossier Architecture

```text
                              USER
                               │
                               ▼
                           FRONTEND
                               │
                               ▼
                            FASTAPI
                               │
                      ┌────────┴────────┐
                      ▼                 ▼
                  DOSSIER            STORAGE
                  SERVICE               │
                      │                 │
         ┌────────────┼──────────────┐  │
         │            │              │  │
         ▼            ▼              ▼  ▼
      Document 1   Document 2     Document N
         │            │              │
         └────────────┼──────────────┘
                      ▼
               AI PIPELINE × N
                      │
                      ▼
             ExtractionResults
                      │
              ┌───────┴────────┐
              ▼                ▼
           POSTGRES          ALOKA
                               │
                               ▼
                        KNOWLEDGE GRAPH
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
            MATCH           CONFLICT         RELATION
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                         FINAL REASONING
                               │
                               ▼
                            KAVEEN
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
                PDF VIEWER            RESULTS UI
                BBox overlays          Confidence
                Raw evidence           Normalized data
                Explainability          Conflict display
```

---

# 52. Phase Roadmap

The current architecture is built progressively through the following phases.

```text
Phase 01
Environment / foundations
        │
        ▼
Phase 02
OCR integration + text + bbox
        │
        ▼
Phase 03
Document classification
        │
        ▼
Phase 04/05
Entity extraction / related document intelligence
        │
        ▼
Phase 06
BBox mapping / extraction integration
        │
        ▼
Phase 08
Confidence scoring
        │
        ▼
Phase 09
Normalization + persistent cache
        │
        ▼
Phase 10
Pipeline orchestration
        │
        ▼
Phase 11
Integration testing + demo preparation
        │
        ├───────────────────────────────┐
        ▼                               ▼
     ALOKA                           KAVEEN
     Reasoning                       Frontend/XAI
        │                               │
        └──────────────┬────────────────┘
                       ▼
                COMPLETE SYSTEM
```

---

# 53. Production Request Flow

The target runtime behavior is:

```python
# Backend / service layer
result = pipeline.process_document(
    pdf_path=document.path,
    document_id=document.id,
)
```

The backend should not need code like:

```python
ocr = OcrEngine()
classification = classifier.classify(...)
extractor.extract(...)
normalizer.normalize(...)
```

That knowledge belongs inside the pipeline.

---

# 54. Final Integration Contracts

## Pipeline contract

```python
process_document(
    pdf_path: str,
    document_id: str
) -> dict
```

## Aloka input

```text
document_type
classification_confidence
classification_evidence
entities[]
normalized_value
unit
extraction_confidence
classification_confidence
errors
```

## Kaveen input

```text
page
bbox
value
entity_type
normalized_value
extraction_confidence
normalization_warning
raw_ocr
```

## Dossier input/output

```text
dossier_id
  ↓
document_id[]
  ↓
ExtractionResult[]
  ↓
Aloka reasoning
```

---

# 55. Definition of Done — Whole AI System

The architecture is operational when all of the following work together:

```text
✅ User can create/upload a dossier
✅ Dossier can contain multiple documents
✅ Each document receives a stable document_id
✅ PDFs are stored/retrievable
✅ Pipeline accepts a single PDF + document_id
✅ OCR extracts text + bbox + confidence
✅ Classification identifies document type
✅ Entity extraction returns structured fields
✅ BBox mapping links entities to source evidence
✅ Normalization converts/standardizes supported values
✅ Persistent cache avoids unnecessary semantic LLM calls
✅ Confidence metadata is populated
✅ Duplicate identical entities are controlled
✅ Genuine conflicting values are preserved
✅ Master ExtractionResult is JSON serializable
✅ Errors are returned in a controlled structure
✅ Aloka consumes the result without knowing pipeline internals
✅ Aloka combines documents through the Knowledge Graph
✅ Kaveen renders page/bbox evidence
✅ Synthetic regression tests pass
✅ Edge-case tests do not crash the system
✅ Trap tests validate normalization
✅ Performance is measured
✅ Demo documents are preprocessed
✅ Demo cache is available as deterministic fallback
✅ Final health/self-test passes
```

---

# 56. Final Architecture in One Diagram

```text
                                      ┌──────────────────┐
                                      │       USER       │
                                      └────────┬─────────┘
                                               │
                                               ▼
                                      ┌──────────────────┐
                                      │    FRONTEND      │
                                      │ Upload / Results │
                                      │ PDF / XAI        │
                                      └────────┬─────────┘
                                               │
                                               ▼
                                      ┌──────────────────┐
                                      │      FASTAPI     │
                                      └────────┬─────────┘
                                               │
                         ┌─────────────────────┴─────────────────────┐
                         ▼                                           ▼
                ┌─────────────────┐                         ┌─────────────────┐
                │  DOSSIER LAYER  │                         │  FILE STORAGE   │
                │ dossier_id      │                         │ PDFs / images   │
                │ document_id     │                         └─────────────────┘
                │ status          │
                └────────┬────────┘
                         │
                         ▼
                ┌───────────────────────────────────────┐
                │            AI PIPELINE                │
                │                                       │
                │  OCR                                  │
                │   ↓                                   │
                │  Classification                       │
                │   ↓                                   │
                │  Entity Extraction                    │
                │   ↓                                   │
                │  BBox Mapping                         │
                │   ↓                                   │
                │  Normalization ─────► PostgreSQL      │
                │   ↓                 norm_cache        │
                │  Confidence                           │
                │   ↓                                   │
                │  Dedup / Validation                    │
                │   ↓                                   │
                │  Master ExtractionResult               │
                └───────────────┬───────────────────────┘
                                │
                  ┌─────────────┴──────────────┐
                  ▼                            ▼
        ┌─────────────────────┐      ┌─────────────────────┐
        │        ALOKA        │      │       KAVEEN        │
        │ Reasoning Engine    │      │ Frontend / XAI      │
        │                     │      │                     │
        │ Multi-document      │      │ PDF evidence        │
        │ Knowledge Graph     │      │ bbox overlays       │
        │ Matching            │      │ entity display      │
        │ Conflict detection  │      │ confidence UI       │
        └──────────┬──────────┘      └─────────────────────┘
                   │
                   ▼
        ┌─────────────────────────┐
        │ Shipment-level Findings │
        │                         │
        │ matches                 │
        │ conflicts               │
        │ relationships            │
        │ reasoning               │
        └────────────┬────────────┘
                     │
                     ▼
              ┌───────────────┐
              │    FRONTEND   │
              │ Final results │
              │ + XAI         │
              └───────────────┘
```

---

# 57. The Single Most Important Mental Model

Remember the system as four layers:

```text
LAYER 1 — DOSSIER
"Which documents belong together?"

        ↓

LAYER 2 — AI PIPELINE
"What is inside this ONE document?"

        ↓

LAYER 3 — ALOKA / KNOWLEDGE GRAPH
"How do ALL documents relate?"

        ↓

LAYER 4 — KAVEEN / XAI FRONTEND
"How do we show the answer and its evidence?"
```

That separation is the core architecture.

---

# 58. Final Summary

The project should ultimately behave like this:

```text
                  SHIPPING DOSSIER
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
        Invoice PDF              AWB PDF
             │                       │
             ▼                       ▼
        process_document()      process_document()
             │                       │
             ▼                       ▼
       ExtractionResult        ExtractionResult
             │                       │
             └───────────┬───────────┘
                         ▼
                     ALOKA
                         │
                         ▼
                 KNOWLEDGE GRAPH
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
           MATCH      CONFLICT    RELATION
                         │
                         ▼
                    FINAL RESULT
                         │
                         ▼
                      KAVEEN
                         │
                 ┌───────┴────────┐
                 ▼                ▼
             PDF + BBOX       Result / XAI
```

> **Core architectural statement:** The platform turns a collection of raw shipping PDFs into structured document intelligence, then into cross-document shipment reasoning, while preserving enough source evidence for the frontend to explain every important extracted value.
