# Export Workflow, ASYCUDA Integration, and ClearanceX SRS Guide

## 1. Introduction to the Problem & Solution

### 1.1 Context & The Core Pain Point
In the fast-paced apparel manufacturing sector, clearing imported raw materials or exporting finished goods through Sri Lanka Customs requires compiling a highly detailed Customs Declaration (CUSDEC) via the ASYCUDA system. This process relies on extracting data from highly unstandardized, multi-page shipping dossiers (Commercial Invoices, Packing Lists, Airway Bills, Bills of Lading, and Delivery Orders). 

Frequent discrepancies across these documents—such as mismatched gross weights, contradictory Incoterms, or misaligned packaging counts—force shipping executives into hours of manual cross-referencing. Human errors in this workflow lead to rejected declarations, extensive clearance delays, missed shipping cut-offs, and severe financial penalties (port demurrage or bank payment freezes).

### 1.2 The Proposed Solution: ClearanceX
ClearanceX is an Intelligent Decision Support System that automates the ingestion, reconciliation, and validation of complex shipping dossiers for both **Imports** and **Exports**. The system reads unstructured supply chain documents, extracts necessary entities, and utilizes a cross-document matching engine to instantly flag discrepancies. Instead of replacing the human operator, ClearanceX serves as an intelligent copilot, surfacing conflicts, recommending compliant values, and generating bulk upload files.

---

## 2. Software Requirements Specification (SRS) - ClearanceX

### 2.1 Project Overview & Competition Alignment (Theme 1: XAI)
*   **Theme:** Develop a Decision Support System Using Explainable AI (XAI).
*   **XAI Justification:** Customs declarations and bank letter of credit negotiations are legally binding processes. Black-box predictions are unacceptable. ClearanceX implements **traceable bounding box attributions**, **confidence metrics**, and **human-readable rule justifications** to empower the shipping executive to verify and approve declaration data rapidly.

### 2.2 Functional Requirements

#### Module 1: Document Ingestion & Optical Recognition
*   **FR-1.1:** The system shall allow users to upload a complete shipment dossier containing core import or export document types (Commercial Invoice, Packing List, MAWB/HAWB, Bill of Lading, Freight Invoice, DO/FAN, Letter of Credit).
*   **FR-1.2:** The system shall automatically classify uploaded documents by type with a confidence threshold $\ge 95\%$.
*   **FR-1.3:** The OCR engine shall extract both text and spatial coordinates (bounding boxes $[x, y, w, h]$) across all pages.

#### Module 2: Entity Extraction & Canonical Normalization
*   **FR-2.1:** The system shall extract multi-line tabular items from Commercial Invoices and Packing Lists (Item Description, Fabric Composition, GSM, Width, Quantity, Unit of Measure, Unit Price, Total Price).
*   **FR-2.2:** The system shall extract header-level metadata (Consignee/Shipper Name & Address, Invoice Number, Incoterm, Flight/Vessel Number, Transport Document Number, Gross/Net Weight, Package Count, Shipping Marks).
*   **FR-2.3:** The system shall normalize varying terminology (e.g., mapping "T/T 30 Days", "Remittance: Wire" to canonical payment terms).

#### Module 3: Cross-Document Discrepancy & Reconciliation Engine
The system shall execute cross-document verification rules across all identified fields:
*   **Gross / Net Weight:** Compare Packing List against Transport Documents (AWB / B/L / DO). Flag variances $> 0.5\%$.
*   **Package Count:** Cross-reference roll/carton breakdowns against pallet or container summaries.
*   **Cargo Description:** Flag fiber composition or item description contradictions.
*   **Incoterms & Freight:** Ensure invoice Incoterms align with freight prepaid/collect markings on transport bills.
*   **Consignee Details:** Catch typographical errors across documents.

#### Module 4: Explainable AI (XAI) Decision Support Interface
*   **FR-4.1 (Visual Attribution):** When an executive clicks any field in the preparation sheet, the system shall render a split-screen view highlighting the exact location and page in the original PDF source.
*   **FR-4.2 (Conflict Explanations):** For every detected mismatch, the system shall generate a structured natural language explanation with an actionable recommendation.
*   **FR-4.3 (Confidence Scoring):** Every extracted value and matching recommendation shall display a color-coded confidence score (Green $\ge 90\%$, Yellow $70\text{--}89\%$, Red $< 70\%$).

