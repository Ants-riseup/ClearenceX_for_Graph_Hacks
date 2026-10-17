# Phase 10 — Discrepancy List Panel

> **Priority:** MUST
> **Estimated Time:** 2–3 hours
> **Dependencies:** Phase 06 (left pane slot), Phase 11 (ConfidenceBadge)
> **Blocks:** Nothing — integrates Aloka's ReasoningChainPanel + CounterfactualCards

---

## Goal

Build an expandable list of detected discrepancies. Each item shows severity, field, and summary. Expanding reveals the full XAI breakdown: reasoning chain steps, decomposed confidence, counterfactual suggestions, and source links.

## Why

This is where all XAI layers come together for the user. A single discrepancy card contains Layer 2 (reasoning), Layer 3 (confidence), and Layer 4 (counterfactuals). The judge can click one discrepancy and see the complete AI decision pathway.

## Implementation

```tsx
// frontend/src/components/DiscrepancyList.tsx
import React, { useState } from 'react';
import {
  AlertTriangle, ChevronDown, ChevronRight, MapPin,
  Lightbulb, Link2, CheckCircle
} from 'lucide-react';
import { ConfidenceBadge } from './ConfidenceBadge';
import type { Discrepancy, DiscrepancySource, Entity } from '../types';
import { getSeverityColor, getDocTypeLabel } from '../types';

interface Props {
  discrepancies: Discrepancy[];
  onSourceClick?: (source: DiscrepancySource) => void; // Highlight in PDF
}

export const DiscrepancyList: React.FC<Props> = ({ discrepancies, onSourceClick }) => {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const toggle = (id: string) => {
    setExpandedIds(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  if (discrepancies.length === 0) {
    return (
      <div className="disc-empty">
        <CheckCircle size={32} color="var(--conf-high)" />
        <p>No discrepancies detected</p>
        <span>All values match across documents</span>
      </div>
    );
  }

  return (
    <div className="discrepancy-list">
      <div className="disc-summary">
        <AlertTriangle size={16} color="var(--sev-medium)" />
        <span>{discrepancies.length} discrepanc{discrepancies.length === 1 ? 'y' : 'ies'} detected</span>
      </div>

      {discrepancies.map(disc => {
        const isExpanded = expandedIds.has(disc.discrepancy_id);
        const sevColor = getSeverityColor(disc.severity);

        return (
          <div
            key={disc.discrepancy_id}
            className={`disc-item glass-card ${isExpanded ? 'disc-item-expanded' : ''}`}
            style={{ '--sev-color': sevColor } as React.CSSProperties}
          >
            {/* ── Header (always visible) ── */}
            <button className="disc-header" onClick={() => toggle(disc.discrepancy_id)}>
              <span className="disc-chevron">
                {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              </span>
              <span className={`badge badge-${disc.severity}`}>
                {disc.severity.toUpperCase()}
              </span>
              <span className="disc-field">{disc.field.replace(/_/g, ' ')}</span>
              <ConfidenceBadge overall={disc.confidence.overall} />
            </button>

            {/* ── Expanded content ── */}
            {isExpanded && (
              <div className="disc-body animate-fade-in">

                {/* Sources */}
                <div className="disc-section">
                  <h4><Link2 size={14} /> Sources</h4>
                  <div className="disc-sources">
                    {disc.sources.map((src, i) => (
                      <button
                        key={i}
                        className="source-chip"
                        onClick={() => onSourceClick?.(src)}
                        title="Click to highlight in PDF"
                      >
                        <span className="source-doc">{getDocTypeLabel(src.document_type as any)}</span>
                        <span className="source-value mono">{src.value}</span>
                        <MapPin size={12} />
                      </button>
                    ))}
                  </div>
                </div>

                {/* Layer 2: Reasoning Chain */}
                {disc.reasoning_chain && (
                  <div className="disc-section">
                    <h4>🔗 Reasoning Chain</h4>
                    <div className="reasoning-steps">
                      {disc.reasoning_chain.steps.map((step, i) => {
                        const isPass = step.includes('✓') || step.includes('MATCH');
                        const isFail = step.includes('⚠') || step.includes('VARIANCE') || step.includes('INCONSISTENCY');
                        return (
                          <div
                            key={i}
                            className={`reasoning-step ${isPass ? 'step-pass' : isFail ? 'step-fail' : ''}`}
                          >
                            <span className="step-num">{i + 1}</span>
                            <span className="step-text">{step}</span>
                          </div>
                        );
                      })}
                      <div className="reasoning-conclusion">
                        <strong>Conclusion:</strong> {disc.reasoning_chain.conclusion}
                      </div>
                    </div>
                  </div>
                )}

                {/* Layer 3: Confidence Breakdown */}
                <div className="disc-section">
                  <h4>📊 Confidence Breakdown</h4>
                  <div className="confidence-breakdown-full">
                    <div className="conf-bar-row">
                      <span>Extraction</span>
                      <div className="conf-bar"><div className="conf-bar-fill" style={{ width: `${disc.confidence.extraction * 100}%`, background: 'var(--conf-high)' }} /></div>
                      <span className="mono">{Math.round(disc.confidence.extraction * 100)}%</span>
                    </div>
                    <div className="conf-bar-row">
                      <span>Classification</span>
                      <div className="conf-bar"><div className="conf-bar-fill" style={{ width: `${disc.confidence.classification * 100}%`, background: 'var(--conf-high)' }} /></div>
                      <span className="mono">{Math.round(disc.confidence.classification * 100)}%</span>
                    </div>
                    <div className="conf-bar-row">
                      <span>Matching</span>
                      <div className="conf-bar"><div className="conf-bar-fill" style={{ width: `${disc.confidence.matching * 100}%`, background: disc.confidence.matching >= 0.7 ? 'var(--conf-medium)' : 'var(--conf-low)' }} /></div>
                      <span className="mono">{Math.round(disc.confidence.matching * 100)}%</span>
                    </div>
                  </div>
                </div>

                {/* Layer 4: Counterfactuals */}
                {disc.counterfactual && (
                  <div className="disc-section">
                    <h4><Lightbulb size={14} /> What Would Resolve This?</h4>
                    <div className="cf-options">
                      {disc.counterfactual.options.map((opt, i) => (
                        <div key={i} className="cf-option">
                          <span className="cf-arrow">→</span>
                          <span>{opt}</span>
                        </div>
                      ))}
                    </div>
                    <div className="cf-recommendation">
                      <strong>📋 Recommendation:</strong> {disc.counterfactual.recommendation}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
```

