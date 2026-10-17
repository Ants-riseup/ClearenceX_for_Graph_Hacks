# Phase 08 — Layer 4: Counterfactual Generator

> **Priority:** MUST
> **Estimated Time:** 2–3 hours
> **Dependencies:** Phase 05 (discrepancy engine — needs discrepancy records)
> **Blocks:** Kaveen Phase 10 (DiscrepancyList shows counterfactual cards)

---

## Goal

For each discrepancy, generate "what would need to change" suggestions. These are **minimal counterfactual changes** that would resolve the conflict, plus a domain-specific recommendation.

## Why

The master plan (Section 5, Layer 4) says: *"This is a **2026-trend XAI technique**. Tells the user not just 'what's wrong' but 'what would make it right'—directly actionable. Judges will recognize this as advanced XAI."*

This is marked **"Novel for this domain"** in the XAI techniques summary (master plan line 526).

## Implementation

```python
# backend/reasoning/counterfactual.py

class CounterfactualGenerator:
    """
    Layer 4 XAI: Generates minimal counterfactual changes that would resolve each discrepancy.
    
    For each conflict, answers: "What would need to change for this to pass?"
    Includes domain-specific recommendations for Sri Lankan apparel customs context.
    """
    
    # Domain-specific recommendations based on customs/shipping expertise
    DOMAIN_RECOMMENDATIONS = {
        "GROSS_WEIGHT": "Verify actual weight at factory scale. The Packing List is typically the most accurate source for BOI apparel shipments.",
        "NET_WEIGHT": "Net weight should be calculated as gross weight minus tare weight. Check for rounding differences.",
        "PACKAGE_COUNT": "Verify physical count at warehouse. Package unit terminology (cartons vs pieces) may differ but refer to the same items.",
        "CONSIGNEE_NAME": "Use the exact name as it appears in the Letter of Credit. Minor variations (Ltd. vs Limited) may cause LC rejection.",
        "SHIPPER_NAME": "Shipper name must match exactly across Invoice, Packing List, and B/L. Check for abbreviations.",
        "INCOTERM": "Incoterm must be consistent across all documents. Invoice Incoterm is the contractual reference.",
        "TOTAL_AMOUNT": "Invoice amount must match LC value exactly. Any discrepancy will cause bank rejection.",
        "INVOICE_NUMBER": "Invoice number must be identical across all referencing documents. Check for typos or prefix differences.",
        "WEIGHT_CONSISTENCY": "Internal weight consistency: net weight + tare weight must equal gross weight within each document.",
    }
    
    def generate(self, discrepancy: dict) -> dict:
        """Generate counterfactual options and domain recommendation for a discrepancy."""
        field = discrepancy["field"]
        sources = discrepancy["sources"]
        conflict_type = discrepancy.get("conflict_type", "unknown")
        
        options = []
        
        if conflict_type == "numeric_variance":
            options = self._numeric_counterfactual(field, sources)
        elif conflict_type == "text_mismatch":
            options = self._text_counterfactual(field, sources)
        elif conflict_type == "internal_inconsistency":
            options = self._internal_counterfactual(discrepancy)
        else:
            options = self._generic_counterfactual(field, sources)
        
        recommendation = self.DOMAIN_RECOMMENDATIONS.get(field, 
            "Review the source documents and select the correct value.")
        
        return {"options": options, "recommendation": recommendation}
    
    def _numeric_counterfactual(self, field: str, sources: list) -> list:
        """Generate counterfactuals for numeric value conflicts."""
        options = []
        values = {}
        for src in sources:
            doc = src["document_type"].replace("_", " ").title()
            val = src["value"]
            values[doc] = val
        
        for doc, val in values.items():
            for other_doc, other_val in values.items():
                if doc != other_doc and val != other_val:
                    field_label = field.replace('_', ' ').lower()
                    options.append(
                        f"If {doc} {field_label} were {other_val} "
                        f"(instead of {val}), this discrepancy would resolve."
                    )
        
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for opt in options:
            if opt not in seen:
                seen.add(opt)
                unique.append(opt)
        
        return unique[:4]  # Max 4 options to avoid overwhelming the user
    
    def _text_counterfactual(self, field: str, sources: list) -> list:
        """Generate counterfactuals for text mismatch conflicts."""
        if len(sources) < 2:
            return ["Only one source found — cannot generate comparison."]
        
        val_a = sources[0]["value"]
        val_b = sources[1]["value"]
        doc_a = sources[0]["document_type"].replace("_", " ").title()
        doc_b = sources[1]["document_type"].replace("_", " ").title()
        field_label = field.replace('_', ' ').lower()
        
        options = [
            f"If {doc_b} {field_label} were '{val_a}', names would match exactly.",
            f"If {doc_a} {field_label} were '{val_b}', names would match exactly."
        ]
        
        # Add similarity hint
        from difflib import SequenceMatcher
        sim = SequenceMatcher(None, val_a.lower(), val_b.lower()).ratio()
        if sim >= 0.85:
            options.append(
                f"These values are {sim:.0%} similar — likely a minor typographical difference."
            )
        
        return options
    
    def _internal_counterfactual(self, discrepancy: dict) -> list:
        """Generate counterfactuals for internal document inconsistencies."""
        detail = discrepancy.get("detail", "weight values are inconsistent")
        return [
            "Correct the internal weight values so that net + tare = gross.",
            f"Specific issue: {detail}"
        ]
    
    def _generic_counterfactual(self, field: str, sources: list) -> list:
        """Fallback counterfactual for unrecognized conflict types."""
        options = []
        for src in sources:
            doc = src["document_type"].replace("_", " ").title()
            options.append(f"Verify {field.replace('_', ' ').lower()} value in {doc}: '{src['value']}'")
        return options[:4]
```

## Output Format

This is what Kaveen's `DiscrepancyList` component expects:

```json
{
  "options": [
    "If Packing List gross weight were 448.50 kg (instead of 450.00 kg), this discrepancy would resolve.",
    "If Air Waybill gross weight were 450.00 kg (instead of 448.50 kg), this discrepancy would resolve."
  ],
  "recommendation": "Verify actual weight at factory scale. The Packing List is typically the most accurate source for BOI apparel shipments."
}
```

## Acceptance Criteria

- [ ] Every discrepancy gets at least 1 counterfactual option
- [ ] Numeric conflicts: shows what each document's value would need to become
- [ ] Text conflicts: shows exact string that would resolve the mismatch
- [ ] Internal conflicts: explains net + tare = gross rule
- [ ] Options reference specific document names and values
- [ ] Domain-specific recommendations included (Sri Lankan apparel customs context)
- [ ] Max 4 options per discrepancy (not overwhelming)
- [ ] Output matches Kaveen's `Counterfactual` TypeScript interface

## Outputs

- `backend/reasoning/counterfactual.py` — CounterfactualGenerator class
