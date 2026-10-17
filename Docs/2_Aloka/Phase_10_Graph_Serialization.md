# Phase 10 — Layer 6: Graph Data Serialization for Frontend

> **Priority:** MUST
> **Estimated Time:** 2–3 hours
> **Dependencies:** Phase 04 (knowledge graph built)
> **Blocks:** Kaveen Phase 09 (vis.js needs this exact format)

---

## Goal

Enhance the `to_vis_json()` method in `knowledge_graph.py` to produce production-quality graph data that Kaveen's vis.js component can render directly — with correct colors, sizes, shapes, tooltips, and physics suggestions.

## Why

This is the data bridge between your backend knowledge graph (NetworkX) and Kaveen's frontend visualization (vis.js). If the node/edge format doesn't match exactly, the "wow moment" graph won't render. Get this right.

## Implementation

```python
# Enhancement to backend/reasoning/knowledge_graph.py

# Document type color mapping (matches Kaveen's design system)
DOC_TYPE_COLORS = {
    "commercial_invoice": "#4A90D9",   # Blue
    "packing_list": "#50C878",         # Green
    "awb": "#FFB347",                  # Orange
    "bl": "#DDA0DD",                   # Purple/Plum
    "freight_invoice": "#F0E68C",      # Khaki
    "delivery_order": "#87CEEB",       # Sky Blue
    "letter_of_credit": "#CD853F",     # Peru/Brown
    "unknown": "#CCCCCC",              # Gray
}

# Entity status colors
ENTITY_STATUS_COLORS = {
    "conflict": "#ef4444",    # Red
    "match": "#10b981",       # Green
    "warning": "#f59e0b",     # Yellow/Amber
    "pending": "#94a3b8",     # Gray
}

def to_vis_json(self) -> dict:
    """
    Serialize the knowledge graph to vis.js-compatible JSON.
    
    Produces format matching Kaveen's GraphData TypeScript interface:
    {
        nodes: GraphNode[],
        edges: GraphEdge[]
    }
    """
    nodes = []
    for node_id, data in self.graph.nodes(data=True):
        node_type = data.get("node_type", "unknown")
        
        if node_type == "entity":
            status = data.get("status", "pending")
            color = ENTITY_STATUS_COLORS.get(status, "#94a3b8")
            node = {
                "id": node_id,
                "label": data.get("label", node_id).replace("_", " ").title(),
                "type": "entity",
                "shape": "dot",
                "status": status,
                "color": {"background": color, "border": color},
                "size": 35 if status == "conflict" else 22,
                "font": {"color": "#f1f5f9"},
                "shadow": status == "conflict",  # Glow effect for conflicts
            }
        else:
            # Document node
            doc_type = data.get("document_type", "unknown")
            color = DOC_TYPE_COLORS.get(doc_type, "#CCCCCC")
            node = {
                "id": node_id,
                "label": data.get("label", doc_type.replace("_", " ").title()),
                "type": "document",
                "shape": "box",
                "document_type": doc_type,
                "color": {"background": color, "border": color},
                "size": 18,
                "font": {"color": "#f1f5f9"},
                "shadow": False,
            }
        
        nodes.append(node)
    
    edges = []
    for u, v, data in self.graph.edges(data=True):
        conf = data.get("confidence", 0.5)
        edges.append({
            "from": u,
            "to": v,
            "label": str(data.get("value", "")),
            "confidence": conf,
            "width": max(1, int(conf * 5)),    # Thicker = more confident
            "font": {"color": "#94a3b8", "size": 10},
            "color": {"color": "#64748b"},
        })
    
    return {"nodes": nodes, "edges": edges}
```

## Vis.js Physics Configuration (Suggest to Kaveen)

Include this in the graph data or documentation for Kaveen:

```python
# Recommended vis.js options for Kaveen's KnowledgeGraph component
RECOMMENDED_VIS_OPTIONS = {
    "physics": {
        "barnesHut": {
            "gravitationalConstant": -4000,
            "springLength": 200,
            "springConstant": 0.015,
            "damping": 0.12,
            "avoidOverlap": 0.3
        },
        "stabilization": {
            "iterations": 200,
            "fit": True
        }
    },
    "interaction": {
        "hover": True,
        "tooltipDelay": 150
    }
}
```

## Output Format

Must match Kaveen's `GraphData` TypeScript interface exactly:

```json
{
  "nodes": [
    {
      "id": "doc_001",
      "label": "Commercial Invoice",
      "type": "document",
      "shape": "box",
      "document_type": "commercial_invoice",
      "color": {"background": "#4A90D9", "border": "#4A90D9"},
      "size": 18,
      "font": {"color": "#f1f5f9"},
      "shadow": false
    },
    {
      "id": "GROSS_WEIGHT",
      "label": "Gross Weight",
      "type": "entity",
      "shape": "dot",
      "status": "conflict",
      "color": {"background": "#ef4444", "border": "#ef4444"},
      "size": 35,
      "font": {"color": "#f1f5f9"},
      "shadow": true
    }
  ],
  "edges": [
    {
      "from": "doc_001",
      "to": "GROSS_WEIGHT",
      "label": "450.00 kg",
      "confidence": 0.94,
      "width": 4,
      "font": {"color": "#94a3b8", "size": 10},
      "color": {"color": "#64748b"}
    }
  ]
}
```

## Acceptance Criteria

- [ ] Document nodes are boxes with doc-type-specific colors
- [ ] Entity nodes are dots with status-specific colors (red=conflict, green=match, yellow=warning)
- [ ] Conflict nodes are larger (35) with shadow enabled (pulsing glow in Kaveen's CSS)
- [ ] Edge widths scale with confidence
- [ ] Edge labels show extracted values
- [ ] Font color is `#f1f5f9` (matches dark theme)
- [ ] Output matches Kaveen's `GraphNode` and `GraphEdge` TypeScript interfaces
- [ ] Color mapping matches Kaveen's `getDocTypeColor()` function

## Outputs

- Enhanced `to_vis_json()` in `backend/reasoning/knowledge_graph.py`
