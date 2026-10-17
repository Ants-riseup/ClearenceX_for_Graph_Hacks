# Phase 08 — Extraction Data Table

> **Priority:** MUST
> **Estimated Time:** 2–3 hours
> **Dependencies:** Phase 06 (left pane slot), Phase 11 (ConfidenceBadge)
> **Blocks:** Nothing — but critical for demo flow

---

## Goal

Build a table component that displays all extracted entities, grouped by source document. Each row is clickable to highlight the corresponding bounding box in the PDF viewer.

## Why

This is how the user reads extraction results — the left-pane primary view. Grouped by document type, with confidence badges and click-to-locate functionality, it ties directly to Layer 1 XAI.

## Implementation

```tsx
// frontend/src/components/ExtractionTable.tsx
import React, { useState } from 'react';
import { ChevronDown, ChevronRight, FileText, MapPin } from 'lucide-react';
import { ConfidenceBadge } from './ConfidenceBadge';
import type { Entity, DocumentExtraction, DocumentType } from '../types';
import { getDocTypeLabel, getDocTypeColor, getConfidenceLevel } from '../types';

interface Props {
  documents: DocumentExtraction[];
  selectedEntity: Entity | null;
  onEntitySelect: (entity: Entity) => void;
}

export const ExtractionTable: React.FC<Props> = ({
  documents, selectedEntity, onEntitySelect
}) => {
  const [expandedDocs, setExpandedDocs] = useState<Set<string>>(
    new Set(documents.map(d => d.document_id)) // All expanded by default
  );

  const toggleDoc = (docId: string) => {
    setExpandedDocs(prev => {
      const next = new Set(prev);
      next.has(docId) ? next.delete(docId) : next.add(docId);
      return next;
    });
  };

  const isSelected = (entity: Entity) =>
    selectedEntity?.entity_type === entity.entity_type &&
    selectedEntity?.page === entity.page &&
    selectedEntity?.value === entity.value;

  return (
    <div className="extraction-table">
      {documents.map(doc => (
        <div key={doc.document_id} className="extraction-group">
          {/* Document header */}
          <button
            className="extraction-group-header"
            onClick={() => toggleDoc(doc.document_id)}
          >
            <span className="group-chevron">
              {expandedDocs.has(doc.document_id) ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </span>
            <span
              className="group-dot"
              style={{ backgroundColor: getDocTypeColor(doc.document_type) }}
            />
            <span className="group-label">{getDocTypeLabel(doc.document_type)}</span>
            <span className="group-count">{doc.entities.length} fields</span>
            <ConfidenceBadge overall={doc.classification_confidence} />
          </button>

          {/* Entity rows */}
          {expandedDocs.has(doc.document_id) && (
            <div className="extraction-rows">
              {doc.entities.map((entity, idx) => {
                const confLevel = getConfidenceLevel(entity.extraction_confidence);
                return (
                  <div
                    key={`${doc.document_id}-${entity.entity_type}-${idx}`}
                    className={`extraction-row ${isSelected(entity) ? 'extraction-row-selected' : ''}`}
                    onClick={() => onEntitySelect(entity)}
                    style={{ '--conf-border': `var(--conf-${confLevel})` } as React.CSSProperties}
                  >
                    <div className="row-main">
                      <span className="entity-type">
                        {entity.entity_type.replace(/_/g, ' ')}
                      </span>
                      <span className="entity-value mono">
                        {entity.value}
                      </span>
                    </div>
                    <div className="row-meta">
                      <span className="entity-page" title="Page number">
                        <MapPin size={12} /> pg.{entity.page}
                      </span>
                      <ConfidenceBadge
                        overall={entity.extraction_confidence}
                        extraction={entity.extraction_confidence}
                        classification={entity.classification_confidence}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ))}

      {documents.length === 0 && (
        <div className="extraction-empty">
          <FileText size={32} color="var(--text-muted)" />
          <p>No extractions available</p>
        </div>
      )}
    </div>
  );
};
```

### CSS

```css
/* ============================================ */
/*  EXTRACTION TABLE                            */
/* ============================================ */
.extraction-table {
  padding: 8px;
}

.extraction-group {
  margin-bottom: 4px;
}

.extraction-group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.15);
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-family: inherit;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition-fast);
}
.extraction-group-header:hover { background: rgba(0, 0, 0, 0.25); }

.group-chevron { color: var(--text-muted); flex-shrink: 0; }
.group-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.group-label { flex: 1; text-align: left; }
.group-count { font-size: 0.75rem; color: var(--text-muted); font-weight: 400; }

.extraction-rows {
  padding: 4px 0 4px 20px;
}

.extraction-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  margin: 2px 0;
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--conf-border, var(--border-subtle));
  cursor: pointer;
  transition: all var(--transition-fast);
}
.extraction-row:hover {
  background: var(--bg-card-hover);
}
.extraction-row-selected {
  background: rgba(99, 102, 241, 0.1) !important;
  border-left-color: var(--accent-primary) !important;
}

.row-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.entity-type {
  font-size: 0.7rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 600;
}

.entity-value {
  font-size: 0.9rem;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.row-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.entity-page {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 0.7rem;
  color: var(--text-muted);
}

.extraction-empty {
  text-align: center;
  padding: 40px 20px;
}
.extraction-empty p {
  color: var(--text-muted);
  margin-top: 8px;
}
```

## Acceptance Criteria

- [ ] Entities grouped by document type with collapsible sections
- [ ] Each row shows: entity type (label), value (mono font), page, confidence badge
- [ ] Clicking a row calls `onEntitySelect` → highlights bbox in PDF
- [ ] Selected row has accent background + border
- [ ] Color-coded left border: green (≥90%), yellow (70–89%), red (<70%)
- [ ] All sections expanded by default
- [ ] Empty state when no documents/entities
- [ ] Smooth expand/collapse transitions

## Outputs

- `src/components/ExtractionTable.tsx`
- Extraction table CSS in `index.css`
