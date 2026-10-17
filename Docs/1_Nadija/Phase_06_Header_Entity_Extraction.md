# Phase 06 — Header Entity Extraction

> **Priority:** MUST
> **Estimated Time:** 3–4 hours
> **Dependencies:** Phase 03, 04, 05
> **Blocks:** Phase 10 (pipeline orchestration)

---

## Goal

Extract header-level metadata from each document type: invoice number, consignee name, gross weight, net weight, package count, Incoterms, etc. These are the entities that get cross-referenced across documents for discrepancy detection.

## Why

This is the core AI contribution. Every XAI layer downstream depends on accurate entity extraction with bounding boxes. Header entities are the primary fields for cross-document reconciliation.

## Entities to Extract Per Document Type

### Commercial Invoice
| Entity | Key | Example |
|---|---|---|
| Invoice Number | `INVOICE_NUMBER` | "INV-2024-1023" |
| Invoice Date | `INVOICE_DATE` | "2024-08-15" |
| Consignee Name | `CONSIGNEE_NAME` | "ABC Textiles Ltd" |
| Consignee Address | `CONSIGNEE_ADDRESS` | "42 Galle Road, Colombo" |
| Shipper Name | `SHIPPER_NAME` | "XYZ Fabrics Co." |
| Incoterm | `INCOTERM` | "FOB Colombo" |
| Payment Terms | `PAYMENT_TERMS` | "T/T 30 Days" |
| Total Amount | `TOTAL_AMOUNT` | "45,230.00 USD" |
| Currency | `CURRENCY` | "USD" |
| Gross Weight | `GROSS_WEIGHT` | "450.00 KG" |
| Net Weight | `NET_WEIGHT` | "420.00 KG" |
| Package Count | `PACKAGE_COUNT` | "25 Cartons" |

### Packing List
| Entity | Key | Example |
|---|---|---|
| Gross Weight | `GROSS_WEIGHT` | "450.00 KG" |
| Net Weight | `NET_WEIGHT` | "420.00 KG" |
| Tare Weight | `TARE_WEIGHT` | "30.00 KG" |
| Package Count | `PACKAGE_COUNT` | "25 Cartons" |
| Total Volume | `VOLUME` | "12.5 CBM" |
| Shipping Marks | `SHIPPING_MARKS` | "ABC-2024/COL" |

### Airway Bill (AWB)
| Entity | Key | Example |
|---|---|---|
| AWB Number | `AWB_NUMBER` | "631-12345678" |
| Flight Number | `FLIGHT_NUMBER` | "UL 504" |
| Origin | `ORIGIN` | "CMB (Colombo)" |
| Destination | `DESTINATION` | "LHR (London)" |
| Gross Weight | `GROSS_WEIGHT` | "448.50 KG" |
| Package Count | `PACKAGE_COUNT` | "25 Pieces" |
| Shipper | `SHIPPER_NAME` | "XYZ Fabrics Co." |
| Consignee | `CONSIGNEE_NAME` | "ABC Textiles Ltd" |

### Bill of Lading
| Entity | Key | Example |
|---|---|---|
| BL Number | `BL_NUMBER` | "MAEU123456789" |
| Vessel Name | `VESSEL_NAME` | "MSC ANNA" |
| Port of Loading | `PORT_LOADING` | "Colombo" |
| Port of Discharge | `PORT_DISCHARGE` | "Felixstowe" |
| Gross Weight | `GROSS_WEIGHT` | "450.00 KG" |
| Package Count | `PACKAGE_COUNT` | "25 Cartons" |
| Container Number | `CONTAINER_NUMBER` | "MSKU1234567" |

## Implementation (Hybrid Approach — Option C from Phase 04)

### 5.1 Create `entity_extractor.py`

