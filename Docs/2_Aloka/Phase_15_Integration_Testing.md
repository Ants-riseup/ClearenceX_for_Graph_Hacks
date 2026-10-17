# Phase 15 — Integration Testing

> **Priority:** MUST
> **Estimated Time:** 2–3 hours
> **Dependencies:** Phases 01–14 (everything must be built)
> **Blocks:** Demo readiness

---

## Goal

Run end-to-end tests on 5 synthetic dossiers through the complete pipeline. Verify extraction accuracy, discrepancy detection, reasoning chain correctness, counterfactual validity, audit trail completeness, and graph rendering.

## Why

The master plan (Section 15, Phase 8) requires: *"10 test dossiers with 50 known discrepancies"* and *"XAI quality check (reasoning chains accurate? counterfactuals valid?)"*. This is how we prove the system works before the demo.

## Test Plan

### Test 1: Full Pipeline Smoke Test

```python
# tests/test_full_pipeline.py
import json
from reasoning.knowledge_graph import ShipmentKnowledgeGraph
from reasoning.discrepancy_engine import DiscrepancyEngine
from reasoning.reasoning_chains import ReasoningChainGenerator
from reasoning.confidence_decomp import ConfidenceDecomposer
from reasoning.counterfactual import CounterfactualGenerator
from reasoning.audit_trail import AuditLogger
from reasoning.asycuda_export import AsycudaExporter

def test_full_pipeline():
    """Run a synthetic dossier through the complete pipeline."""
    
    # 1. Load synthetic extraction data
    with open("data/sample_documents/test_dossier_01.json") as f:
        extractions = json.load(f)
    
    shipment_id = "test-001"
    audit = AuditLogger()
    
    # 2. Build knowledge graph
    kg = ShipmentKnowledgeGraph()
    for doc in extractions:
        kg.add_document(doc["document_id"], doc["document_type"])
        for entity in doc["entities"]:
            kg.add_entity(doc["document_id"], entity["entity_type"],
                         entity["value"], entity.get("extraction_confidence", 0.9),
                         entity.get("page", 1), entity.get("bbox", [0,0,100,20]))
    
    # 3. Detect conflicts
    conflicts = kg.detect_conflicts()
    print(f"✓ Found {len(conflicts)} conflicts")
    
    # 4. Generate discrepancies
    engine = DiscrepancyEngine()
    discrepancies = engine.process(conflicts, shipment_id)
    print(f"✓ Generated {len(discrepancies)} discrepancies")
    
    # 5. Attach XAI layers
    chain_gen = ReasoningChainGenerator()
    conf_decomp = ConfidenceDecomposer()
    cf_gen = CounterfactualGenerator()
    
    for disc in discrepancies:
        disc["reasoning_chain"] = chain_gen.generate(disc)
        disc["confidence"] = conf_decomp.compute(disc)
        disc["counterfactual"] = cf_gen.generate(disc)
    
    # 6. Validate XAI quality
    for disc in discrepancies:
        # Reasoning chains should have 3+ steps
        assert len(disc["reasoning_chain"]["steps"]) >= 3, f"Too few steps for {disc['field']}"
        assert disc["reasoning_chain"]["conclusion"], f"Missing conclusion for {disc['field']}"
        
        # Confidence should have all 3 components
        assert "extraction" in disc["confidence"]
        assert "classification" in disc["confidence"]
        assert "matching" in disc["confidence"]
        assert disc["confidence"]["overall"] == min(
            disc["confidence"]["extraction"],
            disc["confidence"]["classification"],
            disc["confidence"]["matching"]
        ), "Overall should be min of components"
        
        # Counterfactuals should have at least 1 option
        assert len(disc["counterfactual"]["options"]) >= 1, f"No counterfactual for {disc['field']}"
        assert disc["counterfactual"]["recommendation"], f"Missing recommendation for {disc['field']}"
    
    print(f"✓ All XAI layers validated")
    
    # 7. Test graph serialization
    graph_data = kg.to_vis_json()
    assert len(graph_data["nodes"]) > 0
    assert len(graph_data["edges"]) > 0
    for node in graph_data["nodes"]:
        assert "id" in node and "label" in node and "type" in node
    print(f"✓ Graph: {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges")
    
    # 8. Test ASYCUDA export
    exporter = AsycudaExporter()
    shipment_data = exporter.build_shipment_data(extractions, discrepancies)
    xml = exporter.generate_xml(shipment_data)
    assert "<?xml" in xml
    assert "CUSDEC" in xml
    assert "ClearanceX" in xml
    print(f"✓ ASYCUDA XML generated ({len(xml)} chars)")
    
    # 9. Test audit trail
    trail = audit.get_trail(shipment_id)
    print(f"✓ Audit trail: {len(trail)} entries")
    
    print("\n🎉 FULL PIPELINE TEST PASSED")

if __name__ == "__main__":
    test_full_pipeline()
```

### Test 2: Discrepancy Detection Precision/Recall

```python
def test_discrepancy_detection():
    """Test against dossiers with KNOWN discrepancies (ground truth)."""
    
    # Each test dossier has injected discrepancies with ground truth
    test_cases = [
        {"file": "test_dossier_weight_mismatch.json", "expected_fields": ["GROSS_WEIGHT"]},
        {"file": "test_dossier_name_typo.json", "expected_fields": ["CONSIGNEE_NAME"]},
        {"file": "test_dossier_incoterm_conflict.json", "expected_fields": ["INCOTERM"]},
        {"file": "test_dossier_multiple.json", "expected_fields": ["GROSS_WEIGHT", "PACKAGE_COUNT"]},
        {"file": "test_dossier_clean.json", "expected_fields": []},  # No discrepancies
    ]
    
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    
    for case in test_cases:
        # Run pipeline...
        detected_fields = [d["field"] for d in discrepancies]
        
        for expected in case["expected_fields"]:
            if expected in detected_fields:
                true_positives += 1
            else:
                false_negatives += 1
        
        for detected in detected_fields:
            if detected not in case["expected_fields"]:
                false_positives += 1
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    
    print(f"Precision: {precision:.0%}")
    print(f"Recall: {recall:.0%}")
    print(f"Target: Precision ≥ 90%, Recall ≥ 95%")
```

### Test 3: Counterfactual Validity

```python
def test_counterfactuals_resolve():
    """Verify that applying counterfactual changes actually resolves conflicts."""
    # For each discrepancy with numeric counterfactuals:
    # 1. Parse the suggested value change
    # 2. Apply it to the extraction data
    # 3. Re-run conflict detection
    # 4. Verify the conflict no longer exists
    pass  # Implement based on your data format
```

## Checklist

- [ ] 5 synthetic dossiers tested through full pipeline
- [ ] Extraction → Graph → Discrepancy → XAI layers → Export all pass
- [ ] Reasoning chains have 3+ steps referencing correct documents and values
- [ ] Confidence decomposition: overall = min(extraction, classification, matching)
- [ ] Counterfactuals: at least 1 option per discrepancy with domain recommendation
- [ ] Audit trail logs all pipeline steps
- [ ] Graph serialization produces valid vis.js JSON
- [ ] ASYCUDA XML is well-formed
- [ ] Precision ≥ 90%, Recall ≥ 95% on discrepancy detection
- [ ] **Document results for presentation**

## Outputs

- `tests/test_full_pipeline.py` — integration test script
- Test results documented for presentation slides
