# Phase 10 — Pipeline Orchestration

> **Priority:** MUST
> **Estimated Time:** 2–3 hours
> **Dependencies:** Phases 02, 03, 06, 08, 09
> **Blocks:** Integration with Aloka's reasoning engine and Kaveen's frontend/XAI layer

---

# Goal

Wire together all AI modules into a single document-processing pipeline.

The rest of the backend should call:

```python
pipeline.process_document(
    pdf_path="/uploads/invoice.pdf",
    document_id="doc_001"
)

```

The calling layer should NOT need to know how OCR, classification, extraction, normalization, or confidence scoring works internally.

The pipeline is responsible for:

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
Master ExtractionResult

```

---

# Important Architecture Decision

The system has a **Dossier layer** above the document pipeline.

A dossier can contain multiple documents:

```text
DOSSIER-001
│
├── commercial_invoice.pdf
├── packing_list.pdf
├── awb.pdf
├── bill_of_lading.pdf
└── delivery_order.pdf

```

The upload/API layer creates the `dossier_id` and `document_id`.

The AI pipeline remains **document-oriented**:

```text
Dossier
   │
   ├── document 1 → process_document()
   ├── document 2 → process_document()
   ├── document 3 → process_document()
   └── document 4 → process_document()

```

Aloka's reasoning engine later combines the resulting documents through the dossier/Knowledge Graph.

This keeps the AI pipeline reusable and avoids coupling it directly to FastAPI.

---

# Overall Architecture

```text
                         DOSSIER UPLOAD
                               │
                               ▼
                         FastAPI API
                               │
                   ┌───────────┴───────────┐
                   │                       │
                   ▼                       ▼
             File Storage             PostgreSQL
                   │                 dossier/documents
                   │                       │
                   └───────────┬───────────┘
                               │
                               ▼
                     pipeline.process_document()
                               │
                               ▼
                         PDF PROCESSING
                               │
                               ▼
                              OCR
                               │
                               ▼
                       CLASSIFICATION
                               │
                               ▼
                       ENTITY EXTRACTION
                               │
                               ▼
                         BBOX MAPPING
                               │
                               ▼
                        NORMALIZATION
                               │
                               ▼
                      CONFIDENCE SCORING
                               │
                               ▼
                       MASTER RESULT
                               │
                     ┌─────────┴─────────┐
                     ▼                   ▼
              Aloka Reasoning       Kaveen Frontend
               Knowledge Graph        PDF / XAI

```

---

# Input Contract

The primary document-level interface is:

```python
result = pipeline.process_document(
    pdf_path="/uploads/invoice.pdf",
    document_id="doc_001"
)

```

## Parameters

### `pdf_path`

Absolute or resolvable path to the uploaded PDF.

### `document_id`

Unique identifier for the document.

The dossier/upload layer is responsible for generating this identifier.

---

# Output — Master Contract

The pipeline returns:

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
    },
    {
      "entity_type": "CONSIGNEE_NAME",
      "value": "ABC Textiles Ltd",
      "normalized_value": "ABC Textiles Ltd",
      "unit": null,
      "page": 1,
      "bbox": [50, 100, 300, 130],
      "extraction_confidence": 0.88,
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

# Entity Contract

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

### Important

The raw value must remain unchanged.

Example:

```text
value:
"1,000.00 LBS"

```

must remain:

```text
"1,000.00 LBS"

```

while:

```text
normalized_value:
453.592

```

and:

```text
unit:
"kg"

```

are added later by Phase 09.

---

# Pipeline Processing Order

The pipeline must execute in this exact order:

```text
STEP 1  → OCR
STEP 2  → Classification
STEP 3  → Entity Extraction
STEP 4  → Bounding Box Mapping
STEP 5  → Canonical Normalization
STEP 6  → Confidence Scoring
STEP 7  → Entity Deduplication / Validation
STEP 8  → Master Result Assembly

```

No raw entity should be returned to downstream modules before normalization has been attempted.

---

# Step 1 — OCR

Call:

```python
ocr_result = self.ocr.extract(pdf_path)

```

Expected:

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

If OCR fails:

```text
Return error result

