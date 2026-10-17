# Phase 09 — Layer 5: Audit Trail System

> **Priority:** MUST
> **Estimated Time:** 1–2 hours
> **Dependencies:** None (standalone module)
> **Blocks:** Kaveen Phase 13 (Audit Trail export button)

---

## Goal

Build an immutable append-only log that records every AI decision ClearanceX makes — from document classification through to counterfactual generation. This is Layer 5 XAI: *"Show me every decision this system made and why."*

## Why

The master plan (Section 5, Layer 5) says: *"Complete regulatory compliance. Customs auditors can trace every value to its source. This is the XAI feature that makes ClearanceX **audit-ready**, not just a tool."*

Currently customs brokers have **0% traceability**. ClearanceX provides **100%**. This is a new capability that doesn't exist in the manual process.

## Implementation

```python
# backend/reasoning/audit_trail.py
from datetime import datetime, timezone
from typing import Optional, Any
import json

class AuditLogger:
    """
    Layer 5 XAI: Immutable decision audit trail.
    
    Logs every AI decision with timestamp, module, action, reasoning, 
    confidence, and outcome. Exportable as JSON for customs compliance.
    
    Usage: Call audit.log() at every pipeline step:
      - Document classification
      - Entity extraction (each entity)
      - Knowledge graph construction
      - Conflict detection (each conflict)
      - Reasoning chain generation
      - Counterfactual generation
      - Human overrides/corrections
    """
    
    def __init__(self):
        self.entries: list[dict] = []
    
    def log(
        self,
        shipment_id: str,
        module: str,
        action: str,
        reasoning: Optional[str] = None,
        confidence: Optional[float] = None,
        outcome: Optional[str] = None,
        details: Optional[dict] = None
    ) -> dict:
        """
        Append a decision to the audit trail.
        
        Args:
            shipment_id: Which shipment this decision relates to
            module: Which system component made the decision
                    (e.g., "CLASSIFIER", "NER", "RECONCILER", "COUNTERFACTUAL")
            action: What the system did
                    (e.g., "Extracted GROSS_WEIGHT", "Detected conflict")
            reasoning: Why the system did it (optional)
            confidence: Confidence score 0.0–1.0 (optional)
            outcome: Result of the action
                     (e.g., "Accepted", "Flagged", "PASS", "FAIL")
            details: Additional structured data (optional)
        
        Returns:
            The created audit entry dict
        """
        entry = {
            "shipment_id": shipment_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "module": module,
            "action": action,
            "reasoning": reasoning,
            "confidence": confidence,
            "outcome": outcome,
            "details": details
        }
        self.entries.append(entry)
        return entry
    
    def get_trail(self, shipment_id: Optional[str] = None) -> list[dict]:
        """Get audit trail entries, optionally filtered by shipment."""
        if shipment_id:
            return [e for e in self.entries if e["shipment_id"] == shipment_id]
        return self.entries
    
    def export_json(self, shipment_id: str) -> str:
        """Export audit trail as formatted JSON for download."""
        trail = self.get_trail(shipment_id)
        export_data = {
            "shipment_id": shipment_id,
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_entries": len(trail),
            "entries": trail
        }
        return json.dumps(export_data, indent=2, default=str)
    
    def get_summary(self, shipment_id: str) -> dict:
        """Get summary statistics for presentation."""
        trail = self.get_trail(shipment_id)
        modules = set(e["module"] for e in trail)
        return {
            "total_decisions": len(trail),
            "modules_involved": list(modules),
            "flags_raised": len([e for e in trail if e.get("outcome") in ("FLAG", "FAIL", "Flagged")]),
            "passes": len([e for e in trail if e.get("outcome") in ("PASS", "Accepted")]),
        }
```

## Where to Call `audit.log()`

You must integrate audit logging at every pipeline step. Here's the checklist:

| Pipeline Step | Module | Action Example | When |
|---|---|---|---|
| Document classified | `CLASSIFIER` | `"Classified as commercial_invoice"` | After Nadija's classifier runs |
| Entity extracted | `NER` | `"Extracted GROSS_WEIGHT=450.00kg from PL pg.2"` | After Nadija's extractor runs |
| Entity normalized | `NORMALIZER` | `"Normalized '450 KGS' → 450.0 kg"` | After normalization |
| Graph node added | `GRAPH` | `"Added entity node GROSS_WEIGHT"` | During graph construction |
| Conflict detected | `RECONCILER` | `"Compared PL.GROSS_WEIGHT vs AWB.GROSS_WEIGHT"` | During conflict detection |
| Reasoning chain generated | `XAI_LAYER_2` | `"Generated 5-step reasoning chain"` | After reasoning chain |
| Confidence decomposed | `XAI_LAYER_3` | `"Decomposed confidence: ext=94%, cls=97%, match=72%"` | After confidence decomp |
| Counterfactual generated | `XAI_LAYER_4` | `"Generated 2 counterfactual options"` | After counterfactual gen |
| Human correction | `USER` | `"User corrected GROSS_WEIGHT from 450.0 to 448.5"` | When user overrides |

## Output Format

This is what Kaveen's `ExportButtons` and audit trail viewer expect:

```json
{
  "shipment_id": "abc-123",
  "export_timestamp": "2026-09-15T12:00:00+00:00",
  "total_entries": 24,
  "entries": [
    {
      "shipment_id": "abc-123",
      "timestamp": "2026-09-15T11:58:01+00:00",
      "module": "CLASSIFIER",
      "action": "Classified document doc_001 as commercial_invoice",
      "reasoning": "Keyword match: 'COMMERCIAL INVOICE' found in header region",
      "confidence": 0.97,
      "outcome": "Accepted",
      "details": {"document_id": "doc_001", "filename": "invoice.pdf"}
    },
    {
      "shipment_id": "abc-123",
      "timestamp": "2026-09-15T11:58:02+00:00",
      "module": "NER",
      "action": "Extracted GROSS_WEIGHT=450.00kg",
      "reasoning": "Source: PL pg.2 bbox(120,240,410,290)",
      "confidence": 0.94,
      "outcome": "Accepted",
      "details": {"entity_type": "GROSS_WEIGHT", "page": 2, "bbox": [120,240,410,290]}
    }
  ]
}
```

## Acceptance Criteria

- [ ] Append-only log — entries are never deleted or modified
- [ ] Every entry has: timestamp, module, action, reasoning, confidence, outcome
- [ ] `get_trail(shipment_id)` filters correctly
- [ ] `export_json()` produces downloadable JSON
- [ ] Audit logging called at every pipeline step (see checklist above)
- [ ] Output matches Kaveen's `AuditEntry` TypeScript interface

## Outputs

- `backend/reasoning/audit_trail.py` — AuditLogger class
