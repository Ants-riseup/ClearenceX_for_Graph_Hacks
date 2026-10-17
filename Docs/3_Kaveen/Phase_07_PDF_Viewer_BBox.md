# Phase 07 — PDF Viewer with BBox Overlay (Layer 1 XAI)

> **Priority:** MUST
> **Estimated Time:** 4–5 hours
> **Dependencies:** Phase 06 (review layout), Nadija's bbox format `[x1, y1, x2, y2]`
> **Blocks:** Nothing — but this is the KEY XAI demo feature

---

## Goal

Render uploaded PDFs in the browser using `react-pdf` and overlay bounding boxes on extracted entities. Clicking an entity in the extraction table → PDF scrolls to that location and highlights the bounding box with a pulsing glow. This IS **Layer 1 XAI — Visual Attribution**.

## Why

This is the first XAI feature judges see: *"Where did this value come from?"* → click → exact PDF location highlighted. Without this, there's no source provenance — the system is a black box.

## Critical Technical Challenge

PDF.js renders pages at a specific scale. Bounding boxes from Nadija's OCR are in **original page pixel coordinates**. You must convert:

```
display_x = original_x × (canvas_width / original_page_width)
display_y = original_y × (canvas_height / original_page_height)
```

If the user zooms, `scale` changes everything — bboxes must recalculate.

## Implementation

### 7.1 PDF Viewer Component