```

rather than raising an exception to the API layer.

---

# Step 2 — Document Classification

Call:

```python
classification = self.classifier.classify(
    ocr_result
)

```

Expected:

```text
document_type
confidence
evidence
all_scores

```

Example:

```json
{
  "document_type": "commercial_invoice",
  "confidence": 0.97,
  "evidence": [
    "invoice",
    "unit price",
    "total amount"
  ]
}

```

If classification fails:

```text
document_type = "unknown"
confidence = 0.0
evidence = []

```

The pipeline should continue when possible.

---

# Step 3 — Page Image Preparation

Entity extraction requires the actual page image.

Convert the PDF to page images:

```python
images = convert_from_path(
    pdf_path
)

```

The pipeline should ensure that:

```text
OCR page N

```

corresponds to:

```text
Image N

```

Do not accidentally shift page numbers.

---

# Step 4 — Entity Extraction

For each page:

```python
page_entities = self.extractor.extract(
    page_image,
    classification.document_type,
    page.tokens
)

```

The extractor performs:

```text
Page Image
     +
OCR Tokens
     +
Document Type
     ↓
Gemini Vision
     ↓
Structured Entity JSON
     ↓
OCR BBox Mapping
     ↓
Raw Entities

```

---

# Entity Extraction Rules

The extractor must:

```text
✅ preserve raw value
✅ return entity_type
✅ map bbox
✅ return extraction confidence
✅ handle multi-token entities
✅ handle missing fields
✅ return [] for unknown document types
✅ handle Gemini errors safely

```

The extractor must NOT:

```text
❌ normalize weights
❌ convert units
❌ normalize dates
❌ canonicalize identifiers

```

Those belong to Phase 09.

---

# Bounding Box Mapping

Gemini may return:

```text
"ABC Textiles Ltd"

```

while OCR may contain:

```text
ABC
Textiles
Ltd

```

Therefore the pipeline must rely on the bbox-aware mapping performed by the extractor.

The resulting bbox may be:

```text
[50, 100, 300, 130]

```

covering all relevant OCR tokens.

A missing bbox should be represented honestly:

```json
"bbox": null

```

rather than a fabricated coordinate.

This is required for Layer 1 XAI.

---

# Step 5 — Normalization

Every extracted entity goes through Phase 09:

```python
norm = self.normalizer.normalize(
    entity["entity_type"],
    entity["value"]
)

```

Then:

```python
entity["normalized_value"] = (
    norm["normalized_value"]
)

entity["unit"] = norm["unit"]

entity["normalization_warning"] = (
    norm["warn"]
)

```

---

# Normalization Architecture

Phase 09 performs:

```text
                         RAW VALUE
                             │
                             ▼
                    Entity Type Router
                             │
                ┌────────────┴────────────┐
                │                         │
          Deterministic               Semantic
             Entity                    Entity
                │                         │
                ▼                         ▼
          Python Rules               Tier 1 Key
                │                         │
                │                         ▼
                │                    PostgreSQL
                │                    norm_cache
                │                         │
                │                   ┌─────┴─────┐
                │                   │           │
                │                  HIT         MISS
                │                   │           │
                │                   │           ▼
                │                   │        Gemini
                │                   │           │
                │                   │           ▼
                │                   │        Save DB
                │                   │
                └───────────────────┴───────────┘
                             │
                             ▼
                     Normalized Entity

```

---

# Critical Rule

Raw values must never be replaced.

Example:

```json
{
  "entity_type": "GROSS_WEIGHT",
  "value": "1,000.00 LBS",
  "normalized_value": 453.592,
  "unit": "kg"
}

```

This preserves:

```text
WHAT WAS WRITTEN

```

while also providing:

```text
WHAT THE SYSTEM USES FOR COMPARISON

```

---

# Step 6 — Confidence Scoring

The pipeline must preserve extraction confidence from Phase 08.

For each entity:

```text
OCR confidence
       +
BBox match quality
       +
Entity difficulty
       ↓
Extraction confidence

```

Classification confidence comes from Phase 03.

The final entity should contain:

```json
{
  "extraction_confidence": 0.94,
  "classification_confidence": 0.97
}

