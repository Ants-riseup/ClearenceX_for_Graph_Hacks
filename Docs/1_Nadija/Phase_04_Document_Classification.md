# Phase 03 — Document Classification

> **Priority:** MUST
> **Estimated Time:** 2–3 hours
> **Dependencies:** Phase 02 (OCR working)
> **Blocks:** Phase 05 (entity extraction needs to know doc type)

---

## Goal

Build a classifier that identifies what type of shipping document each uploaded PDF is. The system needs to know if a PDF is a Commercial Invoice, Packing List, AWB, B/L, etc. before it can extract the right entities.

## Why

- Different document types have different entity schemas (invoices have prices, AWBs have flight numbers)
- Classification confidence feeds into Layer 3 XAI (decomposed confidence)
- Misclassification is a common failure mode — surfacing it builds trust

## Interface

### Input
```python
def classify_document(ocr_output: OcrOutput) -> ClassificationResult:
```

### Output Schema
```python
@dataclass
class ClassificationResult:
    document_type: str        # "commercial_invoice", "packing_list", "awb", "bl", "freight_invoice", "delivery_order", "letter_of_credit"
    confidence: float         # 0.0 to 1.0
    all_scores: dict          # {"commercial_invoice": 0.97, "packing_list": 0.02, ...}
    evidence: list[str]       # Keywords/patterns that drove the classification
```

## Document Types to Classify

| Type Key | Full Name | Key Indicators |
|---|---|---|
| `commercial_invoice` | Commercial Invoice | "Invoice", "Unit Price", "Total Amount", invoice number pattern |
| `packing_list` | Packing List | "Packing List", "Carton", "Net Weight", "Gross Weight", roll/bale counts |
| `awb` | Airway Bill (HAWB/MAWB) | "Air Waybill", "MAWB", "HAWB", flight number, IATA codes |
| `bl` | Bill of Lading | "Bill of Lading", "B/L", vessel name, port of loading |
| `freight_invoice` | Freight Invoice | "Freight", "Charges", "THC", "Documentation Fee" |
| `delivery_order` | Delivery Order / FAN | "Delivery Order", "Freight Arrival Notice", "DO" |
| `letter_of_credit` | Letter of Credit | "L/C", "Letter of Credit", "Documentary Credit", bank name |

## Tasks

### 3.1 Approach A — Keyword Heuristic (Fast, ~80% accuracy)

Start with this. It works for demo and can be the fallback:

```python
# backend/ai_pipeline/classifier.py

DOCUMENT_SIGNATURES = {
    "commercial_invoice": {
        "keywords": ["invoice", "unit price", "total amount", "commercial invoice", "inv no", "invoice no"],
        "weight": 1.0
    },
    "packing_list": {
        "keywords": ["packing list", "carton", "net weight", "gross weight", "bale", "roll", "packing"],
        "weight": 1.0
    },
    "awb": {
        "keywords": ["air waybill", "airway bill", "mawb", "hawb", "flight", "iata", "awb"],
        "weight": 1.0
    },
    "bl": {
        "keywords": ["bill of lading", "b/l", "vessel", "port of loading", "port of discharge", "shipper"],
        "weight": 1.0
    },
    "freight_invoice": {
        "keywords": ["freight", "charges", "thc", "documentation fee", "handling"],
        "weight": 0.8
    },
    "delivery_order": {
        "keywords": ["delivery order", "freight arrival", "do no", "arrival notice"],
        "weight": 0.8
    },
    "letter_of_credit": {
        "keywords": ["letter of credit", "l/c", "documentary credit", "issuing bank", "beneficiary"],
        "weight": 1.0
    }
}

class DocumentClassifier:
    def classify(self, ocr_output) -> ClassificationResult:
        # Combine all text from first 2 pages (usually enough for classification)
        full_text = ""
        for page in ocr_output.pages[:2]:
            full_text += " ".join([t.text for t in page.tokens]) + " "
        full_text_lower = full_text.lower()
        
        scores = {}
        evidence = {}
        
        for doc_type, sig in DOCUMENT_SIGNATURES.items():
            matched_keywords = [kw for kw in sig["keywords"] if kw in full_text_lower]
            score = (len(matched_keywords) / len(sig["keywords"])) * sig["weight"]
            scores[doc_type] = round(score, 3)
            evidence[doc_type] = matched_keywords
        
        # Get best match
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        
        # Normalize confidence
        total = sum(scores.values()) or 1
        normalized_scores = {k: round(v / total, 3) for k, v in scores.items()}
        
        return ClassificationResult(
            document_type=best_type,
            confidence=normalized_scores[best_type],
            all_scores=normalized_scores,
            evidence=evidence[best_type]
        )
```

### 3.2 Approach B — Gemini Vision API (Higher accuracy, ~95%)

If keyword heuristic isn't accurate enough:

```python
class GeminiClassifier:
    def __init__(self):
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def classify(self, pdf_path: str) -> ClassificationResult:
        # Convert first page to image
        images = convert_from_path(pdf_path, first_page=1, last_page=1)
        
        prompt = """Classify this shipping/trade document into exactly one of these types:
        - commercial_invoice
        - packing_list
        - awb (airway bill)
        - bl (bill of lading)
        - freight_invoice
        - delivery_order
        - letter_of_credit
        
        Return JSON only:
        {"document_type": "...", "confidence": 0.95, "evidence": ["keyword1", "keyword2"]}"""
        
        response = self.model.generate_content([prompt, images[0]])
        # Parse JSON response
        ...
```

### 3.3 Combine Both (Recommended)

Use keyword heuristic first. If confidence < 0.7, fall back to Gemini Vision.

## Acceptance Criteria

- [ ] Correctly classifies Commercial Invoice, Packing List, and AWB (minimum 3 types)
- [ ] Returns confidence score between 0.0 and 1.0
- [ ] Returns evidence (which keywords/features drove the decision)
- [ ] Returns scores for ALL document types (not just the winner)
- [ ] Handles unknown document types gracefully (returns lowest confidence)
- [ ] Classification runs in < 5 seconds per document

## Outputs

- `backend/ai_pipeline/classifier.py` — classifier module
- Classification confidence feeds into Aloka's Layer 3 (decomposed confidence)

## Handoff

Aloka needs `classification_confidence` and `document_type` to build the reasoning engine. Share your classifier output format so he can integrate.
