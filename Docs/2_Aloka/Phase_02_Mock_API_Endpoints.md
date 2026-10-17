# Phase 02 — Mock API Endpoints

> **Priority:** MUST
> **Estimated Time:** 2–3 hours
> **Dependencies:** Phase 01 (database ready)
> **Blocks:** Kaveen's entire frontend (he builds against these mocks)

---

## Goal

Create ALL backend API endpoints with mock/hardcoded data so Kaveen can build the entire frontend without waiting for real AI or reasoning logic.

## Why

This is the most critical enabling task. If Kaveen doesn't have working API endpoints, he's blocked. Mock endpoints let him build the full UI immediately.

## Endpoints to Create

### 2.1 POST `/api/shipments/upload`

```python
# backend/api/routes.py
from fastapi import APIRouter, UploadFile, File
from typing import List
import uuid
import os

router = APIRouter(prefix="/api")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/shipments/upload")
async def upload_shipment(files: List[UploadFile] = File(...)):
    shipment_id = str(uuid.uuid4())
    documents = []
    
    for file in files:
        doc_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{file.filename}")
        
        # Save file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        documents.append({
            "document_id": doc_id,
            "filename": file.filename,
            "status": "uploaded"
        })
    
    # TODO: Trigger AI pipeline processing (Phase 14)
    
    return {
        "shipment_id": shipment_id,
        "status": "processing",
        "documents": documents
    }
```

### 2.2 GET `/api/shipments/{id}/status`

```python
@router.get("/shipments/{shipment_id}/status")
async def get_shipment_status(shipment_id: str):
    # MOCK: Return fake status
    return {
        "shipment_id": shipment_id,
        "status": "completed",
        "progress": 100,
        "documents": [
            {"document_id": "doc_001", "filename": "commercial_invoice.pdf", "document_type": "commercial_invoice", "classification_confidence": 0.97},
            {"document_id": "doc_002", "filename": "packing_list.pdf", "document_type": "packing_list", "classification_confidence": 0.96},
            {"document_id": "doc_003", "filename": "awb.pdf", "document_type": "awb", "classification_confidence": 0.95}
        ],
        "processing_time_ms": 8500
    }
```

### 2.3 GET `/api/shipments/{id}/extraction`