```

---

# Step 7 — Entity Deduplication

Multi-page documents can repeat header information.

Example:

```text
Page 1:
Invoice Number = INV-1023

Page 2:
Invoice Number = INV-1023

```

The pipeline should avoid creating unnecessary duplicate entities.

A reasonable deduplication key is:

```text
entity_type
+
normalized_value

```

Example:

```text
INVOICE_NUMBER:INV1023

```

If the same value appears multiple times:

- retain the strongest extraction
- retain the most reliable bbox
- do not discard genuinely different values
- do not deduplicate different page occurrences when the document actually contains separate values

---

# Conflict Between Duplicate Entity Values

Example:

```text
Page 1:
GROSS_WEIGHT = 450 KG

Page 2:
GROSS_WEIGHT = 448 KG

```

Do NOT silently overwrite one with the other.

Both may be relevant.

The reasoning layer should be able to inspect the competing values.

The pipeline should preserve them or report them appropriately rather than hiding the discrepancy.

---

# Step 8 — Master Result Assembly

After all pages are processed:

```python
raw_ocr = []

```

For every OCR token:

```python
raw_ocr.append({
    "text": token.text,
    "page": token.page,
    "bbox": token.bbox,
    "ocr_confidence": token.confidence
})

```

Then assemble:

```python
{
    "document_id": document_id,
    "document_type": classification.document_type,
    "classification_confidence": classification.confidence,
    "classification_evidence": classification.evidence,
    "entities": all_entities,
    "raw_ocr": raw_ocr,
    "processing_time_ms": processing_time,
    "errors": errors
}

```

---

# Error Handling

The pipeline must not crash because one stage fails.

## OCR failure

```text
OCR failed
→ return error result

```

## Classification failure

```text
classification error
→ document_type = unknown
→ continue where possible

```

## Gemini extraction failure

```text
Gemini extraction error
→ record error
→ continue remaining pages

```

## Normalization failure

```text
normalization error
→ normalized_value = null
→ warn = true
→ continue

```

## Database failure

```text
DB cache failure
→ log warning
→ Phase 09 gracefully degrades
→ pipeline continues

```

## Invalid PDF

```text
invalid PDF
→ return errors[]
→ no uncaught exception

```

---

# Error Contract

Errors should be returned as:

```json
{
  "errors": [
    {
      "stage": "normalization",
      "message": "PostgreSQL cache unavailable",
      "page": 1,
      "entity_type": "PORT_LOADING"
    }
  ]
}

```

For MVP compatibility, a simple string format is also acceptable:

```json
{
  "errors": [
    "Normalization failed for PORT_LOADING on page 1"
  ]
}

```

The important requirement is that errors do not crash the pipeline.

---

# Processing Time

The pipeline must record:

```python
processing_time_ms

```

using:

```python
start_time = time.perf_counter()

```

rather than relying on coarse wall-clock measurement.

Example:

```python
processing_time = int(
    (time.perf_counter() - start_time) * 1000
)

```

Target:

```text
< 30 seconds per document

```

for the hackathon demo.

---

# Performance Optimization

The pipeline should avoid unnecessary repeated work.

## Models

Initialize models once:

```text
AIPipeline
 ├── OcrEngine
 ├── DocumentClassifier
 ├── EntityExtractor
 ├── EntityNormalizer
 └── ConfidenceScorer

```

The singleton/persistent application instance can reuse these components.

## Images

Convert the PDF to images once within a document processing run.

## Normalization

Deterministic normalization must not call Gemini.

Semantic normalization should use:

```text
Tier 1 → PostgreSQL → Gemini

```

to minimize API calls.

---

# Dossier Integration

The dossier layer should call the document pipeline for each file:

```python
for document in dossier.documents:

    result = pipeline.process_document(
        pdf_path=document.path,
        document_id=document.id
    )

    save_result(result)

```

Conceptually:

```text
Dossier
│
├── Document A
│      ↓
│   process_document()
│
├── Document B
│      ↓
│   process_document()
│
├── Document C
│      ↓
│   process_document()
│
└── Document D
       ↓
    process_document()

