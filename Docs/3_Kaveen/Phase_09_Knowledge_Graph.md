# Phase 09 — Knowledge Graph Visualization (vis.js)

> **Priority:** MUST
> **Estimated Time:** 4–5 hours
> **Dependencies:** Phase 06 (right pane slot), Aloka's graph API
> **Blocks:** Nothing — but this is the **"WOW moment"** for judges

---

## Goal

Render the interactive knowledge graph using `vis-network`. Document nodes connect to entity nodes through labeled edges. Conflict entities pulse red. Clicking nodes triggers cross-pane interaction.

## Why

The knowledge graph is the single most visually impressive feature. When a judge sees 5 documents connected through shared entities, with conflicts glowing red and matches glowing green — it immediately communicates the power of cross-document reconciliation. This alone can win the demo.

## Implementation

```tsx
// frontend/src/components/KnowledgeGraph.tsx
import React, { useRef, useEffect, useState } from 'react';
import { Network, Options } from 'vis-network';
import { DataSet } from 'vis-data';
import { Maximize2, RotateCcw } from 'lucide-react';
import type { GraphData, GraphNode } from '../types';

interface Props {
  data: GraphData;
  onNodeClick?: (nodeId: string, nodeType: string) => void;
  onEdgeClick?: (fromId: string, toId: string) => void;
}

export const KnowledgeGraph: React.FC<Props> = ({ data, onNodeClick, onEdgeClick }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);
  const [stabilized, setStabilized] = useState(false);

  useEffect(() => {
    if (!containerRef.current || !data || data.nodes.length === 0) return;

    // ── Build nodes ──
    const nodes = new DataSet(
      data.nodes.map((n: GraphNode) => ({
        id: n.id,
        label: n.label,
        group: n.type,

        // Shape: documents are boxes, entities are dots
        shape: n.type === 'document' ? 'box' : 'dot',

        // Size: conflicts are larger and draw attention
        size: n.status === 'conflict' ? 35 : n.type === 'document' ? 18 : 22,

        // Colors
        color: {
          background: typeof n.color === 'string' ? n.color : n.color?.background || '#888',
          border: typeof n.color === 'string' ? n.color : n.color?.border || '#888',
          highlight: {
            background: '#6366f1',
            border: '#818cf8',
          },
          hover: {
            background: typeof n.color === 'string' ? n.color : n.color?.background || '#888',
            border: '#f1f5f9',
          },
        },

        // Font
        font: {
          color: '#f1f5f9',
          size: n.type === 'document' ? 12 : 13,
          face: 'Inter, sans-serif',
          bold: n.status === 'conflict' ? { color: '#ef4444' } : undefined,
        },

        // Effects
        shadow: n.status === 'conflict',
        borderWidth: n.status === 'conflict' ? 3 : n.type === 'document' ? 1 : 2,
        borderWidthSelected: 4,

        // Tooltip
        title: n.type === 'document'
          ? `📄 ${n.label}\nType: ${n.document_type || 'unknown'}`
          : `🔍 ${n.label}\nStatus: ${n.status || 'unknown'}`,
      }))
    );

    // ── Build edges ──
    const edges = new DataSet(
      data.edges.map((e, idx) => ({
        id: `edge-${idx}`,
        from: e.from,
        to: e.to,
        label: e.label,
        width: Math.max(1.5, (e.confidence || 0.5) * 4),
        font: {
          color: '#64748b',
          size: 10,
          face: 'JetBrains Mono, monospace',
          strokeWidth: 0,
          align: 'middle',
        },
        color: {
          color: '#475569',
          highlight: '#6366f1',
          hover: '#818cf8',
        },
        smooth: {
          type: 'continuous' as const,
          roundness: 0.2,
        },
        arrows: { to: { enabled: false } },
        title: `Value: ${e.label}\nConfidence: ${Math.round((e.confidence || 0) * 100)}%`,
      }))
    );

    // ── Network options ──
    const options: Options = {
      physics: {
        enabled: true,
        barnesHut: {
          gravitationalConstant: -4500,
          springLength: 200,
          springConstant: 0.015,
          damping: 0.12,
          avoidOverlap: 0.3,
        },
        stabilization: {
          enabled: true,
          iterations: 200,
          fit: true,
        },
      },
      interaction: {
        hover: true,
        tooltipDelay: 150,
        zoomView: true,
        dragView: true,
        dragNodes: true,
        multiselect: false,
      },
      layout: {
        improvedLayout: true,
        clusterThreshold: 150,
      },
      nodes: {
        chosen: true,
      },
      edges: {
        chosen: true,
      },
    };

    // ── Create network ──
    const network = new Network(containerRef.current, { nodes, edges }, options);
    networkRef.current = network;

    // ── Events ──
    network.on('click', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0] as string;
        const node = data.nodes.find(n => n.id === nodeId);
        onNodeClick?.(nodeId, node?.type || 'unknown');
      } else if (params.edges.length > 0) {
        const edge = data.edges[parseInt(params.edges[0].toString().replace('edge-', ''))];
        if (edge) onEdgeClick?.(edge.from, edge.to);
      }
    });

    network.on('stabilized', () => {
      setStabilized(true);
      network.setOptions({ physics: { enabled: false } }); // Stop physics after stabilization
    });

    // ── Cleanup ──
    return () => {
      network.destroy();
      networkRef.current = null;
    };
  }, [data]);

  const handleFit = () => {
    networkRef.current?.fit({ animation: { duration: 500, easingFunction: 'easeInOutQuad' } });
  };

  const handleReset = () => {
    networkRef.current?.setOptions({ physics: { enabled: true } });
    setTimeout(() => {
      networkRef.current?.stabilize(100);
    }, 100);
  };

  return (
    <div className="knowledge-graph-wrapper">
      {/* Controls */}
      <div className="graph-controls">
        <button className="btn btn-secondary btn-sm" onClick={handleFit} title="Fit to view">
          <Maximize2 size={14} />
        </button>
        <button className="btn btn-secondary btn-sm" onClick={handleReset} title="Re-layout">
          <RotateCcw size={14} />
        </button>
        {!stabilized && (
          <span className="graph-status">Laying out graph...</span>
        )}
      </div>

      {/* Legend */}
      <div className="graph-legend">
        <div className="legend-item"><span className="legend-dot" style={{ background: '#4A90D9' }} /> Invoice</div>
        <div className="legend-item"><span className="legend-dot" style={{ background: '#50C878' }} /> Packing List</div>
        <div className="legend-item"><span className="legend-dot" style={{ background: '#FFB347' }} /> AWB</div>
        <div className="legend-item"><span className="legend-dot" style={{ background: '#ef4444' }} /> Conflict</div>
        <div className="legend-item"><span className="legend-dot" style={{ background: '#10b981' }} /> Match</div>
      </div>

      {/* Graph canvas */}
      <div ref={containerRef} className="knowledge-graph-container" />
    </div>
  );
};
```

