# Phase 08 — Confidence Scoring

> **Priority:** MUST
> **Estimated Time:** 1–2 hours
> **Dependencies:** Phase 03, 04, 06
> **Blocks:** Phase 10 (pipeline needs confidence scores)
> **🔗 Aloka Integration:** Confidence scores are stored on graph edges in `knowledge_graph.py` — `self.graph.add_edge(..., confidence=confidence)`. They power Layer 3 XAI confidence decomposition.

---

## Goal

Create a module that computes extraction confidence scores for every entity. This feeds directly into Layer 3 XAI (Decomposed Confidence) — one of our key differentiators.

## Why

Layer 3 XAI decomposes confidence into three components:
- **Extraction confidence:** How well did OCR read the text?
- **Classification confidence:** How certain is the document type?
- **Matching confidence:** How closely do values match across documents? *(Aloka handles this)*

You provide the first two. Aloka adds the third.

## Interface

```python
@dataclass
class ConfidenceBreakdown:
    extraction: float       # 0.0–1.0 — OCR + NER confidence
    classification: float   # 0.0–1.0 — document type confidence
    # matching: float       ← Aloka adds this in the reasoning engine
```

## Implementation

### 7.1 Create `confidence.py`

```python
# backend/ai_pipeline/confidence.py

class ConfidenceScorer:
    """
    Computes extraction-side confidence for each entity.
    Aloka's reasoning engine adds the matching confidence later.
    """
    
    def compute_extraction_confidence(
        self,
        ocr_confidence: float,     # PaddleOCR's confidence for the matched token
        bbox_match_ratio: float,   # How well Gemini's value matched an OCR token (0-1)
        entity_type: str           # Some entities are harder than others
    ) -> float:
        """
        Combine OCR confidence and value-matching quality into one score.
        
        Logic:
        - If OCR read it clearly (high ocr_confidence) AND
          Gemini's value matches the OCR token well (high bbox_match_ratio)
          → High extraction confidence
        - If either is low → lower confidence
        """
        # Entity-specific difficulty factors
        DIFFICULTY = {
            "GROSS_WEIGHT": 0.95,      # Numbers are easy to OCR
            "NET_WEIGHT": 0.95,
            "PACKAGE_COUNT": 0.95,
            "TOTAL_AMOUNT": 0.93,
            "INVOICE_NUMBER": 0.90,     # Alphanumeric, harder
            "CONSIGNEE_NAME": 0.85,     # Names can be tricky
            "SHIPPER_NAME": 0.85,
            "INCOTERM": 0.92,           # Short standard terms
            "AWB_NUMBER": 0.90,
            "BL_NUMBER": 0.90,
            "VESSEL_NAME": 0.85,
            "PAYMENT_TERMS": 0.80,      # Variable formats
        }
        
        difficulty = DIFFICULTY.get(entity_type, 0.85)
        
        # Weighted combination
        raw_score = (
            0.4 * ocr_confidence +
            0.4 * bbox_match_ratio +
            0.2 * difficulty
        )
        
        # Clamp to [0.0, 1.0]
        return round(min(max(raw_score, 0.0), 1.0), 3)
    
    def compute_classification_confidence(
        self,
        classifier_confidence: float,  # From Phase 03 classifier
        evidence_count: int            # How many keywords matched
    ) -> float:
        """
        Classification confidence — how sure we are about the document type.
        """
        # More evidence = more confidence
        evidence_boost = min(evidence_count * 0.05, 0.15)  # Max +15% boost
        
        raw_score = classifier_confidence + evidence_boost
        return round(min(raw_score, 1.0), 3)
    
    def get_confidence_level(self, score: float) -> str:
        """
        Return color-coded confidence level for frontend display.
        """
        if score >= 0.90:
            return "green"    # High confidence
        elif score >= 0.70:
            return "yellow"   # Medium confidence — user should verify
        else:
            return "red"      # Low confidence — likely incorrect
```

### 7.2 Integration into Entity Extractor

Update your `entity_extractor.py` to include confidence breakdown:

```python
# In entity_extractor.py, modify the extract() method output:
entity = {
    "entity_type": "GROSS_WEIGHT",
    "value": "450.00 KG",
    "page": 1,
    "bbox": [120, 240, 410, 290],
    "extraction_confidence": scorer.compute_extraction_confidence(
        ocr_confidence=0.98,
        bbox_match_ratio=0.92,
        entity_type="GROSS_WEIGHT"
    ),
    "classification_confidence": scorer.compute_classification_confidence(
        classifier_confidence=0.97,
        evidence_count=4
    )
}
```

## Acceptance Criteria

- [ ] Every entity has `extraction_confidence` (0.0–1.0)
- [ ] Every entity has `classification_confidence` (0.0–1.0)
- [ ] Confidence levels map to green/yellow/red correctly
- [ ] Numeric entities (weights, counts) score higher than text entities (names)
- [ ] Low OCR confidence → low extraction confidence

## Outputs

- `backend/ai_pipeline/confidence.py`
- Confidence data ready for Aloka's Layer 3 XAI decomposition
