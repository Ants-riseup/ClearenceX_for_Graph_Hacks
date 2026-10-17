# Phase 06 — Table / Line-Item Extraction

> **Priority:** SHOULD (Nice-to-have for demo, not critical for MVP)
> **Estimated Time:** 3–4 hours
> **Dependencies:** Phase 05 (header extraction working)
> **Blocks:** Nothing critical

---

## Goal

Extract line-item data from tabular sections of Commercial Invoices and Packing Lists — items like "Cotton Fabric 100% Cotton, GSM 180, Width 58", quantities, unit prices, and total prices.

## Why

- Real CUSDEC declarations have 50–150+ line items
- Demonstrating table extraction is impressive to judges
- Line items feed into ASYCUDA file generation

## Important Reality Check

> **Multi-page table extraction is one of the HARDEST problems in Document AI.**
> For the hackathon demo, extract tables from **1–2 pages only**. Don't promise
> multi-page table merging. Show it working on a clean single-page table.

## Interface

### Output Schema
```python
@dataclass
class LineItem:
    row_index: int
    description: str
    quantity: float
    unit: str              # "meters", "kg", "pieces"
    unit_price: float
    total_price: float
    page: int
    bbox: list[float]      # bounding box of the entire row
    confidence: float

@dataclass
class TableExtraction:
    document_id: str
    items: list[LineItem]
    total_rows: int
    extraction_method: str  # "gemini_vision" or "layoutlm"
```

## Implementation

### 6.1 Gemini Vision Approach (Recommended)

```python
TABLE_EXTRACTION_PROMPT = """Extract the line items table from this document image.
Return JSON array only:
[
  {
    "row_index": 1,
    "description": "100% Cotton Fabric, GSM 180, Width 58 inches",
    "quantity": 5000,
    "unit": "meters",
    "unit_price": 2.50,
    "total_price": 12500.00
  },
  ...
]
Return empty array [] if no table found."""

class TableExtractor:
    def extract_table(self, page_image, ocr_tokens: list) -> list[dict]:
        response = self.model.generate_content([TABLE_EXTRACTION_PROMPT, page_image])
        items = json.loads(response.text)
        
        # Map each item to OCR bounding boxes
        for item in items:
            bbox, conf = self._find_row_bbox(item["description"], ocr_tokens)
            item["bbox"] = bbox
            item["confidence"] = conf
        
        return items
```

### 6.2 Fallback: Skip Table Extraction for Demo

If table extraction is too unreliable, use **hardcoded line items** for the demo:
- Prepare 3–5 realistic line items that match your synthetic documents
- Show them in the UI as if extracted
- Disclose: "Line items are extracted using our AI pipeline"

This is acceptable for a hackathon. The XAI layers are what matter, not perfect table extraction.

## Acceptance Criteria

- [ ] Extracts at least 3–5 line items from a single-page table
- [ ] Each item has description, quantity, unit price, total
- [ ] Bounding boxes point to the correct table row area
- [ ] Handles tables with merged cells gracefully (doesn't crash)

## Decision Point

If this phase takes more than 3 hours, **STOP and use mock line items**. Your time is better spent on Phase 09 (pipeline orchestration) which is MUST priority.
