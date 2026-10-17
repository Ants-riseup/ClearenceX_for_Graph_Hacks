"""Immutable FalkorDB snapshots. No SQL/NetworkX fallback for context tools."""
import json
import os
import re
from pathlib import Path
from falkordb import FalkorDB
from fastapi import HTTPException
from reasoning.entity_resolution import resolve_documents, apply_manual_resolutions

QUERIES = Path(__file__).parent / "queries"
LABELS = {"Shipment", "Document", "Assertion", "CanonicalField", "Decision", "Memory", "ReviewTask", "RuleEvaluation", "Rule"}
EDGES = {"HAS_DOCUMENT", "HAS_FIELD", "CONTAINS", "ASSERTS_VALUE_FOR", "DEPENDS_ON", "ABOUT", "BASED_ON", "RESOLVES", "DERIVED_FROM", "EVALUATES", "USES_RULE", "SUPPORTED_BY"}


def fields(state, shipment_id, reviewed=True):
    result = resolve_documents(shipment_id, state.get("documents", []))
    if reviewed:
        resolutions = {d["field_id"]: {"resolved_value": d["value"], "source_assertion_id": d["assertion_id"],
            "reason": d["reason"], "resolved_by": d["actor_id"]} for d in state.get("decisions", [])
            if d["status"] == "approved" and d["validity_state"] == "current"}
        result = apply_manual_resolutions(result, resolutions)
    return result


def all_assertions(state, shipment_id):
    result = []
    for doc in state.get("documents", []) + state.get("archived_documents", []):
        for field in resolve_documents(shipment_id, [doc]):
            result.extend(field["assertions"])
    return result


class GraphRepository:
    def __init__(self, tenant_id):
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", tenant_id):
            raise ValueError("Invalid trusted tenant identifier")
        self.client = FalkorDB(host=os.getenv("FALKORDB_HOST", "localhost"),
            port=int(os.getenv("FALKORDB_PORT", "6379")),
            password=os.getenv("FALKORDB_PASSWORD"),
            socket_connect_timeout=3, socket_timeout=6,
            ssl=os.getenv("FALKORDB_TLS", "false").lower() == "true")
        self.graph = self.client.select_graph("clearancex_" + tenant_id)

    def query(self, name, shipment_id, revision, **params):
        try:
            return self.graph.ro_query((QUERIES / f"{name}.cypher").read_text(),
                params={"shipment_id": shipment_id, "revision": revision, **params}, timeout=3000).result_set
        except Exception as exc:
            raise HTTPException(503, "Graph context is unavailable. Retry after synchronization.") from exc

    def project(self, row):
        sid, rev, state = row.id, row.revision, row.state
        node_batches, edge_batches = {}, {}
        def key(node_id):
            return f"{sid}:{rev}:{node_id}"
        def node(label, node_id, payload):
            assert label in LABELS
            safe = {"id": node_id, "key": key(node_id), "shipment_id": sid, "revision": rev,
                "payload": json.dumps(payload, allow_nan=False), "status": str(payload.get("status", "")),
                "field_id": str(payload.get("canonical_field_id", payload.get("field_id", ""))),
                "active": bool(payload.get("active", True))}
            node_batches.setdefault(label, []).append({"key": key(node_id), "properties": safe})
        def edge(left, right, relation):
            assert relation in EDGES
            edge_batches.setdefault(relation, []).append({"left": key(left), "right": key(right)})

        node("Shipment", sid, {"id": sid, "title": row.title})
        active_doc_ids = {d["document_id"] for d in state.get("documents", [])}
        for doc in state.get("documents", []) + state.get("archived_documents", []):
            # Never copy internal paths or document bytes into agent context.
            payload = {k: v for k, v in doc.items() if k not in {"file_path", "raw_ocr", "entities"}}
            payload["active"] = doc["document_id"] in active_doc_ids
            node("Document", doc["document_id"], payload)
            edge(sid, doc["document_id"], "HAS_DOCUMENT")
        for field in fields(state, sid):
            node("CanonicalField", field["canonical_field_id"], {k: v for k, v in field.items() if k != "assertions"})
            edge(sid, field["canonical_field_id"], "HAS_FIELD")
        for assertion in all_assertions(state, sid):
            assertion["active"] = assertion["document_id"] in active_doc_ids
            node("Assertion", assertion["assertion_id"], assertion)
            edge(assertion["document_id"], assertion["assertion_id"], "CONTAINS")
            edge(assertion["assertion_id"], assertion["document_id"], "DEPENDS_ON")
            edge(assertion["assertion_id"], assertion["canonical_field_id"], "ASSERTS_VALUE_FOR")
        for field in fields(state, sid, reviewed=False):
            rid, eid = "comparison-v1", f"evaluation:{field['canonical_field_id']}"
            node("Rule", rid, {"id": rid, "description": "Prototype exact/0.01 absolute numeric comparison; unit mismatch needs review.", "authority_status": "prototype"})
            node("RuleEvaluation", eid, {"id": eid, "field_id": field["canonical_field_id"], "status": field["status"]})
            edge(eid, field["canonical_field_id"], "EVALUATES")
            edge(eid, rid, "USES_RULE")
            for a in field["assertions"]:
                edge(eid, a["assertion_id"], "SUPPORTED_BY")
        for task in state.get("tasks", []):
            node("ReviewTask", task["id"], task)
            edge(task["id"], task["field_id"], "ABOUT")
            for aid in task["evidence_ids"]:
                edge(task["id"], aid, "DEPENDS_ON")
        for d in state.get("decisions", []):
            node("Decision", d["id"], d)
            edge(d["id"], d["assertion_id"], "DEPENDS_ON")
            edge(d["id"], d["assertion_id"], "BASED_ON")
            if d.get("task_id"):
                edge(d["id"], d["task_id"], "RESOLVES")
            memory = {"id": "memory:" + d["id"], "status": "active" if d["validity_state"] == "current" and d["status"] == "approved" else "stale",
                "field_id": d["field_id"], "summary": d["reason"], "decision_id": d["id"], "value": d["value"], "expires_at": d["decided_at"] + 30 * 86400}
            node("Memory", memory["id"], memory)
            edge(memory["id"], d["id"], "DEPENDS_ON")
            edge(memory["id"], d["id"], "DERIVED_FROM")
        for label, rows in node_batches.items():
            self.graph.query(f"UNWIND $rows AS row MERGE (n:{label} {{key:row.key}}) SET n += row.properties",
                params={"rows": rows}, timeout=5000)
        for relation, rows in edge_batches.items():
            self.graph.query(f"UNWIND $rows AS row MATCH (a {{key:row.left}}), (b {{key:row.right}}) MERGE (a)-[:{relation}]->(b)",
                params={"rows": rows}, timeout=5000)

    def evidence(self, sid, rev, field_id):
        return [json.loads(r[0]) for r in self.query("evidence", sid, rev, field_id=field_id)]

    def issues(self, sid, rev):
        return [json.loads(r[0]) for r in self.query("issues", sid, rev)]

    def memory(self, sid, rev, now):
        return [m for r in self.query("memory", sid, rev) if (m := json.loads(r[0]))["expires_at"] > now]

    def impact(self, sid, rev, source_id):
        rows = self.query("impact", sid, rev, source_id=source_id)
        if len(rows) > 100:
            raise HTTPException(409, "Change impact exceeds the review budget; no partial invalidation was applied.")
        return [{"id": r[0], "type": r[1]} for r in rows]
