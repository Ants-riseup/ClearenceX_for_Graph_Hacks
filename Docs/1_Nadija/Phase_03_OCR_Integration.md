# Phase 02 — OCR Integration: Text + Bounding Boxes

> **Priority:** MUST
> **Estimated Time:** 2–3 hours
> **Dependencies:** Phase 01 (environment setup)
> **Blocks:** Phases 03, 05, 06

---

## Goal

Build the OCR engine module that takes a PDF file and returns structured text with spatial coordinates (bounding boxes) for every text region on every page. This is the foundation for Layer 1 XAI (Visual Attribution).

## Why

Bounding boxes are essential for:
- **Layer 1 XAI:** Click any field → see exactly where it came from in the PDF
- **Entity extraction:** LayoutLMv3 needs spatial coordinates
- **Knowledge graph provenance:** Every value traces back to a pixel location

## Interface

### Input
```python
def extract_ocr(pdf_path: str) -> OcrOutput:
```

### Output Schema
```python
@dataclass
class OcrToken:
    text: str
    page: int              # 1-indexed
    bbox: list[float]      # [x1, y1, x2, y2] in pixel coordinates
    confidence: float      # 0.0 to 1.0

@dataclass  
class OcrPage:
    page_number: int
    width: int             # page width in pixels
    height: int            # page height in pixels
    tokens: list[OcrToken]

@dataclass
class OcrOutput:
    file_path: str
    total_pages: int
    pages: list[OcrPage]
```

## Tasks

### 2.1 Create `ocr_engine.py`

```python
# backend/ai_pipeline/ocr_engine.py
from paddleocr import PaddleOCR
from dataclasses import dataclass, asdict
from pdf2image import convert_from_path
import json

@dataclass
class OcrToken:
    text: str
    page: int
    bbox: list  # [x1, y1, x2, y2]
    confidence: float

@dataclass
class OcrPage:
    page_number: int
    width: int
    height: int
    tokens: list

@dataclass
class OcrOutput:
    file_path: str
    total_pages: int
    pages: list

class OcrEngine:
    def __init__(self):
        self.ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)
    
    def extract(self, pdf_path: str) -> OcrOutput:
        """Extract text + bounding boxes from all pages of a PDF."""
        result = self.ocr.ocr(pdf_path, cls=True)
        
        # Get page dimensions
        images = convert_from_path(pdf_path)
        
        pages = []
        for page_idx, (page_result, img) in enumerate(zip(result, images)):
            tokens = []
            if page_result:
                for line in page_result:
                    bbox_raw = line[0]  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
                    text = line[1][0]
                    confidence = float(line[1][1])
                    
                    # Convert quadrilateral to [x1, y1, x2, y2] bounding box
                    x_coords = [p[0] for p in bbox_raw]
                    y_coords = [p[1] for p in bbox_raw]
                    bbox = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
                    
                    tokens.append(OcrToken(
                        text=text,
                        page=page_idx + 1,
                        bbox=bbox,
                        confidence=confidence
                    ))
            
            pages.append(OcrPage(
                page_number=page_idx + 1,
                width=img.width,
                height=img.height,
                tokens=tokens
            ))
        
        return OcrOutput(
            file_path=pdf_path,
            total_pages=len(pages),
            pages=pages
        )
    
    def to_dict(self, output: OcrOutput) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "file_path": output.file_path,
            "total_pages": output.total_pages,
            "pages": [
                {
                    "page_number": p.page_number,
                    "width": p.width,
                    "height": p.height,
                    "tokens": [
                        {
                            "text": t.text,
                            "page": t.page,
                            "bbox": t.bbox,
                            "confidence": t.confidence
                        } for t in p.tokens
                    ]
                } for p in output.pages
            ]
        }
```

### 2.2 Test with a Sample PDF

```python
# backend/ai_pipeline/test_ocr.py
from ocr_engine import OcrEngine
import json

engine = OcrEngine()
result = engine.extract("path/to/sample_invoice.pdf")

# Print summary
for page in result.pages:
    print(f"\n--- Page {page.page_number} ({page.width}x{page.height}) ---")
    for token in page.tokens[:10]:  # First 10 tokens
        print(f"  [{token.confidence:.2f}] {token.text}")
        print(f"    BBox: {token.bbox}")

# Save full output
with open("ocr_output_sample.json", "w") as f:
    json.dump(engine.to_dict(result), f, indent=2)
```

### 2.3 Handle Edge Cases

- **Scanned PDFs:** PaddleOCR handles these natively
- **Multi-column layouts:** PaddleOCR's detection should handle this, but verify
- **Rotated text:** `use_angle_cls=True` handles rotation
- **Empty pages:** Return empty tokens list, don't crash
- **Large PDFs (>10 pages):** Should still work, just slower

## Acceptance Criteria

- [ ] `OcrEngine.extract()` returns `OcrOutput` for any PDF
- [ ] Every text region has a bounding box `[x1, y1, x2, y2]`
- [ ] Page dimensions (width, height) are captured
- [ ] Confidence scores are between 0.0 and 1.0
- [ ] Output is JSON-serializable
- [ ] Works on at least 3 different PDF layouts (invoice, packing list, AWB)
- [ ] Empty/corrupt PDFs don't crash — return error gracefully

## Outputs

- `backend/ai_pipeline/ocr_engine.py` — production module
- Sample OCR output JSON for Aloka to test reasoning engine against

## Handoff

Share a sample `ocr_output_sample.json` with Aloka so he can start building the knowledge graph against real OCR output structure.