```

Then Aloka receives the collection of document results for reasoning.

---

# Dossier Status Flow

The upload/service layer can expose:

```text
UPLOADED
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
COMPLETED

```

On failure:

```text
FAILED

```

The core pipeline does not need to own the HTTP status API.

---

# Optional Progress Callback

For better frontend progress reporting, the pipeline may accept an internal callback in a future version:

```python
on_progress(stage, progress)

```

Example:

```text
OCR          → 20%
Classification → 35%
Extraction   → 60%
Normalization → 80%
Confidence   → 90%
Complete     → 100%

```

This is optional for MVP.

---

# Production `pipeline.py`

```python
# backend/ai_pipeline/pipeline.py

import time
import logging
from pathlib import Path

from pdf2image import convert_from_path

from .ocr_engine import OcrEngine
from .classifier import DocumentClassifier
from .entity_extractor import EntityExtractor
from .normalizer import EntityNormalizer
from .confidence import ConfidenceScorer


logger = logging.getLogger(__name__)


class AIPipeline:

    def __init__(self):

        self.ocr = OcrEngine()
        self.classifier = DocumentClassifier()
        self.extractor = EntityExtractor()
        self.normalizer = EntityNormalizer()
        self.scorer = ConfidenceScorer()

    def process_document(
        self,
        pdf_path: str,
        document_id: str
    ) -> dict:

        start_time = time.perf_counter()

        errors = []
        all_entities = []

        pdf_path = str(
            Path(pdf_path).resolve()
        )

        # ========================================================
        # STEP 1 — OCR
        # ========================================================

        try:

            ocr_result = self.ocr.extract(
                pdf_path
            )

        except Exception as exc:

            logger.exception(
                "OCR failed for document=%s",
                document_id
            )

            return self._error_result(
                document_id,
                f"OCR failed: {exc}",
            )

        # ========================================================
        # STEP 2 — CLASSIFICATION
        # ========================================================

        try:

            classification = (
                self.classifier.classify(
                    ocr_result
                )
            )

        except Exception as exc:

            logger.exception(
                "Classification failed for document=%s",
                document_id
            )

            errors.append(
                f"Classification failed: {exc}"
            )

            classification = None

        if classification is None:

            document_type = "unknown"
            classification_confidence = 0.0
            classification_evidence = []

        else:

            document_type = (
                classification.document_type
            )

            classification_confidence = (
                float(
                    classification.confidence
                )
            )

            classification_evidence = (
                list(
                    classification.evidence
                    or []
                )
            )

        # ========================================================
        # STEP 3 — PAGE IMAGES
        # ========================================================

        try:

            images = convert_from_path(
                pdf_path
            )

        except Exception as exc:

            logger.exception(
                "PDF image conversion failed"
            )

            errors.append(
                f"Image conversion failed: {exc}"
            )

            images = []

        # ========================================================
        # STEP 4 — ENTITY EXTRACTION
        #           + BBOX MAPPING
        #           + NORMALIZATION
        # ========================================================

        if document_type != "unknown":

            for page_index, page in enumerate(
                ocr_result.pages
            ):

                if page_index >= len(images):

                    errors.append(
                        "Missing rendered image "
                        f"for page {page_index + 1}"
                    )

                    continue

                image = images[page_index]

                try:

                    page_entities = (
                        self.extractor.extract(
                            image,
                            document_type,
                            page.tokens,
                        )
                    )

                except Exception as exc:

                    logger.exception(
                        "Entity extraction failed "
                        "document=%s page=%d",
                        document_id,
                        page_index + 1,
                    )

                    errors.append(
                        "Entity extraction failed "
                        f"on page {page_index + 1}: "
                        f"{exc}"
                    )

                    continue

                # ----------------------------------------------
                # NORMALIZATION
                # ----------------------------------------------

                for entity in page_entities:

                    try:

                        entity_type = entity[
                            "entity_type"
                        ]

                        raw_value = entity[
                            "value"
                        ]

                        norm = (
                            self.normalizer.normalize(
                                entity_type,
                                raw_value,
                            )
                        )

                        entity[
                            "normalized_value"
                        ] = norm.get(
                            "normalized_value"
                        )

                        entity["unit"] = norm.get(
                            "unit"
                        )

                        entity[
                            "normalization_warning"
                        ] = norm.get(
                            "warn",
                            False,
                        )

                        entity[
                            "page"
                        ] = page_index + 1

                        entity[
                            "classification_confidence"
                        ] = (
                            classification_confidence
                        )

                        # Make sure confidence exists.
                        if (
                            "extraction_confidence"
                            not in entity
                        ):

                            entity[
                                "extraction_confidence"
                            ] = 0.0

                    except Exception as exc:

                        logger.exception(
                            "Normalization failed "
                            "for entity=%r",
                            entity,
                        )

                        entity[
                            "normalized_value"
                        ] = None

                        entity["unit"] = None

                        entity[
                            "normalization_warning"
                        ] = True

                        entity[
                            "classification_confidence"
                        ] = (
                            classification_confidence
                        )

                        errors.append(
                            "Normalization failed "
                            f"on page {page_index + 1}: "
                            f"{exc}"
                        )

                    all_entities.append(
                        entity
                    )

        # ========================================================
        # STEP 5 — OPTIONAL ENTITY DEDUPLICATION
        # ========================================================

        all_entities = self._deduplicate_entities(
            all_entities
        )

        # ========================================================
        # STEP 6 — RAW OCR FOR LAYER 1 XAI
        # ========================================================

        raw_ocr = []

        for page in ocr_result.pages:

            for token in page.tokens:

                raw_ocr.append({
                    "text": token.text,
                    "page": token.page,
                    "bbox": token.bbox,
                    "ocr_confidence": token.confidence,
                })

        # ========================================================
        # STEP 7 — FINAL RESULT
        # ========================================================

        processing_time_ms = int(
            (
                time.perf_counter()
                - start_time
            ) * 1000
        )

        return {
            "document_id": document_id,
            "document_type": document_type,
            "classification_confidence":
                classification_confidence,
            "classification_evidence":
                classification_evidence,
            "entities": all_entities,
            "raw_ocr": raw_ocr,
            "processing_time_ms":
                processing_time_ms,
            "errors": errors,
        }

    # ============================================================
    # ENTITY DEDUPLICATION
    # ============================================================

    def _deduplicate_entities(
        self,
        entities: list[dict]
    ) -> list[dict]:

        grouped = {}

        for entity in entities:

            entity_type = entity.get(
                "entity_type"
            )

            normalized = entity.get(
                "normalized_value"
            )

            raw_value = entity.get(
                "value"
            )

            # Do not combine unresolved values.
            comparison_value = (
                normalized
                if normalized is not None
                else raw_value
            )

            key = (
                entity_type,
                str(comparison_value)
            )

            existing = grouped.get(key)

            if existing is None:

                grouped[key] = entity
                continue

            # Keep the entity with higher
            # extraction confidence.
            current_conf = float(
                entity.get(
                    "extraction_confidence",
                    0.0
                )
            )

            existing_conf = float(
                existing.get(
                    "extraction_confidence",
                    0.0
                )
            )

            if current_conf > existing_conf:
                grouped[key] = entity

        return list(
            grouped.values()
        )

    # ============================================================
    # ERROR RESULT
    # ============================================================

    def _error_result(
        self,
        document_id: str,
        error: str
    ) -> dict:

        return {
            "document_id": document_id,
            "document_type": "unknown",
            "classification_confidence": 0.0,
            "classification_evidence": [],
            "entities": [],
            "raw_ocr": [],
            "processing_time_ms": 0,
            "errors": [error],
        }


