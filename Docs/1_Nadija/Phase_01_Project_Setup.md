# Phase 01 — React + Vite + TypeScript Project Setup

> **Priority:** MUST
> **Estimated Time:** 1–1.5 hours
> **Dependencies:** None
> **Blocks:** All frontend phases

---

## Goal

Create the frontend project foundation with React, Vite, TypeScript, and all required dependencies. Set up the complete design system, folder structure, API client, and shared TypeScript types.

## Why

Everything the judges see runs through your frontend. This foundation must be solid, consistent, and ready for rapid component development.

## Tasks

### 1.1 Create Vite Project

```bash
# From the project root (ants/)
npx -y create-vite@latest frontend --template react-ts
cd frontend
npm install
```

### 1.2 Install All Dependencies

```bash
# Routing + HTTP
npm install react-router-dom axios

# PDF rendering (Layer 1 XAI — bounding box overlay)
npm install react-pdf pdfjs-dist

# Knowledge Graph visualization (Layer 6 XAI)
npm install vis-network vis-data

# File upload (drag & drop)
npm install react-dropzone

# Icons
npm install lucide-react
```

### 1.3 Create Folder Structure

```bash
mkdir -p src/pages src/components src/hooks src/types src/utils src/assets
```

Final structure:
```
frontend/src/
├── App.tsx                  ← Router setup
├── main.tsx                 ← Entry point
├── index.css                ← Design system + global styles
├── pages/
│   ├── UploadPage.tsx       ← Phase 04
│   ├── DashboardPage.tsx    ← Phase 05
│   └── ReviewPage.tsx       ← Phase 06
├── components/
│   ├── Navbar.tsx           ← Phase 03
│   ├── FileUploader.tsx     ← Phase 04
│   ├── ShipmentCard.tsx     ← Phase 05
│   ├── DualPaneLayout.tsx   ← Phase 06
│   ├── PdfViewer.tsx        ← Phase 07
│   ├── BBoxOverlay.tsx      ← Phase 07
│   ├── ExtractionTable.tsx  ← Phase 08
│   ├── KnowledgeGraph.tsx   ← Phase 09
│   ├── DiscrepancyList.tsx  ← Phase 10
│   ├── ConfidenceBadge.tsx  ← Phase 11
│   ├── LoadingSpinner.tsx   ← Phase 12
│   ├── ErrorState.tsx       ← Phase 12
│   └── ExportButtons.tsx    ← Phase 13
├── hooks/
│   ├── useShipment.ts       ← Phase 14
│   └── useApi.ts            ← Phase 14
├── types/
│   └── index.ts             ← Shared TypeScript interfaces
├── utils/
│   └── api.ts               ← Axios API client
└── assets/
    └── (images, etc.)
```

### 1.4 Create Shared TypeScript Types