```python
# backend/ai_pipeline/entity_extractor.py
import google.generativeai as genai
import json
import os
from difflib import SequenceMatcher

EXTRACTION_PROMPTS = {
    "commercial_invoice": """Extract these fields from this Commercial Invoice image.
Return JSON only, no other text:
{
  "INVOICE_NUMBER": "value or null",
  "INVOICE_DATE": "value or null",
  "CONSIGNEE_NAME": "value or null",
  "SHIPPER_NAME": "value or null",
  "INCOTERM": "value or null",
  "PAYMENT_TERMS": "value or null",
  "TOTAL_AMOUNT": "value or null",
  "CURRENCY": "value or null",
  "GROSS_WEIGHT": "value or null",
  "NET_WEIGHT": "value or null",
  "PACKAGE_COUNT": "value or null"
}""",

    "packing_list": """Extract these fields from this Packing List image.
Return JSON only, no other text:
{
  "GROSS_WEIGHT": "value or null",
  "NET_WEIGHT": "value or null",
  "TARE_WEIGHT": "value or null",
  "PACKAGE_COUNT": "value or null",
  "VOLUME": "value or null",
  "SHIPPING_MARKS": "value or null"
}""",

    "awb": """Extract these fields from this Air Waybill image.
Return JSON only, no other text:
{
  "AWB_NUMBER": "value or null",
  "FLIGHT_NUMBER": "value or null",
  "ORIGIN": "value or null",
  "DESTINATION": "value or null",
  "GROSS_WEIGHT": "value or null",
  "PACKAGE_COUNT": "value or null",
  "SHIPPER_NAME": "value or null",
  "CONSIGNEE_NAME": "value or null"
}""",

    "bl": """Extract these fields from this Bill of Lading image.
Return JSON only, no other text:
{
  "BL_NUMBER": "value or null",
  "VESSEL_NAME": "value or null",
  "PORT_LOADING": "value or null",
  "PORT_DISCHARGE": "value or null",
  "GROSS_WEIGHT": "value or null",
  "PACKAGE_COUNT": "value or null",
  "CONTAINER_NUMBER": "value or null"
}"""
}


class EntityExtractor:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def extract(self, page_image, document_type: str, ocr_tokens: list) -> list[dict]:
        """
        Extract entities using Gemini Vision, then map to OCR bounding boxes.
        
        Returns list of:
        {
            "entity_type": "GROSS_WEIGHT",
            "value": "450.00 KG",
            "normalized_value": 450.0,
            "unit": "kg",
            "page": 1,
            "bbox": [120, 240, 410, 290],
            "extraction_confidence": 0.94
        }
        """
        prompt = EXTRACTION_PROMPTS.get(document_type)
        if not prompt:
            return []
        
        # Call Gemini Vision
        response = self.model.generate_content([prompt, page_image])
        
        # Parse JSON from response
        try:
            raw_text = response.text.strip()
            # Remove markdown code blocks if present
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0]
            entities_raw = json.loads(raw_text)
        except (json.JSONDecodeError, IndexError):
            return []
        
        # Map each extracted value to OCR bounding boxes
        entities = []
        for entity_type, value in entities_raw.items():
            if value is None or value == "null":
                continue
            
            # Find matching OCR token for bounding box
            bbox, ocr_confidence = self._find_bbox(str(value), ocr_tokens)
            
            entities.append({
                "entity_type": entity_type,
                "value": str(value),
                "page": ocr_tokens[0].page if ocr_tokens else 1,
                "bbox": bbox,
                "extraction_confidence": ocr_confidence
            })
        
        return entities
    
    def _find_bbox(self, value: str, ocr_tokens: list) -> tuple:
        """Find the best matching OCR token for a Gemini-extracted value."""
        best_match_bbox = [0, 0, 100, 30]  # default fallback
        best_confidence = 0.5
        best_ratio = 0.0
        
        value_lower = value.lower().strip()
        
        for token in ocr_tokens:
            token_text = token.text.lower().strip()
            
            # Check if value appears within token or vice versa
            if value_lower in token_text or token_text in value_lower:
                ratio = 0.9
            else:
                ratio = SequenceMatcher(None, value_lower, token_text).ratio()
            
            if ratio > best_ratio:
                best_ratio = ratio
                best_match_bbox = token.bbox
                best_confidence = token.confidence
        
        # Blend: Gemini extracted it (high confidence) + OCR read it (ocr_confidence)
        final_confidence = min(0.95, best_confidence) if best_ratio > 0.6 else 0.5
        
        return best_match_bbox, round(final_confidence, 2)
```

### 5.2 Test on Sample Documents