```python
@router.get("/shipments/{shipment_id}/extraction")
async def get_extraction(shipment_id: str):
    # MOCK: Return realistic extraction data
    return {
        "shipment_id": shipment_id,
        "documents": [
            {
                "document_id": "doc_001",
                "document_type": "commercial_invoice",
                "classification_confidence": 0.97,
                "entities": [
                    {"entity_type": "INVOICE_NUMBER", "value": "INV-2024-1023", "normalized_value": "INV-2024-1023", "unit": None, "page": 1, "bbox": [45, 120, 280, 145], "extraction_confidence": 0.96, "classification_confidence": 0.97},
                    {"entity_type": "CONSIGNEE_NAME", "value": "ABC Textiles Ltd", "normalized_value": "ABC Textiles Ltd", "unit": None, "page": 1, "bbox": [50, 200, 320, 225], "extraction_confidence": 0.91, "classification_confidence": 0.97},
                    {"entity_type": "GROSS_WEIGHT", "value": "450.00 KG", "normalized_value": 450.0, "unit": "kg", "page": 1, "bbox": [400, 350, 550, 375], "extraction_confidence": 0.94, "classification_confidence": 0.97},
                    {"entity_type": "NET_WEIGHT", "value": "420.00 KG", "normalized_value": 420.0, "unit": "kg", "page": 1, "bbox": [400, 380, 550, 405], "extraction_confidence": 0.93, "classification_confidence": 0.97},
                    {"entity_type": "PACKAGE_COUNT", "value": "25 Cartons", "normalized_value": 25, "unit": "cartons", "page": 1, "bbox": [400, 410, 550, 435], "extraction_confidence": 0.95, "classification_confidence": 0.97},
                    {"entity_type": "INCOTERM", "value": "FOB Colombo", "normalized_value": "FOB", "unit": None, "page": 1, "bbox": [50, 300, 200, 325], "extraction_confidence": 0.92, "classification_confidence": 0.97},
                    {"entity_type": "TOTAL_AMOUNT", "value": "45,230.00 USD", "normalized_value": 45230.0, "unit": None, "page": 1, "bbox": [400, 500, 580, 530], "extraction_confidence": 0.94, "classification_confidence": 0.97}
                ]
            },
            {
                "document_id": "doc_002",
                "document_type": "packing_list",
                "classification_confidence": 0.96,
                "entities": [
                    {"entity_type": "GROSS_WEIGHT", "value": "450.00 KG", "normalized_value": 450.0, "unit": "kg", "page": 1, "bbox": [350, 400, 500, 425], "extraction_confidence": 0.95, "classification_confidence": 0.96},
                    {"entity_type": "NET_WEIGHT", "value": "420.00 KG", "normalized_value": 420.0, "unit": "kg", "page": 1, "bbox": [350, 430, 500, 455], "extraction_confidence": 0.93, "classification_confidence": 0.96},
                    {"entity_type": "TARE_WEIGHT", "value": "25.00 KG", "normalized_value": 25.0, "unit": "kg", "page": 1, "bbox": [350, 460, 500, 485], "extraction_confidence": 0.90, "classification_confidence": 0.96},
                    {"entity_type": "PACKAGE_COUNT", "value": "25 Cartons", "normalized_value": 25, "unit": "cartons", "page": 1, "bbox": [350, 490, 500, 515], "extraction_confidence": 0.96, "classification_confidence": 0.96}
                ]
            },
            {
                "document_id": "doc_003",
                "document_type": "awb",
                "classification_confidence": 0.95,
                "entities": [
                    {"entity_type": "AWB_NUMBER", "value": "631-12345678", "normalized_value": "631-12345678", "unit": None, "page": 1, "bbox": [200, 50, 400, 80], "extraction_confidence": 0.97, "classification_confidence": 0.95},
                    {"entity_type": "GROSS_WEIGHT", "value": "448.50 KG", "normalized_value": 448.5, "unit": "kg", "page": 1, "bbox": [350, 300, 500, 325], "extraction_confidence": 0.93, "classification_confidence": 0.95},
                    {"entity_type": "PACKAGE_COUNT", "value": "25 Pieces", "normalized_value": 25, "unit": "pieces", "page": 1, "bbox": [350, 330, 500, 355], "extraction_confidence": 0.94, "classification_confidence": 0.95},
                    {"entity_type": "CONSIGNEE_NAME", "value": "ABC Textiles Ltd.", "normalized_value": "ABC Textiles Ltd.", "unit": None, "page": 1, "bbox": [50, 200, 350, 225], "extraction_confidence": 0.89, "classification_confidence": 0.95}
                ]
            }
        ]
    }
```

### 2.4 GET `/api/shipments/{id}/graph`

```python
@router.get("/shipments/{shipment_id}/graph")
async def get_knowledge_graph(shipment_id: str):
    # MOCK: Knowledge graph for vis.js
    return {
        "nodes": [
            {"id": "doc_001", "label": "Commercial Invoice", "type": "document", "color": "#4A90D9"},
            {"id": "doc_002", "label": "Packing List", "type": "document", "color": "#50C878"},
            {"id": "doc_003", "label": "AWB", "type": "document", "color": "#FFB347"},
            {"id": "GROSS_WEIGHT", "label": "Gross Weight", "type": "entity", "status": "conflict", "color": "#FF6B6B"},
            {"id": "NET_WEIGHT", "label": "Net Weight", "type": "entity", "status": "match", "color": "#50C878"},
            {"id": "PACKAGE_COUNT", "label": "Package Count", "type": "entity", "status": "match", "color": "#50C878"},
            {"id": "CONSIGNEE_NAME", "label": "Consignee", "type": "entity", "status": "warning", "color": "#FFD700"},
            {"id": "INCOTERM", "label": "Incoterm", "type": "entity", "status": "match", "color": "#50C878"}
        ],
        "edges": [
            {"from": "doc_001", "to": "GROSS_WEIGHT", "label": "450.00 kg", "confidence": 0.94},
            {"from": "doc_002", "to": "GROSS_WEIGHT", "label": "450.00 kg", "confidence": 0.95},
            {"from": "doc_003", "to": "GROSS_WEIGHT", "label": "448.50 kg", "confidence": 0.93},
            {"from": "doc_001", "to": "NET_WEIGHT", "label": "420.00 kg", "confidence": 0.93},
            {"from": "doc_002", "to": "NET_WEIGHT", "label": "420.00 kg", "confidence": 0.93},
            {"from": "doc_001", "to": "PACKAGE_COUNT", "label": "25 cartons", "confidence": 0.95},
            {"from": "doc_002", "to": "PACKAGE_COUNT", "label": "25 cartons", "confidence": 0.96},
            {"from": "doc_003", "to": "PACKAGE_COUNT", "label": "25 pieces", "confidence": 0.94},
            {"from": "doc_001", "to": "CONSIGNEE_NAME", "label": "ABC Textiles Ltd", "confidence": 0.91},
            {"from": "doc_003", "to": "CONSIGNEE_NAME", "label": "ABC Textiles Ltd.", "confidence": 0.89},
            {"from": "doc_001", "to": "INCOTERM", "label": "FOB", "confidence": 0.92}
        ]
    }
```

