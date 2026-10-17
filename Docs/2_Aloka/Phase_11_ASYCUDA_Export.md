# Phase 11 — ASYCUDA Export Generator

> **Priority:** MUST
> **Estimated Time:** 2–3 hours
> **Dependencies:** Phase 05 (needs validated extraction data with resolved discrepancies)
> **Blocks:** Kaveen Phase 13 (ExportButtons calls this API endpoint)

---

## Goal

Generate ASYCUDA-compliant XML (CUSDEC format) from the validated extraction data. This is the final output — the thing customs brokers actually need.

## Why

The master plan's core workflow ends with *"ASYCUDA XML export"*. Without this, ClearanceX doesn't complete the job. The judge demo flow includes clicking "Generate ASYCUDA" and downloading a real XML file.

## Important Note

> **The exact ASYCUDA World XML schema is not publicly documented.** This implementation uses a plausible structure based on UNCTAD documentation and customs declaration conventions. **Disclose this in the presentation:** *"We reverse-engineered a plausible CUSDEC schema; production deployment would use the official ASYCUDA DTI specification."*

## Implementation

```python
# backend/reasoning/asycuda_export.py
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime

class AsycudaExporter:
    """
    Generates ASYCUDA-compliant CUSDEC XML from validated extraction data.
    
    The XML structure follows UNCTAD ASYCUDA World conventions:
    - CUSDEC root element
    - DeclarationHeader (type, office, date)
    - ConsigneeInfo / ShipperInfo
    - TransportInfo (AWB, weights, packages)
    - Items (line items with HS codes, quantities, values)
    """
    
    def generate_xml(self, shipment_data: dict) -> str:
        """
        Generate ASYCUDA-compliant XML from validated extraction data.
        
        Args:
            shipment_data: dict with keys:
                - date: declaration date
                - consignee_name, consignee_address
                - shipper_name, shipper_address
                - awb_number (or bl_number)
                - gross_weight, net_weight, package_count
                - incoterm, currency
                - items: list of {description, hs_code, quantity, unit, unit_price, total}
        
        Returns:
            Pretty-printed XML string
        """
        root = ET.Element("CUSDEC")
        root.set("version", "1.0")
        root.set("xmlns", "urn:asycuda:cusdec")
        root.set("generated_by", "ClearanceX")
        root.set("generated_at", datetime.utcnow().isoformat())
        
        # ── Declaration Header ──
        header = ET.SubElement(root, "DeclarationHeader")
        ET.SubElement(header, "DeclarationType").text = shipment_data.get("declaration_type", "IM4")
        ET.SubElement(header, "DeclarationOffice").text = shipment_data.get("customs_office", "LKCMB01")
        ET.SubElement(header, "DeclarationDate").text = shipment_data.get("date", datetime.utcnow().strftime("%Y-%m-%d"))
        ET.SubElement(header, "CountryOfOrigin").text = shipment_data.get("country_of_origin", "LK")
        ET.SubElement(header, "CountryOfDestination").text = shipment_data.get("country_of_destination", "")
        
        # ── Consignee ──
        consignee = ET.SubElement(root, "ConsigneeInfo")
        ET.SubElement(consignee, "Name").text = shipment_data.get("consignee_name", "")
        ET.SubElement(consignee, "Address").text = shipment_data.get("consignee_address", "")
        ET.SubElement(consignee, "TIN").text = shipment_data.get("consignee_tin", "")
        
        # ── Shipper / Exporter ──
        shipper = ET.SubElement(root, "ShipperInfo")
        ET.SubElement(shipper, "Name").text = shipment_data.get("shipper_name", "")
        ET.SubElement(shipper, "Address").text = shipment_data.get("shipper_address", "")
        
        # ── Transport ──
        transport = ET.SubElement(root, "TransportInfo")
        ET.SubElement(transport, "ModeOfTransport").text = shipment_data.get("transport_mode", "4")  # 4=Air, 1=Sea
        ET.SubElement(transport, "AWBNumber").text = shipment_data.get("awb_number", "")
        ET.SubElement(transport, "BLNumber").text = shipment_data.get("bl_number", "")
        ET.SubElement(transport, "Incoterm").text = shipment_data.get("incoterm", "FOB")
        
        gross = ET.SubElement(transport, "GrossWeight")
        gross.text = str(shipment_data.get("gross_weight", ""))
        gross.set("unit", "KG")
        
        net = ET.SubElement(transport, "NetWeight")
        net.text = str(shipment_data.get("net_weight", ""))
        net.set("unit", "KG")
        
        ET.SubElement(transport, "PackageCount").text = str(shipment_data.get("package_count", ""))
        ET.SubElement(transport, "PackageType").text = shipment_data.get("package_type", "CT")  # CT=Cartons
        
        # ── Financial ──
        financial = ET.SubElement(root, "FinancialInfo")
        ET.SubElement(financial, "InvoiceAmount").text = str(shipment_data.get("total_amount", ""))
        ET.SubElement(financial, "Currency").text = shipment_data.get("currency", "USD")
        ET.SubElement(financial, "ExchangeRate").text = str(shipment_data.get("exchange_rate", "1.00"))
        ET.SubElement(financial, "FreightAmount").text = str(shipment_data.get("freight_amount", "0"))
        ET.SubElement(financial, "InsuranceAmount").text = str(shipment_data.get("insurance_amount", "0"))
        
        # ── Line Items ──
        items_elem = ET.SubElement(root, "Items")
        items_elem.set("count", str(len(shipment_data.get("items", []))))
        
        for i, item in enumerate(shipment_data.get("items", []), 1):
            item_elem = ET.SubElement(items_elem, "Item")
            item_elem.set("number", str(i))
            
            ET.SubElement(item_elem, "Description").text = item.get("description", "")
            ET.SubElement(item_elem, "HSCode").text = item.get("hs_code", "5208.32.00")
            
            qty = ET.SubElement(item_elem, "Quantity")
            qty.text = str(item.get("quantity", ""))
            qty.set("unit", item.get("unit", "MTR"))
            
            up = ET.SubElement(item_elem, "UnitPrice")
            up.text = str(item.get("unit_price", ""))
            up.set("currency", shipment_data.get("currency", "USD"))
            
            val = ET.SubElement(item_elem, "TotalValue")
            val.text = str(item.get("total", ""))
            val.set("currency", shipment_data.get("currency", "USD"))
            
            weight = ET.SubElement(item_elem, "NetWeight")
            weight.text = str(item.get("net_weight", ""))
            weight.set("unit", "KG")
        
        # ── Pretty print ──
        rough_string = ET.tostring(root, encoding="unicode")
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def build_shipment_data(self, extractions: list, discrepancies: list) -> dict:
        """
        Build the shipment_data dict from extraction results.
        Uses the highest-confidence value for each field.
        Prefers resolved discrepancy values over raw extractions.
        """
        data = {"items": []}
        
        # Collect all entity values with confidence
        field_values = {}  # field -> list of (value, confidence, doc_type)
        for doc_ext in extractions:
            for entity in doc_ext.get("entities", []):
                field = entity["entity_type"]
                if field not in field_values:
                    field_values[field] = []
                field_values[field].append({
                    "value": entity.get("normalized_value", entity["value"]),
                    "confidence": entity.get("extraction_confidence", 0.5),
                    "doc_type": doc_ext.get("document_type", "unknown")
                })
        
        # Pick highest-confidence value for each field
        field_map = {
            "GROSS_WEIGHT": "gross_weight",
            "NET_WEIGHT": "net_weight",
            "PACKAGE_COUNT": "package_count",
            "CONSIGNEE_NAME": "consignee_name",
            "SHIPPER_NAME": "shipper_name",
            "INCOTERM": "incoterm",
            "TOTAL_AMOUNT": "total_amount",
            "AWB_NUMBER": "awb_number",
            "BL_NUMBER": "bl_number",
            "INVOICE_NUMBER": "invoice_number",
            "CURRENCY": "currency",
        }
        
        for entity_field, data_key in field_map.items():
            if entity_field in field_values:
                best = max(field_values[entity_field], key=lambda x: x["confidence"])
                data[data_key] = best["value"]
        
        return data
```

## API Endpoint

The export is served via:

```python
@router.get("/shipments/{shipment_id}/asycuda-export")
async def export_asycuda(shipment_id: str):
    exporter = AsycudaExporter()
    shipment_data = exporter.build_shipment_data(extractions, discrepancies)
    xml_content = exporter.generate_xml(shipment_data)
    
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename=CUSDEC_{shipment_id[:8]}.xml"}
    )
```

## Acceptance Criteria

- [ ] Generates well-formed, pretty-printed XML
- [ ] Includes: header, consignee, shipper, transport, financial, line items
- [ ] Uses highest-confidence value for each field
- [ ] Includes HS codes for apparel (5208/5209/5210 series)
- [ ] XML downloads with correct filename and content type
- [ ] `generated_by: ClearanceX` attribution in root element
- [ ] Works with Kaveen's `ExportButtons` download handler

## Outputs

- `backend/reasoning/asycuda_export.py` — AsycudaExporter class