# ================================================================
# SINGLETON
# ================================================================

_pipeline_instance = None


def get_pipeline() -> AIPipeline:

    global _pipeline_instance

    if _pipeline_instance is None:

        _pipeline_instance = AIPipeline()

    return _pipeline_instance

```

---

# Important Deduplication Rule

The example `_deduplicate_entities()` is intentionally conservative.

It must NOT accidentally remove real conflicts.

For example:

```text
GROSS_WEIGHT = 450 KG
GROSS_WEIGHT = 448 KG

```

must remain two entities because:

```text
450.0 != 448.0

```

The reasoning engine may need both values.

---

# Mock Pipeline

Create:

```text
backend/ai_pipeline/mock_pipeline.py

```

The mock pipeline must return the **same master schema** as the real pipeline.

It should not randomly change the schema.

```python
# backend/ai_pipeline/mock_pipeline.py

from copy import deepcopy


MOCK_RESULT = {
    "document_id": "mock_001",
    "document_type": "commercial_invoice",
    "classification_confidence": 0.97,
    "classification_evidence": [
        "invoice",
        "unit price",
        "total amount"
    ],

    "entities": [
        {
            "entity_type": "INVOICE_NUMBER",
            "value": "INV-2024-1023",
            "normalized_value": "INV20241023",
            "unit": None,
            "page": 1,
            "bbox": [45, 120, 280, 145],
            "extraction_confidence": 0.96,
            "classification_confidence": 0.97,
            "normalization_warning": False
        },

        {
            "entity_type": "CONSIGNEE_NAME",
            "value": "ABC Textiles Ltd",
            "normalized_value": "ABC Textiles Ltd",
            "unit": None,
            "page": 1,
            "bbox": [50, 200, 320, 225],
            "extraction_confidence": 0.91,
            "classification_confidence": 0.97,
            "normalization_warning": False
        },

        {
            "entity_type": "GROSS_WEIGHT",
            "value": "450.00 KG",
            "normalized_value": 450.0,
            "unit": "kg",
            "page": 1,
            "bbox": [400, 350, 550, 375],
            "extraction_confidence": 0.94,
            "classification_confidence": 0.97,
            "normalization_warning": False
        },

        {
            "entity_type": "NET_WEIGHT",
            "value": "420.00 KG",
            "normalized_value": 420.0,
            "unit": "kg",
            "page": 1,
            "bbox": [400, 380, 550, 405],
            "extraction_confidence": 0.93,
            "classification_confidence": 0.97,
            "normalization_warning": False
        },

        {
            "entity_type": "PACKAGE_COUNT",
            "value": "25 Cartons",
            "normalized_value": 25,
            "unit": "cartons",
            "page": 1,
            "bbox": [400, 410, 550, 435],
            "extraction_confidence": 0.95,
            "classification_confidence": 0.97,
            "normalization_warning": False
        },

        {
            "entity_type": "INCOTERM",
            "value": "FOB Colombo",
            "normalized_value": "FOB",
            "unit": None,
            "page": 1,
            "bbox": [50, 300, 200, 325],
            "extraction_confidence": 0.92,
            "classification_confidence": 0.97,
            "normalization_warning": False
        },

        {
            "entity_type": "TOTAL_AMOUNT",
            "value": "45,230.00 USD",
            "normalized_value": 45230.0,
            "unit": None,
            "page": 1,
            "bbox": [400, 500, 580, 530],
            "extraction_confidence": 0.94,
            "classification_confidence": 0.97,
            "normalization_warning": False
        }
    ],

    "raw_ocr": [
        {
            "text": "Gross Weight: 450.00 KG",
            "page": 1,
            "bbox": [100, 340, 560, 380],
            "ocr_confidence": 0.98
        }
    ],

    "processing_time_ms": 1200,

    "errors": []
}