### CSS

```css
/* ============================================ */
/*  DISCREPANCY LIST                            */
/* ============================================ */
.discrepancy-list { padding: 8px; }

.disc-summary {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px; margin-bottom: 8px;
  font-size: 0.85rem; color: var(--text-secondary);
}

.disc-item {
  margin-bottom: 8px; padding: 0; overflow: hidden;
  border-left: 3px solid var(--sev-color, var(--border-subtle));
}
.disc-item-expanded { box-shadow: var(--shadow-glow); }

.disc-header {
  display: flex; align-items: center; gap: 8px; width: 100%;
  padding: 12px 14px; background: none; border: none;
  color: var(--text-primary); font-family: inherit; font-size: 0.85rem;
  cursor: pointer; transition: background var(--transition-fast);
}
.disc-header:hover { background: rgba(255, 255, 255, 0.03); }

.disc-chevron { color: var(--text-muted); flex-shrink: 0; }
.disc-field { flex: 1; text-align: left; font-weight: 600; text-transform: capitalize; }

.disc-body { padding: 0 14px 14px; }

.disc-section { margin-top: 14px; }
.disc-section h4 {
  display: flex; align-items: center; gap: 6px;
  font-size: 0.78rem; color: var(--text-secondary); text-transform: uppercase;
  letter-spacing: 0.05em; margin-bottom: 8px;
}

/* Sources */
.disc-sources { display: flex; flex-wrap: wrap; gap: 6px; }
.source-chip {
  display: flex; align-items: center; gap: 6px;
  padding: 5px 10px; background: var(--bg-elevated); border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm); font-size: 0.78rem; cursor: pointer;
  color: var(--text-primary); font-family: inherit; transition: all var(--transition-fast);
}
.source-chip:hover { border-color: var(--accent-primary); background: rgba(99, 102, 241, 0.08); }
.source-doc { color: var(--text-secondary); font-size: 0.7rem; }

/* Reasoning steps */
.reasoning-steps { display: flex; flex-direction: column; gap: 4px; }
.reasoning-step {
  display: flex; align-items: flex-start; gap: 8px;
  padding: 6px 10px; border-radius: var(--radius-sm);
  font-size: 0.8rem; background: rgba(0, 0, 0, 0.1);
}
.step-pass { border-left: 2px solid var(--conf-high); }
.step-fail { border-left: 2px solid var(--conf-low); }
.step-num {
  width: 20px; height: 20px; display: flex; align-items: center; justify-content: center;
  background: var(--bg-elevated); border-radius: 50%; font-size: 0.7rem;
  color: var(--text-muted); flex-shrink: 0; font-weight: 600;
}
.step-text { color: var(--text-primary); line-height: 1.4; }
.reasoning-conclusion {
  margin-top: 8px; padding: 8px 10px; background: rgba(99, 102, 241, 0.06);
  border-radius: var(--radius-sm); font-size: 0.82rem; color: var(--text-primary);
}

/* Confidence bars */
.confidence-breakdown-full { display: flex; flex-direction: column; gap: 6px; }
.conf-bar-row { display: flex; align-items: center; gap: 8px; font-size: 0.78rem; color: var(--text-secondary); }
.conf-bar-row span:first-child { width: 90px; }
.conf-bar { flex: 1; height: 6px; background: rgba(255,255,255,0.06); border-radius: 3px; overflow: hidden; }
.conf-bar-fill { height: 100%; border-radius: 3px; transition: width 0.5s ease; }

/* Counterfactuals */
.cf-options { display: flex; flex-direction: column; gap: 4px; }
.cf-option {
  display: flex; gap: 8px; padding: 6px 10px;
  background: rgba(0, 0, 0, 0.1); border-radius: var(--radius-sm); font-size: 0.82rem;
}
.cf-arrow { color: var(--accent-primary); font-weight: 700; }
.cf-recommendation {
  margin-top: 8px; padding: 8px 10px; background: rgba(245, 158, 11, 0.06);
  border: 1px solid rgba(245, 158, 11, 0.15); border-radius: var(--radius-sm);
  font-size: 0.82rem; color: var(--text-primary);
}

.disc-empty {
  text-align: center; padding: 40px;
}
.disc-empty p { color: var(--conf-high); font-weight: 600; margin-top: 8px; }
.disc-empty span { color: var(--text-muted); font-size: 0.85rem; }
```

## Acceptance Criteria

- [ ] Lists all discrepancies with severity badges (🔴 High, 🟡 Medium, 🔵 Low)
- [ ] Expandable — click to reveal full XAI breakdown
- [ ] Layer 2: Reasoning chain steps with numbered, color-coded steps
- [ ] Layer 3: Confidence breakdown with horizontal bar charts
- [ ] Layer 4: Counterfactual suggestions with recommendation
- [ ] Source chips clickable → highlights bbox in PDF viewer
- [ ] Empty state shows "No discrepancies detected" with green checkmark
- [ ] Severity-colored left border on each item
- [ ] Expanded items get glow shadow

## Outputs

- `src/components/DiscrepancyList.tsx`
- Discrepancy list CSS in `index.css`
- Layers 2, 3, 4 XAI visualization complete
