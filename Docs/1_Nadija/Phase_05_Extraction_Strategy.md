# Phase 05 — Entity Extraction Strategy Decision

> **Priority:** MUST (Decision gate — do this before Phase 06)
> **Estimated Time:** 1 hour
> **Dependencies:** Phase 03 (OCR working), Phase 04 (classifier working)
> **Blocks:** Phase 06, 07
> **⚠️ Aloka Dependency:** Your extraction output feeds directly into `knowledge_graph.py` — the graph reads `entity.get("normalized_value", entity["value"])` so normalized values from Phase 09 are critical for accurate conflict detection.

---

## Goal

Decide which extraction approach to use for the hackathon demo. This is a **decision point**, not an implementation phase.

## Why

LayoutLMv3 fine-tuning is powerful but requires annotated training data and significant time. For a hackathon with tight deadlines, we need to choose the approach that gives the best demo quality with available time.

## Options

### Option A: LayoutLMv3 Fine-tuned NER

| Pros | Cons |
|---|---|
| State-of-the-art document understanding | Needs 200+ BIO-annotated pages |
| Uses text + layout + visual features | Fine-tuning takes hours + GPU |
| Looks impressive to judges | Risk of poor results without enough data |
| Bounding boxes come from model | Complex to debug |

**Choose if:** You have 2+ days dedicated AND synthetic annotated data is ready.

### Option B: Gemini Vision API (Recommended for Hackathon)

| Pros | Cons |
|---|---|
| No training data needed | API cost (minimal for demo) |
| Works out-of-the-box on any layout | No native bounding boxes (must map back to OCR) |
| Very high accuracy on structured docs | Depends on internet + API availability |
| Fast to implement (hours, not days) | Less "ML-impressive" to judges |

**Choose if:** Time is tight and you need reliable extraction fast.

### Option C: Hybrid (Best of Both)

1. **PaddleOCR** for text + bounding boxes (you already have this)
2. **Gemini Vision** to understand the document and identify entities
3. **Map** Gemini's extracted values back to PaddleOCR bounding boxes via text matching

This gives you:
- ✅ Bounding boxes (from PaddleOCR)
- ✅ Accurate extraction (from Gemini)
- ✅ No training data needed
- ✅ Works on any layout

## Recommended Decision: Option C (Hybrid)

```
PDF → PaddleOCR → text + bounding boxes (Phase 02 ✓)
PDF → Gemini Vision → entity names + values (Phase 05)
Map Gemini results → PaddleOCR bounding boxes (Phase 05)
Result: entities with bounding boxes and confidence
```

### How to Map Gemini Output to OCR Bounding Boxes

```python
def map_to_bbox(gemini_value: str, ocr_tokens: list[OcrToken]) -> OcrToken | None:
    """Find the OCR token that best matches a Gemini-extracted value."""
    from difflib import SequenceMatcher
    
    best_match = None
    best_ratio = 0.0
    
    for token in ocr_tokens:
        ratio = SequenceMatcher(None, gemini_value.lower(), token.text.lower()).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = token
    
    if best_ratio >= 0.6:  # Threshold
        return best_match
    return None
```

## Decision Checklist

- [ ] Do I have annotated training data? → If No, choose Option B or C
- [ ] Do I have a GPU available? → If No, choose Option B or C
- [ ] Do I have 2+ full days for AI work? → If No, choose Option C
- [ ] Is Gemini API available and working? → If No, choose Option A

## Action

Write your decision here and communicate it to the team:

```
DECISION: Option C — Hybrid (PaddleOCR + Gemini Vision)
REASON: No annotated training data available, no GPU, tight hackathon timeline.
        PaddleOCR already gives us bounding boxes (Phase 03 ✓).
        Gemini Vision gives accurate extraction with zero training data.
        Mapping Gemini values back to OCR tokens via SequenceMatcher covers XAI Layer 1.
TIME IMPACT: Phase 06 implementation can start immediately. Estimated 3–4 hours.
```

Then proceed to Phase 06.

---

## 🔗 Cross-Team Impact

Aloka's `ShipmentKnowledgeGraph` (`backend/reasoning/knowledge_graph.py`) consumes your extraction output with this exact lookup:
```python
value = entity.get("normalized_value", entity["value"])  # prefers normalized_value
confidence = entity.get("extraction_confidence", 0.5)
```

This means **Phase 09 (Normalization) is not optional** — without `normalized_value`, the graph will use raw strings and numeric comparisons will fail, causing false conflict detections.

---

## 🚧 Extraction Responsibility Boundary

The extraction phase (Phase 06) is responsible for **faithfully capturing what the OCR saw**. It must **not** attempt to normalize, convert, or clean values inline.

| Responsibility | Phase |
|---|---|
| Extract raw OCR text (`value`) | Phase 06 — `entity_extractor.py` |
| Map to bounding box | Phase 06 — `entity_extractor.py` |
| Convert units, dates, identifiers | Phase 09 — `normalizer.py` |
| Populate `normalized_value` + `unit` | Phase 09 — `normalizer.py` |

If you see `"450.00 KG"` in the OCR output, `value` should be `"450.00 KG"`. Phase 09 will populate `normalized_value: 450.0` and `unit: "kg"`.