### 2.5 GET `/api/shipments/{id}/discrepancies`

```python
@router.get("/shipments/{shipment_id}/discrepancies")
async def get_discrepancies(shipment_id: str):
    # MOCK: Full discrepancy with all XAI layers
    return {
        "shipment_id": shipment_id,
        "total_discrepancies": 2,
        "discrepancies": [
            {
                "discrepancy_id": "disc_001",
                "field": "GROSS_WEIGHT",
                "severity": "high",
                "severity_score": 0.87,
                "status": "open",
                "sources": [
                    {"document_id": "doc_001", "document_type": "commercial_invoice", "value": "450.00 kg", "page": 1, "bbox": [400, 350, 550, 375]},
                    {"document_id": "doc_002", "document_type": "packing_list", "value": "450.00 kg", "page": 1, "bbox": [350, 400, 500, 425]},
                    {"document_id": "doc_003", "document_type": "awb", "value": "448.50 kg", "page": 1, "bbox": [350, 300, 500, 325]}
                ],
                "reasoning_chain": {
                    "steps": [
                        "Extracted gross weight from Commercial Invoice (pg.1): 450.00 kg (confidence: 94%)",
                        "Extracted gross weight from Packing List (pg.1): 450.00 kg (confidence: 95%)",
                        "Extracted gross weight from AWB (pg.1): 448.50 kg (confidence: 93%)",
                        "Commercial Invoice vs Packing List: |450.00 - 450.00| / 450.00 = 0.00% → MATCH ✓",
                        "Commercial Invoice vs AWB: |450.00 - 448.50| / 450.00 = 0.33% → Below 0.5% threshold but notable variance",
                        "Packing List internal check: net(420.00) + tare(25.00) = 445.00 ≠ gross(450.00) → INTERNAL INCONSISTENCY ⚠️",
                        "CONCLUSION: AWB weight deviates from Invoice/PL. PL has internal inconsistency (net + tare ≠ gross)."
                    ],
                    "conclusion": "Cross-document weight variance detected between AWB and Invoice/PL. Additionally, Packing List has an internal weight inconsistency."
                },
                "confidence": {
                    "extraction": 0.94,
                    "classification": 0.96,
                    "matching": 0.72,
                    "overall": 0.72
                },
                "counterfactual": {
                    "options": [
                        "If AWB gross weight were 450.00 kg (instead of 448.50 kg), cross-document discrepancy would resolve.",
                        "If Invoice/PL gross weight were 448.50 kg (instead of 450.00 kg), cross-document discrepancy would resolve.",
                        "If PL tare weight were 30.00 kg (instead of 25.00 kg), PL internal consistency would resolve (net 420 + tare 30 = gross 450)."
                    ],
                    "recommendation": "Verify actual weight at factory scale. The Packing List is typically the most accurate source for BOI apparel shipments. The PL internal inconsistency (net + tare ≠ gross) should be corrected first."
                }
            },
            {
                "discrepancy_id": "disc_002",
                "field": "CONSIGNEE_NAME",
                "severity": "low",
                "severity_score": 0.35,
                "status": "open",
                "sources": [
                    {"document_id": "doc_001", "document_type": "commercial_invoice", "value": "ABC Textiles Ltd", "page": 1, "bbox": [50, 200, 320, 225]},
                    {"document_id": "doc_003", "document_type": "awb", "value": "ABC Textiles Ltd.", "page": 1, "bbox": [50, 200, 350, 225]}
                ],
                "reasoning_chain": {
                    "steps": [
                        "Extracted consignee from Invoice (pg.1): 'ABC Textiles Ltd' (confidence: 91%)",
                        "Extracted consignee from AWB (pg.1): 'ABC Textiles Ltd.' (confidence: 89%)",
                        "Fuzzy match score: 97% (above 90% threshold)",
                        "Difference: trailing period '.' in AWB version",
                        "CONCLUSION: Minor typographical variation. Likely same entity."
                    ],
                    "conclusion": "Minor typographical difference in consignee name (trailing period). Not a substantive discrepancy."
                },
                "confidence": {
                    "extraction": 0.90,
                    "classification": 0.96,
                    "matching": 0.97,
                    "overall": 0.90
                },
                "counterfactual": {
                    "options": [
                        "If AWB consignee were 'ABC Textiles Ltd' (without period), names would match exactly."
                    ],
                    "recommendation": "This is likely a non-issue. Both refer to the same entity. Use the Invoice version (without period) for CUSDEC."
                }
            }
        ]
    }
```