#### Module 5: Automated File Generation (One-Click ASYCUDA Export)
*   **FR-5.1:** The system shall compile validated data into standard ASYCUDA-compliant XML or flat-file (`.txt`) formats for Direct Trader Input (DTI) bulk upload, eliminating manual copy-pasting.

---

## 3. Executive Summary

### 3.1 Project Outline
*   **Identified Problem:** High-volume import and export shipments involve unstandardized documents with frequent cross-document mismatches, causing manual fatigue, customs rejection, demurrage penalties, and bank LC payment freezes.
*   **Proposed Solution:** ClearanceX automates data extraction, cross-document reconciliation, and CUSDEC/DTI file generation.
*   **Innovation:** Integrates Explainable AI (XAI) via visual bounding boxes and natural-language justifications, ensuring full auditability and eliminating "black box" risk.
*   **Target Users:** Shipping and Logistics Executives, Customs Brokers, and Compliance Managers.
*   **Expected Impact:** Reduces multi-line CUSDEC preparation time from 6–8 hours to under 15 minutes, drives customs rejection rates to near zero, and prevents costly delays.
*   **Key Technologies:** Vision-Language Models (LayoutLMv3), spatial OCR, Python (FastAPI), PostgreSQL, and a React-based dual-pane UI.

---

## 4. Import vs. Export Workflows & Document Mapping

### 4.1 Import Workflow & Mismatches
In imports, the executive reconciles documents received from third-party suppliers, airlines, and forwarders to clear raw materials and prevent port demurrage.
*   **Core Documents:** Commercial Invoice, Packing List, Master Airway Bill (MAWB), House Airway Bill (HAWB), Freight Invoice, Delivery Order (DO) / Freight Arrival Notice (FAN).
*   **Frequent Overlapping Mismatches:** Gross/Net weight discrepancies, package count mismatches, cargo description contradictions, Incoterm/freight charge conflicts, and consignee typographical errors.

### 4.2 Export Workflow (Chronological Order)

#### Phase 1: The Order (Before Production Finishes)
*   **Documents Received:** Purchase Order (PO) from the Buyer and Letter of Credit (LC) from the Bank.
*   **Action:** Study strict formatting and compliance rules required for payment.

#### Phase 2: Cargo Ready (Internal Handover)
*   **Documents Received:** Factory Packing List.
*   **Documents Made:** Commercial Invoice based on PO prices and packing list.

#### Phase 3: Booking Freight (The Forwarder)
*   **Documents Sent:** Commercial Invoice and Factory Packing List to the Freight Forwarder.
*   **Documents Received:** Draft Bill of Lading (B/L) or Draft Airway Bill (AWB).
*   **Action (AI Use Case):** Cross-check Draft B/L/AWB against the Factory Packing List to catch count or weight errors before cargo leaves the factory.

#### Phase 4: Customs Declaration (Export CUSDEC)
*   **Documents Used:** Commercial Invoice, Factory Packing List, BOI Approval.
*   **Documents Made:** Export CUSDEC (generated via ClearanceX's one-click ASYCUDA XML export tool). Customs issues a Gate Pass/Warrant.

#### Phase 5: Dispatching Goods
*   **Documents Made:** Cargo Dispatch Note (CDN).
*   **Action:** Trucks transport goods to the port/airport with the CDN and Customs Gate Pass.

#### Phase 6: Securing Final Documents
*   **Documents Received:** Final Original Bill of Lading (B/L) or Original AWB issued by the forwarder.
*   **Documents Made:** Certificate of Origin (COO) via the Chamber of Commerce.

#### Phase 7: Getting Paid (Bank Negotiation)
*   **Action:** Submit the final document package (Original B/L, Commercial Invoice, Packing List, COO) to the bank for Letter of Credit (LC) clearance and payment release.

---

## 5. How "One-Click ASYCUDA Export" Works (No Copy-Pasting)
ASYCUDA World supports **Direct Trader Input (DTI)** via bulk XML or flat-file uploads. 
1.  **Extraction & Matching:** ClearanceX extracts and reconciles all data from invoices and packing lists.
2.  **File Compilation:** The tool structures approved data into the exact XML/TXT schema mandated by Sri Lanka Customs.
3.  **Download & Upload:** The user clicks "Download ASYCUDA File," logs into ASYCUDA World, and clicks **"Import from File."** All 100+ line items populate instantly.