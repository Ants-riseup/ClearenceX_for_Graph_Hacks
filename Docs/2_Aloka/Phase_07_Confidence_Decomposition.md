# Phase 07 — Layer 3: Confidence Decomposition

> **Priority:** MUST
> **Estimated Time:** 1–2 hours
> **Dependencies:** Phases 04 (knowledge graph), 05 (discrepancy engine)
> **Blocks:** Kaveen Phase 11 (ConfidenceBadge) needs this data format

---

## Goal

Combine Nadija's extraction/classification confidence with your matching confidence into a 3-part decomposed score. This is what makes Layer 3 XAI unique — not one number, but three actionable components.

## Why

The master plan (Section 5, Layer 3) says: *"Goes beyond a single confidence number—decomposes uncertainty into actionable components. User knows whether to re-scan the document (low extraction) or check the classification (low classification) or investigate the mismatch (low matching)."*

This is a **novel combination** per the XAI techniques summary (master plan line 525).

## Implementation

```python
# backend/reasoning/confidence_decomp.py

class ConfidenceDecomposer:
    """
    Layer 3 XAI: Decomposes overall confidence into three actionable components.
    
    - extraction: How well did OCR read the text? (from Nadija's pipeline)
    - classification: How certain is the document type? (from Nadija's classifier)
    - matching: How well do values match across documents? (YOUR contribution)
    - overall: Weakest link = min(extraction, classification, matching)
    """
    
    def compute(self, discrepancy: dict) -> dict:
        sources = discrepancy["sources"]
        
        # 1. Extraction confidence (from Nadija's AI pipeline)
        extraction_scores = [s.get("confidence", 0.5) for s in sources]
        extraction = round(sum(extraction_scores) / len(extraction_scores), 3)
        
        # 2. Classification confidence (from Nadija's classifier)
        # Use a default if not provided by Nadija's output yet
        classification = round(
            sources[0].get("classification_confidence", 0.90), 3
        ) if sources else 0.5
        
        # 3. Matching confidence (YOUR contribution)
        # How well do the values match across documents?
        matching = self._compute_matching(discrepancy)
        
        # Overall = weakest link (minimum of all three)
        overall = round(min(extraction, classification, matching), 3)
        
        # Human-readable explanation
        explanation = self._generate_explanation(extraction, classification, matching)
        
        return {
            "extraction": extraction,
            "classification": classification,
            "matching": matching,
            "overall": overall,
            "explanation": explanation,
            "level": self._level(overall)
        }
    
    def _compute_matching(self, discrepancy: dict) -> float:
        """Calculate how well values match across different documents."""
        sources = discrepancy["sources"]
        if len(sources) < 2:
            return 0.95  # Single source = high match by default
        
        field = discrepancy["field"]
        values = [s.get("value", "") for s in sources]
        
        # Numeric fields: matching = 1 - (scaled variance)
        try:
            nums = [float(str(v).split()[0].replace(",", "")) for v in values]
            max_val = max(nums) if nums else 1
            variance = max(abs(a - b) for a in nums for b in nums) / max_val if max_val > 0 else 0
            return round(max(0, 1 - variance * 10), 3)  # Scale: 1% variance → 0.9 matching
        except (ValueError, IndexError):
            pass
        
        # Text fields: matching = fuzzy similarity (lowest pairwise score)
        from difflib import SequenceMatcher
        pairs = [(values[i], values[j]) for i in range(len(values)) for j in range(i+1, len(values))]
        if pairs:
            sims = [SequenceMatcher(None, a.lower(), b.lower()).ratio() for a, b in pairs]
            return round(min(sims), 3)
        
        return 0.5
    
    def _generate_explanation(self, ext: float, cls: float, match: float) -> str:
        """Generate human-readable explanation of the decomposed confidence."""
        parts = []
        parts.append(f"OCR read this {'clearly' if ext >= 0.9 else 'with some difficulty'} ({ext:.0%})")
        parts.append(f"document type is {'certain' if cls >= 0.9 else 'somewhat uncertain'} ({cls:.0%})")
        
        if match >= 0.9:
            parts.append(f"values match well across documents ({match:.0%})")
        elif match >= 0.7:
            parts.append(f"values partially conflict across documents ({match:.0%})")
        else:
            parts.append(f"significant value conflict across documents ({match:.0%})")
        
        return ". ".join(parts) + "."
    
    def _level(self, score: float) -> str:
        """Map score to traffic-light level for Kaveen's ConfidenceBadge component."""
        if score >= 0.9: return "green"
        if score >= 0.7: return "yellow"
        return "red"
```

## Output Format

This is what Kaveen's `ConfidenceBadge` and `DiscrepancyList` components expect:

```json
{
  "extraction": 0.94,
  "classification": 0.97,
  "matching": 0.72,
  "overall": 0.72,
  "explanation": "OCR read this clearly (94%). document type is certain (97%). values partially conflict across documents (72%).",
  "level": "yellow"
}
```

## Acceptance Criteria

- [ ] Returns extraction, classification, matching, overall scores
- [ ] Overall = minimum of all three (weakest link)
- [ ] Matching confidence reflects actual value similarity
- [ ] Numeric matching: 1% variance → 0.9, 5% variance → 0.5
- [ ] Text matching: uses SequenceMatcher fuzzy ratio
- [ ] Human-readable explanation generated with specific percentages
- [ ] Level maps to green/yellow/red correctly
- [ ] Output matches Kaveen's `DecomposedConfidence` TypeScript interface

## Outputs

- `backend/reasoning/confidence_decomp.py` — ConfidenceDecomposer class