### 2.6 GET `/api/shipments/{id}/audit-trail`

```python
@router.get("/shipments/{shipment_id}/audit-trail")
async def get_audit_trail(shipment_id: str):
    return {
        "shipment_id": shipment_id,
        "entries": [
            {"timestamp": "2024-09-14T10:30:01", "module": "classifier", "action": "Classified doc_001 as commercial_invoice", "confidence": 0.97, "outcome": "accepted"},
            {"timestamp": "2024-09-14T10:30:02", "module": "classifier", "action": "Classified doc_002 as packing_list", "confidence": 0.96, "outcome": "accepted"},
            {"timestamp": "2024-09-14T10:30:03", "module": "classifier", "action": "Classified doc_003 as awb", "confidence": 0.95, "outcome": "accepted"},
            {"timestamp": "2024-09-14T10:30:05", "module": "extractor", "action": "Extracted GROSS_WEIGHT=450.00kg from doc_001 pg.1", "confidence": 0.94, "outcome": "accepted"},
            {"timestamp": "2024-09-14T10:30:06", "module": "extractor", "action": "Extracted GROSS_WEIGHT=450.00kg from doc_002 pg.1", "confidence": 0.95, "outcome": "accepted"},
            {"timestamp": "2024-09-14T10:30:07", "module": "extractor", "action": "Extracted GROSS_WEIGHT=448.50kg from doc_003 pg.1", "confidence": 0.93, "outcome": "accepted"},
            {"timestamp": "2024-09-14T10:30:10", "module": "reconciler", "action": "Compared GROSS_WEIGHT across 3 documents", "confidence": 0.72, "outcome": "conflict_detected"},
            {"timestamp": "2024-09-14T10:30:11", "module": "reconciler", "action": "Internal consistency check: PL net+tare=445 ≠ gross=450", "confidence": None, "outcome": "inconsistency_flagged"},
            {"timestamp": "2024-09-14T10:30:12", "module": "counterfactual", "action": "Generated 3 resolution options for GROSS_WEIGHT discrepancy", "confidence": None, "outcome": "generated"}
        ]
    }
```

### 2.7 GET `/api/shipments/{id}/asycuda-export`

```python
from fastapi.responses import Response

@router.get("/shipments/{shipment_id}/asycuda-export")
async def export_asycuda(shipment_id: str):
    # MOCK: Return a simple XML structure
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<CUSDEC>
  <DeclarationHeader>
    <DeclarationType>IM</DeclarationType>
    <DeclarationOffice>LKCMB01</DeclarationOffice>
  </DeclarationHeader>
  <ConsigneeInfo>
    <Name>ABC Textiles Ltd</Name>
    <Address>42 Galle Road, Colombo 03</Address>
  </ConsigneeInfo>
  <TransportInfo>
    <AWBNumber>631-12345678</AWBNumber>
    <GrossWeight unit="KG">450.00</GrossWeight>
    <PackageCount>25</PackageCount>
  </TransportInfo>
  <Items>
    <Item number="1">
      <Description>100% Cotton Woven Fabric</Description>
      <HSCode>5208.32.00</HSCode>
      <Quantity unit="MTR">5000</Quantity>
      <Value currency="USD">12500.00</Value>
    </Item>
  </Items>
</CUSDEC>"""
    
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename=CUSDEC_{shipment_id}.xml"}
    )
```

### 2.8 Register Routes in Main App

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

app = FastAPI(title="ClearanceX API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "clearancex"}
```

## Acceptance Criteria

- [ ] All 7 endpoints return valid JSON
- [ ] Upload endpoint saves files to disk
- [ ] Mock data is realistic and matches the agreed contract schemas
- [ ] CORS allows frontend (localhost:5173) to call the API
- [ ] FastAPI auto-docs (Swagger UI) available at `/docs`
- [ ] Kaveen confirms he can call all endpoints from the frontend

## Outputs

- `backend/api/routes.py` — all endpoints
- `backend/main.py` — FastAPI app
- Kaveen is now UNBLOCKED to build the full frontend
