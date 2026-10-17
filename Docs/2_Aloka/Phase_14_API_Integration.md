# Phase 14 — Backend API Integration (Replace Mocks with Real Logic)

> **Priority:** MUST
> **Estimated Time:** 2–3 hours
> **Dependencies:** Phases 04–11 (all reasoning modules must be built)
> **Blocks:** Kaveen Phase 14 (frontend hooks call these real endpoints)

---

## Goal

Replace ALL mock API endpoints (from Phase 02) with real logic that runs the full pipeline: extraction → knowledge graph → discrepancy detection → all XAI layers → response.

## Implementation

```python
# backend/api/routes.py — Updated with real logic
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from reasoning.knowledge_graph import ShipmentKnowledgeGraph
from reasoning.discrepancy_engine import DiscrepancyEngine
from reasoning.reasoning_chains import ReasoningChainGenerator
from reasoning.confidence_decomp import ConfidenceDecomposer
from reasoning.counterfactual import CounterfactualGenerator
from reasoning.audit_trail import AuditLogger
from reasoning.asycuda_export import AsycudaExporter

router = APIRouter(prefix="/api")

# Global audit logger (in production: use DB-backed logger)
audit = AuditLogger()


@router.get("/shipments/{shipment_id}/extraction")
async def get_extraction(shipment_id: str):
    """Get extraction results for all documents in a shipment."""
    # 1. Load extraction results from DB or file cache
    # In demo: load from pre-processed cache
    extractions = load_extractions(shipment_id)  # Your implementation
    
    audit.log(shipment_id, "API", "Served extraction results",
              details={"document_count": len(extractions)})
    
    return {
        "shipment_id": shipment_id,
        "documents": extractions
    }


@router.get("/shipments/{shipment_id}/graph")
async def get_graph(shipment_id: str):
    """Build and return knowledge graph for vis.js rendering."""
    extractions = load_extractions(shipment_id)
    
    # Build knowledge graph
    kg = ShipmentKnowledgeGraph()
    for doc in extractions:
        kg.add_document(doc["document_id"], doc["document_type"])
        for entity in doc["entities"]:
            kg.add_entity(
                doc_id=doc["document_id"],
                entity_type=entity["entity_type"],
                value=entity["value"],
                confidence=entity.get("extraction_confidence", 0.5),
                page=entity.get("page", 1),
                bbox=entity.get("bbox", [])
            )
    
    kg.detect_conflicts()
    
    audit.log(shipment_id, "GRAPH", "Built knowledge graph",
              details={"nodes": len(kg.graph.nodes), "edges": len(kg.graph.edges)})
    
    return kg.to_vis_json()


@router.get("/shipments/{shipment_id}/discrepancies")
async def get_discrepancies(shipment_id: str):
    """Detect discrepancies with all XAI layers attached."""
    extractions = load_extractions(shipment_id)
    
    # 1. Build knowledge graph
    kg = ShipmentKnowledgeGraph()
    for doc in extractions:
        kg.add_document(doc["document_id"], doc["document_type"])
        for entity in doc["entities"]:
            kg.add_entity(doc["document_id"], entity["entity_type"],
                         entity["value"], entity.get("extraction_confidence", 0.5),
                         entity.get("page", 1), entity.get("bbox", []))
    
    # 2. Detect conflicts
    conflicts = kg.detect_conflicts()
    
    # 3. Generate discrepancies with severity
    engine = DiscrepancyEngine()
    discrepancies = engine.process(conflicts, shipment_id)
    
    # 4. Attach all XAI layers
    chain_gen = ReasoningChainGenerator()
    conf_decomp = ConfidenceDecomposer()
    cf_gen = CounterfactualGenerator()
    
    for disc in discrepancies:
        # Layer 2: Reasoning Chain
        disc["reasoning_chain"] = chain_gen.generate(disc)
        audit.log(shipment_id, "XAI_LAYER_2", 
                  f"Generated reasoning chain for {disc['field']}",
                  details={"steps": len(disc["reasoning_chain"]["steps"])})
        
        # Layer 3: Confidence Decomposition
        disc["confidence"] = conf_decomp.compute(disc)
        audit.log(shipment_id, "XAI_LAYER_3",
                  f"Decomposed confidence for {disc['field']}",
                  confidence=disc["confidence"]["overall"])
        
        # Layer 4: Counterfactual
        disc["counterfactual"] = cf_gen.generate(disc)
        audit.log(shipment_id, "XAI_LAYER_4",
                  f"Generated {len(disc['counterfactual']['options'])} counterfactuals for {disc['field']}")
    
    audit.log(shipment_id, "RECONCILER", 
              f"Completed discrepancy analysis: {len(discrepancies)} found",
              outcome=f"{len(discrepancies)} discrepancies")
    
    return {
        "shipment_id": shipment_id,
        "total_discrepancies": len(discrepancies),
        "discrepancies": discrepancies
    }


@router.get("/shipments/{shipment_id}/audit-trail")
async def get_audit_trail(shipment_id: str):
    """Get the full decision audit trail for a shipment."""
    trail = audit.get_trail(shipment_id)
    return {
        "shipment_id": shipment_id,
        "total_entries": len(trail),
        "entries": trail
    }


@router.get("/shipments/{shipment_id}/asycuda-export")
async def export_asycuda(shipment_id: str):
    """Generate and download ASYCUDA CUSDEC XML file."""
    extractions = load_extractions(shipment_id)
    
    exporter = AsycudaExporter()
    shipment_data = exporter.build_shipment_data(extractions, [])
    xml_content = exporter.generate_xml(shipment_data)
    
    audit.log(shipment_id, "EXPORT", "Generated ASYCUDA CUSDEC file",
              outcome="XML exported")
    
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="CUSDEC_{shipment_id[:8]}.xml"'
        }
    )


@router.get("/shipments/{shipment_id}/status")
async def get_status(shipment_id: str):
    """Get processing status for a shipment."""
    # In demo: always return completed
    extractions = load_extractions(shipment_id)
    return {
        "shipment_id": shipment_id,
        "status": "completed",
        "progress": 100,
        "documents": [
            {
                "document_id": doc["document_id"],
                "filename": doc.get("filename", f"document_{i+1}.pdf"),
                "document_type": doc["document_type"],
                "classification_confidence": doc.get("classification_confidence", 0.95)
            }
            for i, doc in enumerate(extractions)
        ],
        "processing_time_ms": 3200
    }
```

## Acceptance Criteria

- [ ] All 7 endpoints return real data (not mock)
- [ ] `/extraction` returns Nadija's pipeline output
- [ ] `/graph` builds knowledge graph and returns vis.js-compatible JSON
- [ ] `/discrepancies` returns discrepancies with ALL 4 XAI layers attached (reasoning, confidence, counterfactual)
- [ ] `/audit-trail` returns all logged decisions
- [ ] `/asycuda-export` returns downloadable XML
- [ ] `/status` returns shipment processing status
- [ ] Audit logging called at every step
- [ ] Response formats match Kaveen's TypeScript interfaces

## Outputs

- Updated `backend/api/routes.py` — all endpoints wired to real logic