class MockPipeline:

    def process_document(
        self,
        pdf_path: str,
        document_id: str
    ) -> dict:

        result = deepcopy(
            MOCK_RESULT
        )

        result[
            "document_id"
        ] = document_id

        return result

```

---

# Why the Mock Pipeline Matters

Aloka and Kaveen can develop against:

```python
MockPipeline

```

before the real AI pipeline is complete.

Later:

```text
MockPipeline
     ↓
Real AIPipeline

```

without requiring changes to the consumers.

Both return the same schema.

---

# Full Pipeline Test

Create:

```text
backend/ai_pipeline/test_pipeline.py

```

```python
import json

from pipeline import get_pipeline


pipeline = get_pipeline()

result = pipeline.process_document(
    pdf_path="test_data/sample_invoice.pdf",
    document_id="test_001"
)


print(
    "Document type:",
    result["document_type"]
)

print(
    "Classification:",
    result["classification_confidence"]
)

print(
    "Entities:",
    len(result["entities"])
)

print(
    "Processing time:",
    result["processing_time_ms"],
    "ms"
)

print(
    "Errors:",
    result["errors"]
)


for entity in result["entities"]:

    confidence = entity[
        "extraction_confidence"
    ]

    if confidence >= 0.90:
        level = "GREEN"

    elif confidence >= 0.70:
        level = "YELLOW"

    else:
        level = "RED"

    print(
        f"{level} "
        f"{entity['entity_type']}: "
        f"{entity['value']} "
        f"→ "
        f"{entity['normalized_value']}"
    )


