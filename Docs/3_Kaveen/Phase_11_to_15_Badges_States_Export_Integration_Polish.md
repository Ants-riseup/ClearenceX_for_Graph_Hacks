# Phase 11 — Confidence Badges

> **Priority:** MUST
> **Estimated Time:** 1–2 hours
> **Dependencies:** Phase 01 (TypeScript types)
> **Blocks:** Phases 08, 10 (both use this component)

---

## Goal

Build a reusable `<ConfidenceBadge>` component that shows a colored dot + percentage. Clickable to expand the 3-part decomposed confidence breakdown (extraction / classification / matching).

## Implementation

```tsx
// frontend/src/components/ConfidenceBadge.tsx
import React, { useState } from 'react';
import { getConfidenceLevel, getConfidenceColor } from '../types';

interface Props {
  overall: number;                    // 0.0–1.0 (required)
  extraction?: number;                // Optional decomposed
  classification?: number;
  matching?: number;
  explanation?: string;               // Human-readable summary
  size?: 'sm' | 'md';                // Badge size
}

export const ConfidenceBadge: React.FC<Props> = ({
  overall, extraction, classification, matching, explanation, size = 'sm'
}) => {
  const [expanded, setExpanded] = useState(false);
  const level = getConfidenceLevel(overall);
  const color = getConfidenceColor(level);
  const hasBreakdown = extraction !== undefined;

  return (
    <div
      className={`confidence-badge conf-${size} ${hasBreakdown ? 'conf-expandable' : ''}`}
      onClick={(e) => {
        if (hasBreakdown) {
          e.stopPropagation();
          setExpanded(!expanded);
        }
      }}
    >
      <div className="conf-main">
        <span className="conf-dot" style={{ backgroundColor: color }} />
        <span className="conf-value" style={{ color }}>
          {Math.round(overall * 100)}%
        </span>
      </div>

      {expanded && hasBreakdown && (
        <div className="conf-dropdown animate-fade-in" onClick={e => e.stopPropagation()}>
          <div className="conf-dropdown-row">
            <span className="conf-label">Extraction</span>
            <span className="conf-score" style={{ color: getConfidenceColor(getConfidenceLevel(extraction!)) }}>
              {Math.round(extraction! * 100)}%
            </span>
          </div>
          {classification !== undefined && (
            <div className="conf-dropdown-row">
              <span className="conf-label">Classification</span>
              <span className="conf-score" style={{ color: getConfidenceColor(getConfidenceLevel(classification)) }}>
                {Math.round(classification * 100)}%
              </span>
            </div>
          )}
          {matching !== undefined && (
            <div className="conf-dropdown-row">
              <span className="conf-label">Matching</span>
              <span className="conf-score" style={{ color: getConfidenceColor(getConfidenceLevel(matching)) }}>
                {Math.round(matching * 100)}%
              </span>
            </div>
          )}
          {explanation && (
            <p className="conf-explanation">{explanation}</p>
          )}
        </div>
      )}
    </div>
  );
};
```

### CSS

```css
/* ============================================ */
/*  CONFIDENCE BADGE                            */
/* ============================================ */
.confidence-badge {
  position: relative;
  display: inline-flex;
  flex-direction: column;
  align-items: flex-end;
}

.conf-expandable { cursor: pointer; }

.conf-main {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.conf-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.conf-value {
  font-size: 0.78rem;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
}

.conf-sm .conf-dot { width: 6px; height: 6px; }
.conf-sm .conf-value { font-size: 0.72rem; }

.conf-md .conf-dot { width: 8px; height: 8px; }
.conf-md .conf-value { font-size: 0.85rem; }

.conf-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 180px;
  padding: 10px 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  z-index: 50;
}

.conf-dropdown-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 3px 0;
  font-size: 0.78rem;
}

.conf-label { color: var(--text-secondary); }
.conf-score { font-family: 'JetBrains Mono', monospace; font-weight: 600; }

.conf-explanation {
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid var(--border-subtle);
  font-size: 0.72rem;
  color: var(--text-muted);
  line-height: 1.4;
}
```

## Acceptance Criteria