```python
# Test with a commercial invoice
from pdf2image import convert_from_path
from ocr_engine import OcrEngine
from classifier import DocumentClassifier
from entity_extractor import EntityExtractor

ocr = OcrEngine()
classifier = DocumentClassifier()
extractor = EntityExtractor()

# Run pipeline
ocr_result = ocr.extract("sample_invoice.pdf")
doc_type = classifier.classify(ocr_result)
print(f"Document type: {doc_type.document_type} ({doc_type.confidence:.0%})")

# Extract entities from first page
images = convert_from_path("sample_invoice.pdf")
entities = extractor.extract(images[0], doc_type.document_type, ocr_result.pages[0].tokens)

for e in entities:
    print(f"  {e['entity_type']}: {e['value']} (conf: {e['extraction_confidence']:.0%})")
    print(f"    BBox: {e['bbox']}")
```

## Acceptance Criteria

- [ ] Extracts at least 8 header entities from a Commercial Invoice
- [ ] Extracts at least 4 header entities from a Packing List
- [ ] Extracts at least 5 header entities from an AWB
- [ ] Every extracted entity has a bounding box mapped from OCR
- [ ] Every entity has an extraction confidence score
- [ ] Returns empty list (not crash) for unknown document types
- [ ] Handles Gemini API failures gracefully

## Outputs

- `backend/ai_pipeline/entity_extractor.py` — extractor module
- Extracted entities ready for Aloka's knowledge graph

## Handoff to Aloka

Share sample extraction output. Aloka's `ShipmentKnowledgeGraph` reads these fields:
- `entity_type` — must match keys in `CROSS_DOCUMENT_FIELDS` (e.g. `GROSS_WEIGHT`, `CONSIGNEE_NAME`, `INCOTERM`)
- `normalized_value` — **required** for numeric comparisons in conflict detection
- `extraction_confidence` — stored on graph edges, used for Layer 3 XAI
- `value` — used as fallback if `normalized_value` is missing
- `page`, `bbox` — used by Kaveen for PDF overlay (Layer 1 XAI)

```json
[
  {
    "entity_type": "GROSS_WEIGHT",
    "value": "450.00 KG",
    "normalized_value": 450.0,
    "unit": "kg",
    "page": 1,
    "bbox": [120, 240, 410, 290],
    "extraction_confidence": 0.94
  },
  {
    "entity_type": "CONSIGNEE_NAME",
    "value": "ABC Textiles Ltd",
    "normalized_value": "ABC Textiles Ltd",
    "unit": null,
    "page": 1,
    "bbox": [50, 100, 300, 130],
    "extraction_confidence": 0.91
  }
]
```

> ⚠️ **Critical:** The knowledge graph's conflict detection uses `CROSS_DOCUMENT_FIELDS = ["GROSS_WEIGHT", "NET_WEIGHT", "PACKAGE_COUNT", "CONSIGNEE_NAME", "SHIPPER_NAME", "INCOTERM"]`. These 6 fields are the primary conflict triggers — make sure extraction is accurate for these specifically.

---

## 🚧 Extraction Responsibility Boundary

This phase is responsible only for **faithfully capturing what the OCR saw and mapping it to a bounding box**. Do NOT normalize, convert, or clean values inside `entity_extractor.py`.

| Responsibility | Owned By |
|---|---|
| Extract raw OCR text → `value` field | **Phase 06** — `entity_extractor.py` |
| Map extracted value to OCR bounding box | **Phase 06** — `entity_extractor.py` |
| Convert `"450.00 KG"` → `normalized_value: 450.0, unit: "kg"` | **Phase 09** — `normalizer.py` |
| Convert `"1000 lbs"` → `normalized_value: 453.592, unit: "kg"` | **Phase 09** — `normalizer.py` |
| Convert `"FOB Colombo"` → `normalized_value: "FOB"` | **Phase 09** — `normalizer.py` |
| Resolve `"Colombo Port"` → `"Colombo Port (LKCMB)"` via LLM cache | **Phase 09** — `normalizer.py` |

> **Rule:** `entity_extractor.py` populates `value` (raw string). `normalizer.py` populates `normalized_value` and `unit`. The pipeline (`pipeline.py`) calls both in sequence in Step 4 of `process_document()`. Keep them separate.