# Verify JSON serialization.

json.dumps(
    result,
    indent=2
)

print(
    "JSON serialization: PASS"
)

```

---

# Required Pipeline Tests

## Test 1 — Commercial Invoice

Expected:

```text
document_type = commercial_invoice
entities >= 8

```

Every entity should contain:

```text
bbox
extraction_confidence
classification_confidence
normalized_value

```

---

## Test 2 — Packing List

Expected:

```text
document_type = packing_list
entities >= 4

```

---

## Test 3 — AWB

Expected:

```text
document_type = awb
entities >= 5

```

---

## Test 4 — Normalization Integration

Input:

```text
"1,000.00 LBS"

```

Expected:

```text
value             = "1,000.00 LBS"
normalized_value  = 453.592
unit              = "kg"

```

---

## Test 5 — BBox Integration

Input OCR:

```text
450.00
KG

```

Expected entity bbox:

```text
bbox covering both OCR tokens

```

---

## Test 6 — Cache Integration

First semantic normalization:

```text
DB MISS
→ Gemini
→ DB INSERT

```

Second normalization:

```text
DB HIT
→ No Gemini

```

---

## Test 7 — Invalid PDF

Expected:

```json
{
  "document_type": "unknown",
  "entities": [],
  "errors": ["..."]
}

```

No uncaught exception.

---

## Test 8 — Empty PDF

Expected:

```text
entities = []

```

and no pipeline crash.

---

## Test 9 — Gemini Failure

Expected:

```text
errors[] populated
pipeline continues where possible

```

---

## Test 10 — Database Failure

Expected:

```text
normalization continues
deterministic rules still work

```

---

## Test 11 — JSON Serialization

Must succeed:

```python
json.dumps(result)

```

No:

```text
numpy.float32
datetime object
custom Python object

```

should remain in the final contract.

---

# Optional Table / Line-Item Extraction

Table extraction is not a blocking requirement for the core pipeline.

If implemented:

```text
OCR
 │
 ▼
Table Extraction
 │
 ▼
Line Items
 │
 └────→ Master Result

```

Example:

```json
{
  "row_index": 1,
  "description": "100% Cotton Fabric",
  "quantity": 5000,
  "unit": "meters",
  "unit_price": 2.50,
  "total_price": 12500.00,
  "page": 1,
  "bbox": [100, 400, 900, 440],
  "confidence": 0.91
}

```

The table extractor must not block header entity extraction.

---

# Final Master Flow

```text
                     USER UPLOAD
                          │
                          ▼
                     DOSSIER
                          │
                          ▼
                    DOCUMENT PDF
                          │
                          ▼
                  ┌──────────────┐
                  │     OCR      │
                  │  PaddleOCR   │
                  └──────┬───────┘
                         │
                    text + bbox
                         │
                         ▼
                  ┌──────────────┐
                  │ CLASSIFIER    │
                  │ heuristic →   │
                  │ Gemini fallback│
                  └──────┬───────┘
                         │
                  document type
                         │
                         ▼
                  ┌──────────────┐
                  │   GEMINI      │
                  │   ENTITY      │
                  │  EXTRACTION   │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ BBOX MAPPING  │
                  │ Gemini ↔ OCR  │
                  └──────┬───────┘
                         │
                    RAW ENTITY
                         │
                         ▼
                  ┌──────────────┐
                  │ NORMALIZER   │
                  │              │
                  │ Rules first  │
                  │      │       │
                  │ PostgreSQL   │
                  │      │       │
                  │ Gemini miss  │
                  └──────┬───────┘
                         │
              normalized_value
                    + unit
                    + warn
                         │
                         ▼
                  ┌──────────────┐
                  │ CONFIDENCE   │
                  │   SCORING    │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ DEDUP /      │
                  │ VALIDATION   │
                  └──────┬───────┘
                         │
                         ▼
               ┌─────────────────────┐
               │ MASTER EXTRACTION   │
               │       RESULT        │
               └──────────┬──────────┘
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
       ALOKA / REASONING        KAVEEN / FRONTEND
             │                         │
             ▼                         ▼
       Knowledge Graph            PDF Viewer
       Cross-document             BBox Overlay
       comparison                 Entity display
       Conflict detection          Confidence UI
       Layer 2 XAI                 Layer 1 XAI
       Layer 3 XAI