```tsx
// frontend/src/components/PdfViewer.tsx
import React, { useState, useRef, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, FileText } from 'lucide-react';
import type { Entity, DocumentType } from '../types';
import { getDocTypeLabel, getDocTypeColor } from '../types';

// PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface DocTab {
  id: string;
  filename: string;
  type: DocumentType;
  url: string;
}

interface Props {
  documents: DocTab[];                       // All uploaded docs with URLs
  entities: Entity[];                        // All entities across all docs
  selectedEntity: Entity | null;             // Currently highlighted entity
  selectedDocId: string | null;              // Which doc tab to show
  onEntityClick?: (entity: Entity) => void;  // Callback when bbox clicked
  onDocSelect?: (docId: string) => void;     // Callback when doc tab changed
  pageWidths?: Record<string, number>;       // Original widths per doc
  pageHeights?: Record<string, number>;      // Original heights per doc
}

export const PdfViewer: React.FC<Props> = ({
  documents, entities, selectedEntity, selectedDocId,
  onEntityClick, onDocSelect,
  pageWidths = {}, pageHeights = {}
}) => {
  const [activeDocIndex, setActiveDocIndex] = useState(0);
  const [numPages, setNumPages] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [canvasSize, setCanvasSize] = useState({ width: 0, height: 0 });
  const pageRef = useRef<HTMLDivElement>(null);

  const activeDoc = documents[activeDocIndex];
  const origWidth = pageWidths[activeDoc?.id] || 595;   // A4 default
  const origHeight = pageHeights[activeDoc?.id] || 842;

  // Entities for the active document + current page
  const visibleEntities = entities.filter(
    e => e.page === currentPage
    // TODO: also filter by document_id when that field is available
  );

  // Scale factors
  const scaleX = canvasSize.width / origWidth;
  const scaleY = canvasSize.height / origHeight;

  // Navigate to selected entity's page when it changes
  useEffect(() => {
    if (selectedEntity) {
      setCurrentPage(selectedEntity.page);
      // Also switch doc tab if entity is from a different doc
      // (requires entity.document_id field)
    }
  }, [selectedEntity]);

  // Switch doc tab when selectedDocId changes
  useEffect(() => {
    if (selectedDocId) {
      const idx = documents.findIndex(d => d.id === selectedDocId);
      if (idx >= 0) {
        setActiveDocIndex(idx);
        setCurrentPage(1);
      }
    }
  }, [selectedDocId, documents]);

  const handlePageRender = () => {
    if (pageRef.current) {
      const canvas = pageRef.current.querySelector('canvas');
      if (canvas) {
        setCanvasSize({ width: canvas.clientWidth, height: canvas.clientHeight });
      }
    }
  };

  return (
    <div className="pdf-viewer">
      {/* Document tabs */}
      {documents.length > 1 && (
        <div className="pdf-doc-tabs">
          {documents.map((doc, idx) => (
            <button
              key={doc.id}
              className={`pdf-doc-tab ${idx === activeDocIndex ? 'active' : ''}`}
              onClick={() => { setActiveDocIndex(idx); setCurrentPage(1); onDocSelect?.(doc.id); }}
              style={{ '--doc-color': getDocTypeColor(doc.type) } as React.CSSProperties}
            >
              <FileText size={14} />
              <span>{doc.filename.length > 20 ? doc.filename.slice(0, 17) + '...' : doc.filename}</span>
            </button>
          ))}
        </div>
      )}

      {/* Page controls */}
      <div className="pdf-controls">
        <div className="pdf-nav">
          <button className="btn btn-secondary btn-sm" onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage <= 1}>
            <ChevronLeft size={14} />
          </button>
          <span className="pdf-page-info mono">
            {currentPage} / {numPages || '–'}
          </span>
          <button className="btn btn-secondary btn-sm" onClick={() => setCurrentPage(p => Math.min(numPages, p + 1))} disabled={currentPage >= numPages}>
            <ChevronRight size={14} />
          </button>
        </div>
        <div className="pdf-zoom">
          <button className="btn btn-secondary btn-sm" onClick={() => setScale(s => Math.max(0.5, +(s - 0.15).toFixed(2)))}>
            <ZoomOut size={14} />
          </button>
          <span className="mono">{Math.round(scale * 100)}%</span>
          <button className="btn btn-secondary btn-sm" onClick={() => setScale(s => Math.min(2.5, +(s + 0.15).toFixed(2)))}>
            <ZoomIn size={14} />
          </button>
        </div>
      </div>

      {/* PDF Canvas + BBox Overlay */}
      <div className="pdf-scroll-area">
        <div className="pdf-page-wrapper" ref={pageRef}>
          {activeDoc && (
            <Document
              file={activeDoc.url}
              onLoadSuccess={({ numPages: n }) => setNumPages(n)}
              loading={<div className="pdf-loading">Loading PDF...</div>}
            >
              <Page
                pageNumber={currentPage}
                scale={scale}
                onRenderSuccess={handlePageRender}
                renderTextLayer={false}
                renderAnnotationLayer={false}
              />
            </Document>
          )}

          {/* ── Bounding Box Overlays ── */}
          {canvasSize.width > 0 && visibleEntities.map((entity, idx) => {
            const [x1, y1, x2, y2] = entity.bbox;
            const isSelected =
              selectedEntity?.entity_type === entity.entity_type &&
              selectedEntity?.page === entity.page;

            const boxStyle: React.CSSProperties = {
              position: 'absolute',
              left: x1 * scaleX * scale,
              top: y1 * scaleY * scale,
              width: (x2 - x1) * scaleX * scale,
              height: (y2 - y1) * scaleY * scale,
            };

            return (
              <div
                key={`bbox-${currentPage}-${idx}`}
                className={`bbox-overlay ${isSelected ? 'bbox-selected' : ''}`}
                style={boxStyle}
                onClick={() => onEntityClick?.(entity)}
              >
                {/* Tooltip on hover */}
                <div className="bbox-tooltip">
                  <strong>{entity.entity_type.replace(/_/g, ' ')}</strong>
                  <span>{entity.value}</span>
                  <span className="mono">{Math.round(entity.extraction_confidence * 100)}%</span>
                </div>

                {/* Label on selected */}
                {isSelected && (
                  <div className="bbox-label">
                    {entity.entity_type.replace(/_/g, ' ')}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
```

