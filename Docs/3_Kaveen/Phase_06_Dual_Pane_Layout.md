# Phase 06 — Dual-Pane Review Layout

> **Priority:** MUST
> **Estimated Time:** 3–4 hours
> **Dependencies:** Phase 03 (app shell), Phase 05 (navigates here from dashboard)
> **Blocks:** Phases 07–13 (all component slots live inside this layout)

---

## Goal

Build the main review interface — the **core screen** of the entire application. Two panes side-by-side with independent tab switching. This is where users spend 90% of their time.

## Why

The dual-pane design lets the user see data (extractions, discrepancies) on the left and visual evidence (PDF, knowledge graph) on the right simultaneously. Cross-referencing is instant — click an entity → see it highlighted in the PDF.

## Layout

```
┌───────────────────────────────────────────────────────┐
│  ◀ Back   Shipment: abc12345   Status: ✅ Completed    │
├───────────────────────┬───────────────────────────────┤
│  LEFT PANE (45%)      │  RIGHT PANE (55%)              │
│                       │                                │
│  [Extractions]        │  [PDF View] [Graph] [Audit]    │
│  [Discrepancies]      │                                │
│  [Export]              │                                │
│                       │                                │
│  Entity table         │  PDF + bounding box overlays   │
│  OR                   │  OR                            │
│  Discrepancy list     │  Interactive knowledge graph   │
│  w/ reasoning chains  │  OR                            │
│  & counterfactuals    │  Chronological audit trail     │
│                       │                                │
└───────────────────────┴───────────────────────────────┘
```

## Implementation

### 6.1 ReviewPage Component

```tsx
// frontend/src/pages/ReviewPage.tsx
import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, FileText, AlertTriangle, Download,
  Eye, GitBranch, ScrollText, Shield
} from 'lucide-react';
import { useShipmentData } from '../hooks/useShipment';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorState } from '../components/ErrorState';
import type { Entity } from '../types';

// Placeholder components — replaced in Phases 07–13
const Placeholder: React.FC<{ name: string }> = ({ name }) => (
  <div style={{ padding: 20, color: 'var(--text-muted)', textAlign: 'center' }}>
    <p>{name} — component coming in later phase</p>
  </div>
);

type LeftTab = 'extractions' | 'discrepancies' | 'export';
type RightTab = 'pdf' | 'graph' | 'audit';

export const ReviewPage: React.FC = () => {
  const { shipmentId } = useParams<{ shipmentId: string }>();
  const navigate = useNavigate();

  // Tab state
  const [leftTab, setLeftTab] = useState<LeftTab>('extractions');
  const [rightTab, setRightTab] = useState<RightTab>('pdf');

  // Cross-pane interaction state
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);

  // Data fetching (Phase 14 hook — use placeholder until then)
  // const { extraction, graph, discrepancies, auditTrail, loading, error } = useShipmentData(shipmentId!);

  const handleEntitySelect = (entity: Entity) => {
    setSelectedEntity(entity);
    setRightTab('pdf'); // Switch to PDF view to show the bounding box
  };

  const handleGraphNodeClick = (nodeId: string, nodeType: string) => {
    if (nodeType === 'entity') {
      setLeftTab('discrepancies'); // Show discrepancy for this entity
    } else if (nodeType === 'document') {
      setSelectedDocId(nodeId);
      setRightTab('pdf');
    }
  };

  return (
    <div className="review-page animate-fade-in">
      {/* ── Top Bar ── */}
      <div className="review-topbar">
        <button className="btn btn-secondary btn-sm" onClick={() => navigate('/dashboard')}>
          <ArrowLeft size={16} /> Back
        </button>
        <div className="topbar-info">
          <Shield size={18} color="var(--accent-primary)" />
          <h2>Shipment <span className="mono">{shipmentId?.slice(0, 8)}</span></h2>
        </div>
        <span className="badge badge-completed">✅ Completed</span>
      </div>

      {/* ── Dual Pane ── */}
      <div className="dual-pane">

        {/* ── LEFT PANE ── */}
        <div className="pane pane-left glass-card">
          <div className="pane-tabs">
            {([
              { key: 'extractions', label: 'Extractions', icon: FileText },
              { key: 'discrepancies', label: 'Discrepancies', icon: AlertTriangle },
              { key: 'export', label: 'Export', icon: Download },
            ] as const).map(tab => (
              <button
                key={tab.key}
                className={`pane-tab ${leftTab === tab.key ? 'active' : ''}`}
                onClick={() => setLeftTab(tab.key)}
              >
                <tab.icon size={15} />
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
          <div className="pane-content">
            {leftTab === 'extractions' && <Placeholder name="ExtractionTable (Phase 08)" />}
            {leftTab === 'discrepancies' && <Placeholder name="DiscrepancyList (Phase 10)" />}
            {leftTab === 'export' && <Placeholder name="ExportButtons (Phase 13)" />}
          </div>
        </div>

        {/* ── RIGHT PANE ── */}
        <div className="pane pane-right glass-card">
          <div className="pane-tabs">
            {([
              { key: 'pdf', label: 'PDF View', icon: Eye },
              { key: 'graph', label: 'Knowledge Graph', icon: GitBranch },
              { key: 'audit', label: 'Audit Trail', icon: ScrollText },
            ] as const).map(tab => (
              <button
                key={tab.key}
                className={`pane-tab ${rightTab === tab.key ? 'active' : ''}`}
                onClick={() => setRightTab(tab.key)}
              >
                <tab.icon size={15} />
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
          <div className="pane-content">
            {rightTab === 'pdf' && <Placeholder name="PdfViewer + BBox (Phase 07)" />}
            {rightTab === 'graph' && <Placeholder name="KnowledgeGraph vis.js (Phase 09)" />}
            {rightTab === 'audit' && <Placeholder name="AuditTrail log (Phase 12)" />}
          </div>
        </div>
      </div>
    </div>
  );
};
```