```

---

# Integration Contract

## Aloka

Aloka should consume:

```text
document_type
classification_confidence
entities[]
normalized_value
unit
extraction_confidence
classification_confidence

```

For cross-document comparison:

```text
normalized_value

```

should be preferred over raw `value`.

---

## Kaveen

Kaveen should consume:

```text
page
bbox
value
entity_type
extraction_confidence

```

for visual attribution.

The bbox must correspond to the original page image coordinates.

---

# Acceptance Criteria

-  `process_document()` is the single document-processing entry point
-  OCR runs first
-  Classification occurs before entity extraction
-  Entity extraction receives document type
-  Every extracted entity is normalized
-  Raw values remain unchanged
-  Every successful entity has a bbox or explicit `null`
-  Every entity has extraction confidence
-  Every entity has classification confidence
-  Normalization warnings are propagated
-  PostgreSQL-backed Phase 09 is used
-  Semantic cache hits avoid Gemini
-  Deterministic normalization does not call Gemini
-  Multi-page documents are supported
-  Duplicate identical header entities are controlled
-  Genuine conflicting values are not silently discarded
-  Raw OCR is included in the final result
-  Processing time is measured
-  Invalid PDFs return errors instead of crashing
-  Gemini failures are handled gracefully
-  Database failures are handled gracefully
-  Final result is JSON serializable
-  Mock pipeline follows identical schema
-  Aloka can consume the result
-  Kaveen can consume page/bbox data
-  Complete pipeline runs within the demo target of <30 seconds/document

---

# Outputs

Create/update:

```text
backend/ai_pipeline/pipeline.py
backend/ai_pipeline/mock_pipeline.py
backend/ai_pipeline/test_pipeline.py

```

The pipeline depends on:

```text
backend/ai_pipeline/ocr_engine.py
backend/ai_pipeline/classifier.py
backend/ai_pipeline/entity_extractor.py
backend/ai_pipeline/confidence.py
backend/ai_pipeline/normalizer.py

```

Database dependency:

```text
norm_cache

```

from Phase 09.

---

# Critical Handoff

When the real pipeline passes all tests:

```text
1. Tell Aloka:
   "Real pipeline is ready — switch from mock to real."

2. Aloka calls:
   pipeline.process_document(...)

3. Kaveen receives:
   page + bbox + entity data

4. The Dossier layer stores:
   document processing results

5. Aloka combines multiple document results:
   into the Shipment Knowledge Graph.

```

---

# Final Definition of Done

The implementation is complete when this works:

```python
result = pipeline.process_document(
    pdf_path="invoice.pdf",
    document_id="doc_001"
)

```

and produces:

```text
REAL PDF
   ↓
REAL OCR
   ↓
REAL classification
   ↓
REAL Gemini extraction
   ↓
REAL OCR bbox mapping
   ↓
REAL normalization
   ↓
REAL PostgreSQL cache
   ↓
REAL confidence
   ↓
VALID MASTER JSON
   ↓
┌───────────────┬─────────────────┐
│               │                 │
▼               ▼                 ▼
Aloka           Kaveen            Dossier
Reasoning       Frontend          Storage
Graph           XAI               Status

```

The pipeline's responsibility is:

> **Turn one raw shipping document into one trustworthy, structured, normalized, explainable document result that every downstream component can consume without knowing how the AI pipeline works internally.**