```typescript
// frontend/src/types/index.ts

// ============================================
// ENTITY & EXTRACTION
// ============================================
export interface Entity {
  entity_type: string;
  value: string;
  normalized_value: number | string;
  unit: string | null;
  page: number;
  bbox: number[];                   // [x1, y1, x2, y2]
  extraction_confidence: number;    // 0.0–1.0
  classification_confidence: number;
}

export interface DocumentExtraction {
  document_id: string;
  document_type: DocumentType;
  classification_confidence: number;
  entities: Entity[];
}

export type DocumentType =
  | 'commercial_invoice'
  | 'packing_list'
  | 'awb'
  | 'bl'
  | 'freight_invoice'
  | 'delivery_order'
  | 'letter_of_credit'
  | 'unknown';

// ============================================
// DISCREPANCY & XAI LAYERS
// ============================================
export interface DiscrepancySource {
  document_id: string;
  document_type: string;
  value: string;
  page: number;
  bbox: number[];
}

export interface ReasoningChain {
  steps: string[];
  conclusion: string;
}

export interface DecomposedConfidence {
  extraction: number;
  classification: number;
  matching: number;
  overall: number;
  explanation?: string;
  level?: 'green' | 'yellow' | 'red';
}

export interface Counterfactual {
  options: string[];
  recommendation: string;
}

export interface Discrepancy {
  discrepancy_id: string;
  field: string;
  severity: 'high' | 'medium' | 'low';
  severity_score: number;
  status: 'open' | 'resolved' | 'accepted' | 'overridden';
  sources: DiscrepancySource[];
  reasoning_chain: ReasoningChain;
  confidence: DecomposedConfidence;
  counterfactual: Counterfactual;
}

// ============================================
// KNOWLEDGE GRAPH
// ============================================
export interface GraphNode {
  id: string;
  label: string;
  type: 'document' | 'entity';
  color: string | { background: string; border: string };
  status?: 'conflict' | 'match' | 'warning' | 'pending';
  document_type?: string;
  size?: number;
  shape?: string;
  shadow?: boolean;
  font?: { color: string };
}

export interface GraphEdge {
  from: string;
  to: string;
  label: string;
  confidence: number;
  width?: number;
  color?: { color: string };
  font?: { color: string; size: number };
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// ============================================
// SHIPMENT
// ============================================
export interface ShipmentDocument {
  document_id: string;
  filename: string;
  document_type: DocumentType;
  classification_confidence: number;
}

export interface ShipmentStatus {
  shipment_id: string;
  status: 'uploaded' | 'processing' | 'completed' | 'error';
  progress: number;
  documents: ShipmentDocument[];
  processing_time_ms: number;
}

export interface UploadResponse {
  shipment_id: string;
  status: string;
  documents: { document_id: string; filename: string; status: string }[];
}

// ============================================
// AUDIT TRAIL
// ============================================
export interface AuditEntry {
  timestamp: string;
  module: string;
  action: string;
  reasoning?: string;
  confidence: number | null;
  outcome: string;
  details?: Record<string, unknown>;
}

// ============================================
// HELPERS
// ============================================
export type ConfidenceLevel = 'green' | 'yellow' | 'red';

export function getConfidenceLevel(score: number): ConfidenceLevel {
  if (score >= 0.9) return 'green';
  if (score >= 0.7) return 'yellow';
  return 'red';
}

export function getConfidenceColor(level: ConfidenceLevel): string {
  switch (level) {
    case 'green': return '#10b981';
    case 'yellow': return '#f59e0b';
    case 'red': return '#ef4444';
  }
}

export function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'high': return '#ef4444';
    case 'medium': return '#f59e0b';
    case 'low': return '#6366f1';
    default: return '#94a3b8';
  }
}

export function getDocTypeLabel(type: DocumentType): string {
  const labels: Record<string, string> = {
    commercial_invoice: 'Commercial Invoice',
    packing_list: 'Packing List',
    awb: 'Air Waybill',
    bl: 'Bill of Lading',
    freight_invoice: 'Freight Invoice',
    delivery_order: 'Delivery Order',
    letter_of_credit: 'Letter of Credit',
    unknown: 'Unknown',
  };
  return labels[type] || type;
}

export function getDocTypeColor(type: DocumentType): string {
  const colors: Record<string, string> = {
    commercial_invoice: '#4A90D9',
    packing_list: '#50C878',
    awb: '#FFB347',
    bl: '#DDA0DD',
    freight_invoice: '#F0E68C',
    delivery_order: '#87CEEB',
    letter_of_credit: '#CD853F',
    unknown: '#CCCCCC',
  };
  return colors[type] || '#CCCCCC';
}
```

### 1.5 Create API Client

```typescript
// frontend/src/utils/api.ts
import axios from 'axios';
import type {
  UploadResponse,
  ShipmentStatus,
  DocumentExtraction,
  GraphData,
  Discrepancy,
  AuditEntry,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// ============ ENDPOINTS ============

export async function uploadShipment(files: File[]): Promise<UploadResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  const { data } = await api.post<UploadResponse>('/shipments/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function getShipmentStatus(id: string): Promise<ShipmentStatus> {
  const { data } = await api.get<ShipmentStatus>(`/shipments/${id}/status`);
  return data;
}

export async function getExtraction(
  id: string
): Promise<{ shipment_id: string; documents: DocumentExtraction[] }> {
  const { data } = await api.get(`/shipments/${id}/extraction`);
  return data;
}

export async function getGraph(id: string): Promise<GraphData> {
  const { data } = await api.get<GraphData>(`/shipments/${id}/graph`);
  return data;
}

export async function getDiscrepancies(
  id: string
): Promise<{ shipment_id: string; total_discrepancies: number; discrepancies: Discrepancy[] }> {
  const { data } = await api.get(`/shipments/${id}/discrepancies`);
  return data;
}

export async function getAuditTrail(
  id: string
): Promise<{ shipment_id: string; entries: AuditEntry[] }> {
  const { data } = await api.get(`/shipments/${id}/audit-trail`);
  return data;
}

export async function exportAsycuda(id: string): Promise<Blob> {
  const { data } = await api.get(`/shipments/${id}/asycuda-export`, {
    responseType: 'blob',
  });
  return data;
}

// ============ HELPERS ============

export function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}
```

### 1.6 Create Design System CSS

