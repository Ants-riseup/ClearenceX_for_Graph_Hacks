# Phase 03 — Synthetic Data Generator

> **Priority:** MUST
> **Estimated Time:** 3–4 hours
> **Dependencies:** None (can start immediately in parallel)
> **Blocks:** Nadija's AI testing, your discrepancy engine testing, demo quality

---

## Goal

Build a Python script that generates realistic-looking shipping documents (PDFs) with controlled discrepancies injected. This provides both training data for Nadija's AI and test data for your reasoning engine.

## Why

1. Real shipping documents are confidential — we can't get them
2. Synthetic docs with KNOWN discrepancies let us prove our system works
3. Judges will ask "where's your data?" — synthetic generator is a strong answer
4. We control the ground truth, so we can measure accuracy precisely

## Document Types to Generate

| Document | Key Fields | Template Style |
|---|---|---|
| Commercial Invoice | Invoice#, consignee, shipper, items, weights, Incoterm, total | Table with header |
| Packing List | Items, carton numbers, gross/net/tare weights, marks | Dense table |
| Air Waybill (AWB) | AWB#, flight, origin/dest, weights, pieces, shipper/consignee | Form-style |
| Bill of Lading | B/L#, vessel, ports, container, weights, packages | Form-style |
| Delivery Order | DO#, reference AWB/BL, consignee, weight, pieces | Simple letter |

## Discrepancies to Inject

| Discrepancy Type | Example | Severity |
|---|---|---|
| Weight mismatch | Invoice: 450kg, AWB: 448.5kg | High |
| Package count mismatch | PL: 25 cartons, AWB: 25 pieces | Medium |
| Internal inconsistency | PL: net(420) + tare(25) ≠ gross(450) | High |
| Consignee typo | Invoice: "ABC Textiles Ltd", AWB: "ABC Textiles Ltd." | Low |
| Incoterm conflict | Invoice: FOB, B/L: CIF | High |
| Date inconsistency | Invoice date after AWB date | Medium |

## Implementation

### 3.1 Create Generator Script

