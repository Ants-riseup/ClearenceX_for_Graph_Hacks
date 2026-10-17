# Phase 05 — Discrepancy Detection Engine

> **Priority:** MUST | **Est. Time:** 3–4 hours | **Depends on:** Phase 04

---

## Goal

Transform knowledge graph conflicts into structured discrepancy records with severity scoring, ready for XAI layer enrichment.

## Implementation

```python
# backend/reasoning/discrepancy_engine.py

class DiscrepancyEngine:
    """Converts knowledge graph conflicts into structured discrepancy records."""
    
    # Financial impact weights per field (used for severity scoring)
    FINANCIAL_IMPACT = {
        "GROSS_WEIGHT": 0.9,      # Weight errors → customs rejection → demurrage
        "NET_WEIGHT": 0.85,
        "PACKAGE_COUNT": 0.7,     # Count errors → inspection holds
        "INCOTERM": 0.95,         # Incoterm conflicts → freight/insurance disputes
        "CONSIGNEE_NAME": 0.4,    # Typos → low financial impact if same entity
        "SHIPPER_NAME": 0.4,
        "TOTAL_AMOUNT": 0.9,      # Amount errors → LC rejection
        "WEIGHT_CONSISTENCY": 0.85  # Internal inconsistency → red flag
    }
    
    SEVERITY_THRESHOLDS = {
        "high": 0.7,
        "medium": 0.4,
        "low": 0.0
    }
    
    def process(self, conflicts: list, shipment_id: str) -> list:
        """Convert graph conflicts into discrepancy records with severity."""
        discrepancies = []
        
        for i, conflict in enumerate(conflicts):
            entity_type = conflict["entity_type"]
            financial_impact = self.FINANCIAL_IMPACT.get(entity_type, 0.5)
            
            # Calculate confidence gap (how far apart are the confidences?)
            confidences = [s.get("confidence", 0.5) for s in conflict["sources"]]
            confidence_gap = max(confidences) - min(confidences) if confidences else 0
            
            # Severity score
            severity_score = round(financial_impact * (1 + confidence_gap), 3)
            severity_score = min(severity_score, 1.0)
            
            # Classify severity
            if severity_score >= self.SEVERITY_THRESHOLDS["high"]:
                severity = "high"
            elif severity_score >= self.SEVERITY_THRESHOLDS["medium"]:
                severity = "medium"
            else:
                severity = "low"
            
            discrepancies.append({
                "discrepancy_id": f"disc_{shipment_id[:8]}_{i+1:03d}",
                "field": entity_type,
                "severity": severity,
                "severity_score": severity_score,
                "status": "open",
                "sources": conflict["sources"],
                "conflict_type": conflict.get("conflict_type", "unknown"),
                # XAI layers will be added in subsequent phases:
                "reasoning_chain": None,    # Phase 06
                "confidence": None,         # Phase 07
                "counterfactual": None      # Phase 08
            })
        
        # Sort by severity score (highest first)
        discrepancies.sort(key=lambda d: d["severity_score"], reverse=True)
        
        return discrepancies
```

## Acceptance Criteria
- [ ] Each conflict becomes a structured discrepancy record
- [ ] Severity scoring considers financial impact
- [ ] Sorted by severity (highest first)
- [ ] Weight/Incoterm conflicts are HIGH severity
- [ ] Consignee typos are LOW severity