### CSS

```css
/* ============================================ */
/*  KNOWLEDGE GRAPH                             */
/* ============================================ */
.knowledge-graph-wrapper {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.graph-controls {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.graph-status {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-left: 8px;
}

.graph-legend {
  position: absolute;
  bottom: 12px;
  left: 12px;
  display: flex;
  gap: 12px;
  padding: 6px 12px;
  background: rgba(10, 10, 26, 0.85);
  backdrop-filter: blur(8px);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  z-index: 10;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.7rem;
  color: var(--text-secondary);
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.knowledge-graph-container {
  flex: 1;
  min-height: 400px;
  background: radial-gradient(ellipse at center, rgba(10, 10, 26, 0.9), var(--bg-primary));
}
```

## Acceptance Criteria

- [ ] Graph renders with document nodes (boxes) and entity nodes (dots)
- [ ] Edge labels show extracted values with confidence-based thickness
- [ ] Conflict entity nodes are LARGER and have RED glow/shadow
- [ ] Match entity nodes are green, warnings are yellow
- [ ] Clicking a node calls `onNodeClick` with ID and type
- [ ] Physics stabilizes then disables (no jittering after load)
- [ ] Fit-to-view and re-layout buttons work
- [ ] Legend shows color meanings
- [ ] Hover shows tooltips with details
- [ ] Drag nodes to rearrange, zoom with scroll wheel
- [ ] Graph entrance animation is smooth (nodes settle into position)

## Outputs

- `src/components/KnowledgeGraph.tsx`
- Knowledge graph CSS in `index.css`
- Layer 6 XAI (Knowledge Graph Visualization) complete