### 6.2 Dual Pane CSS

```css
/* Add to index.css */

/* ============================================ */
/*  REVIEW PAGE                                 */
/* ============================================ */
.review-page {
  height: calc(100vh - 48px);
  display: flex;
  flex-direction: column;
  gap: 0;
}

.review-topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 0 16px;
  flex-shrink: 0;
}

.topbar-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.topbar-info h2 {
  font-size: 1.1rem;
  font-weight: 600;
}

/* ============================================ */
/*  DUAL PANE                                   */
/* ============================================ */
.dual-pane {
  display: flex;
  gap: 12px;
  flex: 1;
  min-height: 0; /* Critical: allows flex children to shrink below content */
}

.pane {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: var(--radius-lg);
}

.pane-left {
  width: 42%;
  min-width: 340px;
}

.pane-right {
  flex: 1;
}

/* ── Pane Tabs ── */
.pane-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-subtle);
  padding: 0 4px;
  flex-shrink: 0;
  background: rgba(0, 0, 0, 0.15);
}

.pane-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 11px 14px;
  background: none;
  border: none;
  color: var(--text-muted);
  font-family: inherit;
  font-size: 0.82rem;
  font-weight: 500;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.pane-tab:hover {
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.03);
}

.pane-tab.active {
  color: var(--accent-primary);
  border-bottom-color: var(--accent-primary);
  background: rgba(99, 102, 241, 0.06);
}

/* ── Pane Content ── */
.pane-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0; /* Components manage their own padding */
  min-height: 0;
}
```

### 6.3 Key Interaction: Cross-Pane Communication

The review page manages shared state between left and right panes:

```
[LEFT: Click entity row] → setSelectedEntity() → [RIGHT: PDF highlights bbox]
[LEFT: Click entity row] → setRightTab('pdf')  → [RIGHT: Switches to PDF view]

[RIGHT: Click graph node] → setLeftTab('discrepancies') → [LEFT: Shows discrepancy]
[RIGHT: Click doc node]   → setSelectedDocId()            → [RIGHT: PDF switches doc]

[LEFT: Click discrepancy source] → setSelectedEntity(source) → [RIGHT: PDF highlights]
```

This cross-pane interaction is what makes the review page powerful. The components in later phases just need to call the callbacks passed as props.

## Acceptance Criteria

- [ ] Two-pane layout fills the available viewport height
- [ ] Left pane: 42% width, right pane: flexible remaining
- [ ] Both panes have independent tab bars
- [ ] Tab switching is smooth with active indicator
- [ ] Left tabs: Extractions / Discrepancies / Export
- [ ] Right tabs: PDF View / Knowledge Graph / Audit Trail
- [ ] Top bar shows shipment ID, back button, status badge
- [ ] Each pane scrolls independently
- [ ] Placeholder content renders for each tab
- [ ] Cross-pane state handlers are wired (`handleEntitySelect`, `handleGraphNodeClick`)
- [ ] `min-height: 0` prevents flex overflow issues

## Outputs

- `src/pages/ReviewPage.tsx` — the core review interface
- Dual pane CSS in `index.css`
- Placeholder slots ready for components from Phases 07–13