- [ ] Shows colored dot (green/yellow/red) + percentage
- [ ] Color thresholds: green ≥ 90%, yellow 70–89%, red < 70%
- [ ] Clickable when decomposed scores provided → shows dropdown
- [ ] Dropdown shows extraction, classification, matching breakdown
- [ ] Optional explanation text below breakdown
- [ ] Dropdown positions correctly (doesn't overflow pane)
- [ ] Supports `sm` and `md` size variants
- [ ] Works as inline element (doesn't break table row layout)

---

# Phase 12 — Loading / Error / Empty States

> **Priority:** MUST
> **Estimated Time:** 1–2 hours
> **Dependencies:** Phase 01 (design system)

## Goal

Create polished state components for loading, error, and empty conditions. These prevent the app from looking broken during demo.

## Implementation

```tsx
// frontend/src/components/LoadingSpinner.tsx
import React from 'react';
import { Loader2 } from 'lucide-react';

interface Props {
  message?: string;
  steps?: string[];    // For multi-step progress
  currentStep?: number;
}

export const LoadingSpinner: React.FC<Props> = ({ message = 'Loading...', steps, currentStep = 0 }) => (
  <div className="loading-state">
    <Loader2 size={36} className="spin" color="var(--accent-primary)" />
    <p className="loading-message">{message}</p>
    {steps && (
      <div className="loading-steps">
        {steps.map((step, i) => (
          <div key={i} className={`loading-step ${i < currentStep ? 'step-done' : i === currentStep ? 'step-active' : ''}`}>
            <span className="step-indicator">{i < currentStep ? '✓' : i === currentStep ? '●' : '○'}</span>
            <span>{step}</span>
          </div>
        ))}
      </div>
    )}
  </div>
);

// frontend/src/components/ErrorState.tsx
import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface Props {
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<Props> = ({ message = 'Something went wrong', onRetry }) => (
  <div className="error-state">
    <AlertCircle size={36} color="var(--sev-high)" />
    <p>{message}</p>
    {onRetry && (
      <button className="btn btn-secondary" onClick={onRetry}>
        <RefreshCw size={16} /> Retry
      </button>
    )}
  </div>
);
```

### CSS

```css
.loading-state, .error-state {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding: 60px 20px; gap: 12px; text-align: center;
}
.loading-message { color: var(--text-secondary); font-size: 0.9rem; }

.loading-steps { display: flex; flex-direction: column; gap: 6px; margin-top: 8px; }
.loading-step {
  display: flex; align-items: center; gap: 8px;
  font-size: 0.82rem; color: var(--text-muted);
}
.step-done { color: var(--conf-high); }
.step-active { color: var(--accent-primary); font-weight: 600; }
.step-indicator { width: 16px; text-align: center; }

.error-state p { color: var(--text-secondary); margin-bottom: 8px; }
```

### 12.2 Audit Trail Viewer (Right Pane Tab)

This component renders in the right pane under the "Audit Trail" tab. It shows a chronological log of every AI decision from Aloka's `AuditLogger`.

```tsx
// frontend/src/components/AuditTrailViewer.tsx
import React, { useState, useEffect } from 'react';
import { ScrollText, Clock, Shield, Filter, ChevronDown, ChevronRight } from 'lucide-react';
import type { AuditEntry } from '../types';

// Module → color mapping
const MODULE_COLORS: Record<string, string> = {
  CLASSIFIER: '#4A90D9',
  NER: '#50C878',
  NORMALIZER: '#FFB347',
  GRAPH: '#8b5cf6',
  RECONCILER: '#f59e0b',
  XAI_LAYER_2: '#6366f1',
  XAI_LAYER_3: '#6366f1',
  XAI_LAYER_4: '#6366f1',
  EXPORT: '#10b981',
  USER: '#ef4444',
  API: '#94a3b8',
};

interface Props {
  entries: AuditEntry[];
  shipmentId: string;
}

export const AuditTrailViewer: React.FC<Props> = ({ entries, shipmentId }) => {
  const [filter, setFilter] = useState<string | null>(null);
  const [expandedIdx, setExpandedIdx] = useState<Set<number>>(new Set());

  const modules = [...new Set(entries.map(e => e.module))];
  const filtered = filter ? entries.filter(e => e.module === filter) : entries;

  const toggleExpand = (idx: number) => {
    setExpandedIdx(prev => {
      const next = new Set(prev);
      next.has(idx) ? next.delete(idx) : next.add(idx);
      return next;
    });
  };

  const formatTime = (ts: string) => {
    const d = new Date(ts);
    return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  return (
    <div className="audit-trail-viewer">
      {/* Header */}
      <div className="audit-header">
        <div className="audit-title">
          <ScrollText size={16} color="var(--accent-primary)" />
          <span>{filtered.length} decisions logged</span>
        </div>
        <div className="audit-filters">
          <button
            className={`audit-filter-btn ${!filter ? 'active' : ''}`}
            onClick={() => setFilter(null)}
          >All</button>
          {modules.map(m => (
            <button
              key={m}
              className={`audit-filter-btn ${filter === m ? 'active' : ''}`}
              onClick={() => setFilter(m)}
              style={{ '--mod-color': MODULE_COLORS[m] || '#94a3b8' } as React.CSSProperties}
            >{m}</button>
          ))}
        </div>
      </div>

      {/* Timeline */}
      <div className="audit-timeline">
        {filtered.map((entry, idx) => {
          const isExpanded = expandedIdx.has(idx);
          const modColor = MODULE_COLORS[entry.module] || '#94a3b8';
          return (
            <div key={idx} className="audit-entry" onClick={() => toggleExpand(idx)}>
              <div className="audit-line">
                <div className="audit-dot" style={{ backgroundColor: modColor }} />
                {idx < filtered.length - 1 && <div className="audit-connector" />}
              </div>
              <div className="audit-content">
                <div className="audit-entry-header">
                  <span className="audit-module" style={{ color: modColor }}>{entry.module}</span>
                  <span className="audit-time mono">
                    <Clock size={11} /> {formatTime(entry.timestamp)}
                  </span>
                </div>
                <p className="audit-action">{entry.action}</p>
                {entry.outcome && (
                  <span className={`audit-outcome ${entry.outcome === 'Accepted' || entry.outcome === 'PASS' ? 'outcome-pass' : 'outcome-flag'}`}>
                    {entry.outcome}
                  </span>
                )}
                {isExpanded && (entry.reasoning || entry.details) && (
                  <div className="audit-details animate-fade-in">
                    {entry.reasoning && <p className="audit-reasoning">{entry.reasoning}</p>}
                    {entry.confidence != null && (
                      <span className="audit-conf mono">Confidence: {Math.round(entry.confidence * 100)}%</span>
                    )}
                    {entry.details && (
                      <pre className="audit-json mono">{JSON.stringify(entry.details, null, 2)}</pre>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {entries.length === 0 && (
        <div className="audit-empty">
          <Shield size={32} color="var(--text-muted)" />
          <p>No audit entries yet</p>
        </div>
      )}
    </div>
  );
};
```

### Audit Trail CSS

```css
/* ============================================ */
/*  AUDIT TRAIL VIEWER                          */
/* ============================================ */
.audit-trail-viewer { padding: 8px; height: 100%; display: flex; flex-direction: column; }

.audit-header { flex-shrink: 0; margin-bottom: 12px; }
.audit-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 0.85rem; font-weight: 600; margin-bottom: 8px;
}

.audit-filters { display: flex; flex-wrap: wrap; gap: 4px; }
.audit-filter-btn {
  padding: 3px 10px; border-radius: var(--radius-full); border: 1px solid var(--border-subtle);
  background: none; color: var(--text-muted); font-family: inherit; font-size: 0.7rem;
  cursor: pointer; transition: all var(--transition-fast); text-transform: uppercase;
  letter-spacing: 0.04em; font-weight: 500;
}
.audit-filter-btn:hover { border-color: var(--mod-color, var(--text-secondary)); color: var(--text-secondary); }
.audit-filter-btn.active {
  background: rgba(99, 102, 241, 0.1); border-color: var(--accent-primary); color: var(--accent-primary);
}

.audit-timeline { flex: 1; overflow-y: auto; padding-right: 4px; }

.audit-entry {
  display: flex; gap: 12px; cursor: pointer;
  transition: background var(--transition-fast); padding: 2px 4px; border-radius: var(--radius-sm);
}
.audit-entry:hover { background: rgba(255, 255, 255, 0.02); }

.audit-line {
  display: flex; flex-direction: column; align-items: center; flex-shrink: 0; width: 12px;
}
.audit-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 6px; }
.audit-connector { width: 1px; flex: 1; background: var(--border-subtle); margin: 2px 0; }

.audit-content { flex: 1; padding-bottom: 12px; min-width: 0; }
.audit-entry-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px; }
.audit-module { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
.audit-time { font-size: 0.68rem; color: var(--text-muted); display: flex; align-items: center; gap: 3px; }
.audit-action { font-size: 0.8rem; color: var(--text-primary); margin: 0; line-height: 1.4; }

.audit-outcome {
  display: inline-block; margin-top: 4px; padding: 1px 8px; border-radius: var(--radius-full);
  font-size: 0.65rem; font-weight: 600; text-transform: uppercase;
}
.outcome-pass { background: rgba(16, 185, 129, 0.1); color: var(--conf-high); }
.outcome-flag { background: rgba(239, 68, 68, 0.1); color: var(--conf-low); }

.audit-details { margin-top: 6px; padding: 8px; background: rgba(0,0,0,0.15); border-radius: var(--radius-sm); }
.audit-reasoning { font-size: 0.78rem; color: var(--text-secondary); margin: 0 0 4px; }
.audit-conf { font-size: 0.72rem; color: var(--text-muted); }
.audit-json {
  margin-top: 4px; padding: 6px; background: rgba(0,0,0,0.2); border-radius: var(--radius-sm);
  font-size: 0.68rem; color: var(--text-muted); overflow-x: auto; white-space: pre-wrap;
}

.audit-empty { text-align: center; padding: 40px; }
.audit-empty p { color: var(--text-muted); margin-top: 8px; }
```

---

# Phase 13 — ASYCUDA Download + Audit Export Buttons

> **Priority:** MUST
> **Estimated Time:** 1 hour

```tsx
// frontend/src/components/ExportButtons.tsx
import React, { useState } from 'react';
import { Download, FileText, CheckCircle, Loader2 } from 'lucide-react';
import { exportAsycuda, getAuditTrail, downloadBlob } from '../utils/api';

interface Props {
  shipmentId: string;
}

export const ExportButtons: React.FC<Props> = ({ shipmentId }) => {
  const [loadingAsycuda, setLoadingAsycuda] = useState(false);
  const [loadingAudit, setLoadingAudit] = useState(false);
  const [asycudaDone, setAsycudaDone] = useState(false);
  const [auditDone, setAuditDone] = useState(false);

  const handleAsycuda = async () => {
    setLoadingAsycuda(true);
    try {
      const blob = await exportAsycuda(shipmentId);
      downloadBlob(blob, `CUSDEC_${shipmentId.slice(0, 8)}.xml`);
      setAsycudaDone(true);
      setTimeout(() => setAsycudaDone(false), 3000);
    } finally {
      setLoadingAsycuda(false);
    }
  };

  const handleAudit = async () => {
    setLoadingAudit(true);
    try {
      const data = await getAuditTrail(shipmentId);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      downloadBlob(blob, `audit_trail_${shipmentId.slice(0, 8)}.json`);
      setAuditDone(true);
      setTimeout(() => setAuditDone(false), 3000);
    } finally {
      setLoadingAudit(false);
    }
  };

  return (
    <div className="export-buttons">
      <h3>Export Documents</h3>
      <p className="export-desc">Download generated files for ASYCUDA import or audit purposes.</p>

      <div className="export-card glass-card" onClick={handleAsycuda}>
        <div className="export-icon"><Download size={24} color="var(--accent-primary)" /></div>
        <div className="export-info">
          <strong>ASYCUDA Declaration File</strong>
          <span>XML format compatible with ASYCUDA World</span>
        </div>
        <div className="export-action">
          {loadingAsycuda ? <Loader2 size={18} className="spin" /> :
           asycudaDone ? <CheckCircle size={18} color="var(--conf-high)" /> :
           <Download size={18} color="var(--text-muted)" />}
        </div>
      </div>

      <div className="export-card glass-card" onClick={handleAudit}>
        <div className="export-icon"><FileText size={24} color="var(--accent-secondary)" /></div>
        <div className="export-info">
          <strong>Audit Trail Report</strong>
          <span>Complete AI decision log in JSON format</span>
        </div>
        <div className="export-action">
          {loadingAudit ? <Loader2 size={18} className="spin" /> :
           auditDone ? <CheckCircle size={18} color="var(--conf-high)" /> :
           <Download size={18} color="var(--text-muted)" />}
        </div>
      </div>
    </div>
  );
};
```

### CSS

```css
.export-buttons { padding: 16px; }
.export-buttons h3 { margin-bottom: 4px; }
.export-desc { color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 16px; }
.export-card {
  display: flex; align-items: center; gap: 14px;
  padding: 16px; margin-bottom: 10px; cursor: pointer;
}
.export-card:hover { transform: translateY(-1px); }
.export-icon { flex-shrink: 0; }
.export-info { flex: 1; }
.export-info strong { display: block; font-size: 0.9rem; margin-bottom: 2px; }
.export-info span { font-size: 0.78rem; color: var(--text-muted); }
.export-action { flex-shrink: 0; }
```

---

# Phase 14 — Frontend ↔ Backend API Integration

> **Priority:** MUST | **Est. Time:** 2–3 hours

Create the `useShipmentData` hook and wire all real API calls into ReviewPage. Replace all placeholders with data-driven components. Add polling for processing status.

```tsx
// frontend/src/hooks/useShipment.ts
import { useState, useEffect, useCallback } from 'react';
import { getShipmentStatus, getExtraction, getGraph, getDiscrepancies, getAuditTrail } from '../utils/api';
import type { ShipmentStatus, DocumentExtraction, GraphData, Discrepancy, AuditEntry } from '../types';

export function useShipmentData(shipmentId: string) {
  const [status, setStatus] = useState<ShipmentStatus | null>(null);
  const [extraction, setExtraction] = useState<{ documents: DocumentExtraction[] } | null>(null);
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [discrepancies, setDiscrepancies] = useState<Discrepancy[]>([]);
  const [auditTrail, setAuditTrail] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [statusRes, extRes, graphRes, discRes, auditRes] = await Promise.all([
        getShipmentStatus(shipmentId),
        getExtraction(shipmentId),
        getGraph(shipmentId),
        getDiscrepancies(shipmentId),
        getAuditTrail(shipmentId),
      ]);
      setStatus(statusRes);
      setExtraction(extRes);
      setGraph(graphRes);
      setDiscrepancies(discRes.discrepancies);
      setAuditTrail(auditRes.entries);
    } catch (err: any) {
      setError(err?.message || 'Failed to load shipment data');
    } finally {
      setLoading(false);
    }
  }, [shipmentId]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  return { status, extraction, graph, discrepancies, auditTrail, loading, error, refetch: fetchAll };
}
```

Wire into ReviewPage: replace `<Placeholder>` with `<ExtractionTable>`, `<DiscrepancyList>`, `<PdfViewer>`, `<KnowledgeGraph>`, `<ExportButtons>`. Pass data from hook.

---

# Phase 15 — UI Polish + Demo Preparation

> **Priority:** MUST | **Est. Time:** 3–4 hours

### Demo-Day Checklist

- [ ] Knowledge graph entrance animation — nodes settle smoothly
- [ ] Page transitions: fade-in on route change
- [ ] All interactive elements have hover effects
- [ ] Consistent spacing, font sizes, border radii
- [ ] No console errors or warnings
- [ ] Demo flow tested end-to-end: **Upload → Process → Review → Extraction table → Click entity → PDF highlights bbox → Switch to Graph → Click conflict node → Discrepancy panel expands → See reasoning chain → See counterfactual → Export ASYCUDA file**
- [ ] Test on actual demo display resolution
- [ ] Error boundary wrapping the app (prevents white screen crash)
- [ ] **RECORD BACKUP DEMO VIDEO** — screen capture the full flow
- [ ] Remove any "TODO", placeholder text, or lorem ipsum
- [ ] Favicon + page title set to "ClearanceX"