```python
# backend/data/synthetic_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import random
import json
import os
from datetime import datetime, timedelta

class ShipmentDataGenerator:
    """Generates a consistent set of shipment data with optional discrepancies."""
    
    FABRIC_TYPES = [
        "100% Cotton Woven Fabric", "65/35 Polyester/Cotton Blend",
        "100% Polyester Knit Fabric", "Cotton Twill Fabric",
        "Spandex Blend Jersey", "Cotton Poplin Fabric"
    ]
    
    SL_COMPANIES = [
        "MAS Holdings (Pvt) Ltd", "Brandix Lanka Ltd",
        "Hirdaramani Group", "Omega Line Ltd",
        "Star Garments Group", "Hidramani Apparel"
    ]
    
    FOREIGN_COMPANIES = [
        "ABC Textiles Ltd, London", "Global Fashion Corp, New York",
        "Euro Fabrics GmbH, Hamburg", "Asian Trading Co, Singapore",
        "Pacific Imports Ltd, Sydney"
    ]
    
    def generate_shipment(self, inject_discrepancies=True):
        """Generate a complete shipment dataset with all documents."""
        # Base truth data
        base = {
            "invoice_number": f"INV-2024-{random.randint(1000, 9999)}",
            "date": datetime.now() - timedelta(days=random.randint(1, 30)),
            "shipper": random.choice(self.SL_COMPANIES),
            "consignee": random.choice(self.FOREIGN_COMPANIES),
            "gross_weight": round(random.uniform(200, 2000), 2),
            "net_weight": None,  # calculated
            "tare_weight": round(random.uniform(15, 50), 2),
            "package_count": random.randint(10, 100),
            "package_unit": "Cartons",
            "incoterm": random.choice(["FOB", "CIF", "CFR", "EXW"]),
            "currency": "USD",
            "items": self._generate_items(random.randint(3, 8)),
            "awb_number": f"631-{random.randint(10000000, 99999999)}",
            "flight": f"UL {random.randint(100, 999)}",
            "origin": "CMB",
            "destination": random.choice(["LHR", "JFK", "FRA", "SIN"]),
            "vessel": f"MSC {random.choice(['ANNA', 'BELLA', 'CLARA', 'DIANA'])}",
            "bl_number": f"MAEU{random.randint(100000000, 999999999)}",
            "port_loading": "Colombo",
            "port_discharge": random.choice(["Felixstowe", "Rotterdam", "Los Angeles"])
        }
        base["net_weight"] = round(base["gross_weight"] - base["tare_weight"], 2)
        base["total_amount"] = round(sum(item["total"] for item in base["items"]), 2)
        
        # Create document variations (with optional discrepancies)
        docs = {
            "invoice": dict(base),
            "packing_list": dict(base),
            "awb": dict(base),
            "bl": dict(base),
            "do": dict(base)
        }
        
        discrepancies_injected = []
        
        if inject_discrepancies:
            discrepancies_injected = self._inject_discrepancies(docs)
        
        return docs, discrepancies_injected
    
    def _generate_items(self, count):
        items = []
        for i in range(count):
            qty = random.randint(500, 10000)
            unit_price = round(random.uniform(1.5, 8.0), 2)
            items.append({
                "description": random.choice(self.FABRIC_TYPES),
                "gsm": random.choice([120, 140, 160, 180, 200]),
                "width": random.choice([44, 54, 58, 60]),
                "quantity": qty,
                "unit": "MTR",
                "unit_price": unit_price,
                "total": round(qty * unit_price, 2)
            })
        return items
    
    def _inject_discrepancies(self, docs):
        """Randomly inject 1-3 discrepancies."""
        injected = []
        
        # 1. Weight mismatch (AWB differs from Invoice/PL)
        if random.random() > 0.3:
            offset = round(random.uniform(0.5, 5.0), 2)
            docs["awb"]["gross_weight"] = round(docs["invoice"]["gross_weight"] - offset, 2)
            injected.append({
                "type": "weight_mismatch",
                "field": "GROSS_WEIGHT",
                "documents": ["invoice", "awb"],
                "values": [docs["invoice"]["gross_weight"], docs["awb"]["gross_weight"]],
                "severity": "high"
            })
        
        # 2. Internal PL inconsistency (net + tare ≠ gross)
        if random.random() > 0.4:
            docs["packing_list"]["tare_weight"] = round(docs["packing_list"]["tare_weight"] - 5, 2)
            injected.append({
                "type": "internal_inconsistency",
                "field": "WEIGHT_CONSISTENCY",
                "documents": ["packing_list"],
                "detail": f"net({docs['packing_list']['net_weight']}) + tare({docs['packing_list']['tare_weight']}) ≠ gross({docs['packing_list']['gross_weight']})",
                "severity": "high"
            })
        
        # 3. Consignee typo
        if random.random() > 0.5:
            original = docs["invoice"]["consignee"]
            docs["awb"]["consignee"] = original + "."  # Add trailing period
            injected.append({
                "type": "consignee_typo",
                "field": "CONSIGNEE_NAME",
                "documents": ["invoice", "awb"],
                "values": [original, docs["awb"]["consignee"]],
                "severity": "low"
            })
        
        # 4. Package unit mismatch
        if random.random() > 0.5:
            docs["awb"]["package_unit"] = "Pieces"
            injected.append({
                "type": "package_unit_mismatch",
                "field": "PACKAGE_COUNT",
                "documents": ["packing_list", "awb"],
                "values": [f"{docs['packing_list']['package_count']} {docs['packing_list']['package_unit']}", 
                          f"{docs['awb']['package_count']} {docs['awb']['package_unit']}"],
                "severity": "medium"
            })
        
        return injected


class PDFGenerator:
    """Generates realistic PDF documents from shipment data."""
    
    def generate_invoice(self, data: dict, output_path: str):
        """Generate a Commercial Invoice PDF."""
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        
        # Title
        elements.append(Paragraph("<b>COMMERCIAL INVOICE</b>", styles['Title']))
        elements.append(Spacer(1, 10*mm))
        
        # Header info
        header_data = [
            ["Invoice No:", data["invoice_number"], "Date:", data["date"].strftime("%d-%b-%Y")],
            ["Shipper:", data["shipper"], "Incoterm:", data["incoterm"]],
            ["Consignee:", data["consignee"], "Currency:", data["currency"]],
        ]
        header_table = Table(header_data, colWidths=[80, 200, 80, 120])
        header_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 10*mm))
        
        # Items table
        items_header = ["#", "Description", "GSM", "Width", "Qty", "Unit", "Unit Price", "Total"]
        items_rows = [items_header]
        for i, item in enumerate(data["items"], 1):
            items_rows.append([
                str(i), item["description"], str(item["gsm"]),
                f'{item["width"]}"', str(item["quantity"]), item["unit"],
                f'${item["unit_price"]:.2f}', f'${item["total"]:.2f}'
            ])
        
        items_table = Table(items_rows, colWidths=[25, 150, 35, 40, 50, 35, 60, 70])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 5*mm))
        
        # Totals
        totals_data = [
            ["", "", "Total Amount:", f'${data["total_amount"]:,.2f} {data["currency"]}'],
            ["", "", "Gross Weight:", f'{data["gross_weight"]:.2f} KG'],
            ["", "", "Net Weight:", f'{data["net_weight"]:.2f} KG'],
            ["", "", "Packages:", f'{data["package_count"]} {data["package_unit"]}'],
        ]
        totals_table = Table(totals_data, colWidths=[100, 100, 100, 180])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ]))
        elements.append(totals_table)
        
        doc.build(elements)
    
    # Add similar methods for packing_list, awb, bl, do...
    # (Follow same pattern — different layout, same data fields)


def generate_demo_dossier(output_dir: str, dossier_id: int = 1):
    """Generate a complete demo shipment dossier with known discrepancies."""
    os.makedirs(output_dir, exist_ok=True)
    
    data_gen = ShipmentDataGenerator()
    pdf_gen = PDFGenerator()
    
    docs, discrepancies = data_gen.generate_shipment(inject_discrepancies=True)
    
    # Generate PDFs
    pdf_gen.generate_invoice(docs["invoice"], os.path.join(output_dir, f"dossier_{dossier_id}_invoice.pdf"))
    # pdf_gen.generate_packing_list(docs["packing_list"], ...)
    # pdf_gen.generate_awb(docs["awb"], ...)
    
    # Save ground truth
    ground_truth = {
        "dossier_id": dossier_id,
        "discrepancies_injected": discrepancies,
        "documents": {k: {kk: str(vv) if isinstance(vv, datetime) else vv for kk, vv in v.items()} for k, v in docs.items()}
    }
    
    with open(os.path.join(output_dir, f"dossier_{dossier_id}_ground_truth.json"), "w") as f:
        json.dump(ground_truth, f, indent=2, default=str)
    
    return ground_truth


if __name__ == "__main__":
    for i in range(1, 11):
        gt = generate_demo_dossier("sample_documents", dossier_id=i)
        print(f"Dossier {i}: {len(gt['discrepancies_injected'])} discrepancies injected")
```

## Acceptance Criteria

- [ ] Generates at least Commercial Invoice + Packing List + AWB as PDFs
- [ ] PDFs look reasonably professional (tables, headers, readable text)
- [ ] 1–3 discrepancies are injected per dossier
- [ ] Ground truth JSON is saved alongside each dossier
- [ ] Can generate 10+ dossiers in batch
- [ ] PDFs are readable by PaddleOCR (test with Nadija)

## Outputs

- `backend/data/synthetic_generator.py`
- `backend/data/sample_documents/` — 10 demo dossiers
- Ground truth JSON for each dossier (for evaluation)

## Handoff

- Share sample PDFs with Nadija for AI pipeline testing
- Use ground truth JSON to evaluate your own discrepancy detection accuracy