### 7.2 PDF Viewer CSS

```css
/* ============================================ */
/*  PDF VIEWER                                  */
/* ============================================ */
.pdf-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.pdf-doc-tabs {
  display: flex;
  gap: 2px;
  padding: 6px 8px;
  border-bottom: 1px solid var(--border-subtle);
  overflow-x: auto;
  flex-shrink: 0;
}

.pdf-doc-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: none;
  border: none;
  border-left: 3px solid transparent;
  color: var(--text-muted);
  font-family: inherit;
  font-size: 0.78rem;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}
.pdf-doc-tab:hover { background: var(--bg-card); color: var(--text-secondary); }
.pdf-doc-tab.active {
  background: var(--bg-card);
  color: var(--text-primary);
  border-left-color: var(--doc-color, var(--accent-primary));
}

.pdf-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.pdf-nav, .pdf-zoom {
  display: flex;
  align-items: center;
  gap: 6px;
}

.pdf-page-info {
  font-size: 0.8rem;
  color: var(--text-secondary);
  min-width: 60px;
  text-align: center;
}

.pdf-scroll-area {
  flex: 1;
  overflow: auto;
  background: rgba(0, 0, 0, 0.3);
}

.pdf-page-wrapper {
  position: relative;
  display: inline-block;
  margin: 16px auto;
}

.pdf-loading {
  padding: 40px;
  text-align: center;
  color: var(--text-muted);
}

/* ── Bounding Boxes ── */
.bbox-overlay {
  position: absolute;
  border: 2px solid rgba(99, 102, 241, 0.45);
  background: rgba(99, 102, 241, 0.06);
  cursor: pointer;
  transition: all 150ms ease;
  z-index: 10;
}

.bbox-overlay:hover {
  border-color: var(--accent-primary);
  background: rgba(99, 102, 241, 0.18);
  box-shadow: 0 0 10px var(--accent-glow);
}

.bbox-selected {
  border-color: var(--accent-primary) !important;
  background: rgba(99, 102, 241, 0.22) !important;
  box-shadow: 0 0 20px var(--accent-glow-strong) !important;
  animation: pulse-glow 2s ease-in-out infinite;
}

.bbox-tooltip {
  display: none;
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background: var(--bg-card);
  border: 1px solid var(--border-medium);
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  white-space: nowrap;
  font-size: 0.75rem;
  box-shadow: var(--shadow-md);
  z-index: 20;
}
.bbox-tooltip strong { display: block; color: var(--accent-primary); text-transform: uppercase; font-size: 0.65rem; letter-spacing: 0.05em; margin-bottom: 2px; }
.bbox-tooltip span { display: block; color: var(--text-primary); }

.bbox-overlay:hover .bbox-tooltip { display: block; }

.bbox-label {
  position: absolute;
  top: -22px;
  left: 0;
  background: var(--accent-primary);
  color: white;
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 0.65rem;
  font-weight: 700;
  white-space: nowrap;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  pointer-events: none;
}
```

## Acceptance Criteria

- [ ] PDFs render correctly in the browser via `react-pdf`
- [ ] Multi-document tabs switch between uploaded PDFs
- [ ] Page navigation (prev/next) works
- [ ] Zoom in/out works and bboxes rescale correctly
- [ ] Bounding boxes overlay at correct positions on the PDF
- [ ] Hovering a bbox shows tooltip with entity type, value, confidence
- [ ] Clicking a bbox calls `onEntityClick`
- [ ] Selected entity bbox pulses with glow animation
- [ ] When `selectedEntity` changes, PDF navigates to that entity's page
- [ ] When `selectedDocId` changes, PDF switches to that document tab
- [ ] Multiple entities per page display simultaneously without overlap issues

## Outputs

- `src/components/PdfViewer.tsx` — full PDF viewer with bbox overlay
- PDF viewer CSS in `index.css`
- Layer 1 XAI (Visual Attribution) complete