```css
/* frontend/src/index.css */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ============================================ */
/*  DESIGN TOKENS                               */
/* ============================================ */
:root {
  /* Background */
  --bg-primary: #0a0a1a;
  --bg-secondary: #12122e;
  --bg-card: #1a1a42;
  --bg-card-hover: #222260;
  --bg-elevated: #1e1e50;

  /* Accent */
  --accent-primary: #6366f1;
  --accent-secondary: #8b5cf6;
  --accent-tertiary: #a78bfa;
  --accent-glow: rgba(99, 102, 241, 0.25);
  --accent-glow-strong: rgba(99, 102, 241, 0.5);

  /* Confidence */
  --conf-high: #10b981;
  --conf-medium: #f59e0b;
  --conf-low: #ef4444;

  /* Severity */
  --sev-high: #ef4444;
  --sev-medium: #f59e0b;
  --sev-low: #6366f1;

  /* Text */
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --text-inverse: #0a0a1a;

  /* Borders */
  --border-subtle: rgba(255, 255, 255, 0.06);
  --border-medium: rgba(255, 255, 255, 0.12);
  --border-accent: rgba(99, 102, 241, 0.4);

  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.4);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.5);
  --shadow-lg: 0 8px 30px rgba(0, 0, 0, 0.6);
  --shadow-glow: 0 0 20px var(--accent-glow);

  /* Radius */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-full: 9999px;

  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-normal: 250ms ease;
  --transition-slow: 400ms ease;
}

/* ============================================ */
/*  BASE RESET                                  */
/* ============================================ */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  font-size: 16px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.6;
  min-height: 100vh;
}

code, pre, .mono {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

a {
  color: var(--accent-primary);
  text-decoration: none;
  transition: color var(--transition-fast);
}
a:hover {
  color: var(--accent-tertiary);
}

/* ============================================ */
/*  UTILITY CLASSES                             */
/* ============================================ */
.glass-card {
  background: rgba(26, 26, 66, 0.7);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  transition: all var(--transition-normal);
}
.glass-card:hover {
  border-color: var(--border-accent);
  box-shadow: var(--shadow-glow);
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.badge-high { background: rgba(239, 68, 68, 0.15); color: var(--sev-high); border: 1px solid rgba(239, 68, 68, 0.3); }
.badge-medium { background: rgba(245, 158, 11, 0.15); color: var(--sev-medium); border: 1px solid rgba(245, 158, 11, 0.3); }
.badge-low { background: rgba(99, 102, 241, 0.15); color: var(--sev-low); border: 1px solid rgba(99, 102, 241, 0.3); }

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: var(--radius-md);
  font-family: inherit;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.btn-primary {
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  color: white;
  box-shadow: 0 2px 10px var(--accent-glow);
}
.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 20px var(--accent-glow-strong);
}
.btn-primary:active {
  transform: translateY(0);
}
.btn-secondary {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-medium);
}
.btn-secondary:hover {
  background: var(--bg-card-hover);
  border-color: var(--border-accent);
}

/* ============================================ */
/*  ANIMATIONS                                  */
/* ============================================ */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 5px var(--sev-high); }
  50% { box-shadow: 0 0 20px var(--sev-high), 0 0 40px rgba(239, 68, 68, 0.3); }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes slideInRight {
  from { opacity: 0; transform: translateX(20px); }
  to { opacity: 1; transform: translateX(0); }
}

.animate-fade-in { animation: fadeIn 0.4s ease forwards; }
.animate-slide-in { animation: slideInRight 0.3s ease forwards; }
.animate-pulse-glow { animation: pulse-glow 2s ease-in-out infinite; }

/* ============================================ */
/*  SCROLLBAR                                   */
/* ============================================ */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-medium); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }
```

### 1.7 Create `.env` File

```bash
# frontend/.env
VITE_API_URL=http://localhost:8000/api
```

### 1.8 Verify Setup

```bash
cd frontend
npm run dev
# Should start at http://localhost:5173
# Open browser → should see Vite default page with dark background
```

## Acceptance Criteria

- [ ] `npm run dev` starts at `http://localhost:5173` without errors
- [ ] TypeScript compiles cleanly (`npx tsc --noEmit`)
- [ ] All dependencies installed (react-pdf, vis-network, react-dropzone, etc.)
- [ ] `src/types/index.ts` has all shared interfaces
- [ ] `src/utils/api.ts` exports all endpoint functions
- [ ] `src/index.css` has full design system with dark theme
- [ ] Folder structure matches the plan
- [ ] `.env` configured with backend URL

## Outputs

- Complete React + Vite + TypeScript project
- Design system ready for all components
- API client ready for backend integration
- TypeScript types matching Aloka's API contracts

## Next

Proceed to Phase 02 (FastAPI Skeleton) or Phase 03 (App Shell) — either can start immediately.
