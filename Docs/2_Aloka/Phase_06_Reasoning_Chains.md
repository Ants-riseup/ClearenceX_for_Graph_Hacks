# Phase 06 — Layer 2: Reasoning Chain Generator

> **Priority:** MUST | **Est. Time:** 2–3 hours | **Depends on:** Phase 05

---

## Goal

Generate step-by-step reasoning chains explaining WHY each discrepancy was flagged. Each chain must reference specific values, document names, page numbers, and rules.

## Implementation

```python
# backend/reasoning/reasoning_chains.py

class ReasoningChainGenerator:
    """Generates human-readable reasoning chains for discrepancies."""
    
    def generate(self, discrepancy: dict) -> dict:
        """Generate reasoning chain for a discrepancy."""
        field = discrepancy["field"]
        sources = discrepancy["sources"]
        conflict_type = discrepancy.get("conflict_type", "numeric_variance")
        
        if conflict_type == "numeric_variance":
            return self._numeric_reasoning(field, sources)
        elif conflict_type == "text_mismatch":
            return self._text_reasoning(field, sources)
        elif conflict_type == "internal_inconsistency":
            return self._internal_reasoning(discrepancy)
        else:
            return self._generic_reasoning(field, sources)
    
    def _numeric_reasoning(self, field: str, sources: list) -> dict:
        steps = []
        field_label = field.replace("_", " ").title()
        
        # Step 1-N: List extracted values
        for i, src in enumerate(sources, 1):
            doc_type = src["document_type"].replace("_", " ").title()
            steps.append(
                f"Extracted {field_label} from {doc_type} "
                f"(pg.{src.get('page', 1)}): {src['value']} "
                f"(confidence: {src.get('confidence', 0.5):.0%})"
            )
        
        # Comparison steps
        values = [float(src.get("value", "0").split()[0].replace(",", "")) 
                  for src in sources if src.get("value")]
        
        if len(values) >= 2:
            for i in range(len(values)):
                for j in range(i+1, len(values)):
                    variance = abs(values[i] - values[j]) / max(values[i], values[j], 1) * 100
                    doc_a = sources[i]["document_type"].replace("_", " ").title()
                    doc_b = sources[j]["document_type"].replace("_", " ").title()
                    
                    result = "MATCH ✓" if variance <= 0.5 else f"VARIANCE DETECTED ⚠️"
                    steps.append(
                        f"{doc_a} vs {doc_b}: "
                        f"|{values[i]:.2f} - {values[j]:.2f}| / {max(values[i], values[j]):.2f} "
                        f"= {variance:.2f}% → {result}"
                    )
        
        # Rule explanation
        steps.append(f"Rule: {field_label} variance > 0.5% triggers flag for customs review")
        
        # Conclusion
        max_var = max([abs(values[i] - values[j]) / max(values[i], values[j], 1) * 100 
                       for i in range(len(values)) for j in range(i+1, len(values))], default=0)
        
        if max_var > 0.5:
            conclusion = f"Cross-document {field_label.lower()} variance of {max_var:.2f}% detected. Manual verification required."
        else:
            conclusion = f"{field_label} values are within acceptable tolerance across all documents."
        
        return {"steps": steps, "conclusion": conclusion}
    
    def _text_reasoning(self, field: str, sources: list) -> dict:
        steps = []
        field_label = field.replace("_", " ").title()
        
        for i, src in enumerate(sources, 1):
            doc_type = src["document_type"].replace("_", " ").title()
            steps.append(f"Extracted {field_label} from {doc_type}: '{src['value']}' (confidence: {src.get('confidence', 0.5):.0%})")
        
        if len(sources) >= 2:
            from difflib import SequenceMatcher
            val_a = str(sources[0]["value"])
            val_b = str(sources[1]["value"])
            similarity = SequenceMatcher(None, val_a.lower(), val_b.lower()).ratio()
            
            steps.append(f"Fuzzy match score: {similarity:.0%} (threshold: 90%)")
            steps.append(f"Difference: '{val_a}' vs '{val_b}'")
            
            if similarity >= 0.9:
                conclusion = f"Minor typographical variation in {field_label.lower()}. Likely same entity."
            else:
                conclusion = f"Significant difference in {field_label.lower()} across documents. Manual verification required."
        else:
            conclusion = f"Insufficient data to compare {field_label.lower()}."
        
        return {"steps": steps, "conclusion": conclusion}
    
    def _internal_reasoning(self, discrepancy: dict) -> dict:
        detail = discrepancy.get("detail", "")
        steps = [
            f"Internal consistency check performed on document",
            f"Validation: {detail}",
            f"Rule: net weight + tare weight must equal gross weight",
            f"RESULT: INTERNAL INCONSISTENCY DETECTED ⚠️"
        ]
        return {"steps": steps, "conclusion": f"Internal weight inconsistency: {detail}"}
    
    def _generic_reasoning(self, field: str, sources: list) -> dict:
        steps = [f"Compared {field} across {len(sources)} documents"]
        for src in sources:
            steps.append(f"  {src['document_type']}: {src['value']}")
        return {"steps": steps, "conclusion": f"Discrepancy detected in {field}"}
```

## Acceptance Criteria
- [ ] Every discrepancy gets a reasoning chain with 3+ steps
- [ ] Steps reference specific document names, pages, values
- [ ] Numeric comparisons show actual variance percentage
- [ ] Rules are explained (not just "flagged")
- [ ] Conclusion summarizes the finding clearly
