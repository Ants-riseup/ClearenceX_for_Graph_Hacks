"""Optional stdio MCP adapter; forwards only narrow tools through normal API auth."""
import os
import uuid
from urllib.parse import urlparse
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ClearanceX context")


def call(method, path, **kwargs):
    base = os.getenv("CLEARANCEX_MCP_API", "http://127.0.0.1:8000").rstrip("/")
    parsed = urlparse(base)
    if parsed.hostname not in {"localhost", "127.0.0.1"} or parsed.scheme != "http" or parsed.path:
        raise ValueError("This local MCP adapter accepts only a loopback API origin.")
    token = os.getenv("CLEARANCEX_MCP_SESSION", "")
    if not token:
        raise ValueError("Set a valid user session in CLEARANCEX_MCP_SESSION; never expose it as a tool argument.")
    with httpx.Client(base_url=base, timeout=10, follow_redirects=False) as client:
        client.cookies.set("clearancex_dev_session", token)
        if method != "GET":
            csrf = client.get("/api/auth/csrf")
            csrf.raise_for_status()
            client.headers["X-CSRF-Token"] = csrf.json()["csrf_token"]
            client.headers["Origin"] = os.getenv("CLEARANCEX_MCP_ORIGIN", "http://localhost:8080")
        result = client.request(method, path, **kwargs)
        if result.is_error:
            detail = result.json().get("detail", "Context request denied.")
            raise ValueError(detail if isinstance(detail, str) else "Context request denied.")
        return result.json()


def root(shipment_id):
    return f"/api/shipments/{uuid.UUID(shipment_id)}"


@mcp.tool()
def list_dossier_issues(shipment_id: str) -> dict:
    """Read graph-derived fields within the signed-in user's tenant."""
    return call("GET", root(shipment_id) + "/context-issues")


@mcp.tool()
def get_field_evidence(shipment_id: str, field_id: str) -> dict:
    """Read source assertions with citation IDs, values and pages."""
    return call("GET", root(shipment_id) + "/context-evidence", params={"field_id": field_id})


@mcp.tool()
def get_rule_explanation(shipment_id: str, field_id: str) -> dict:
    """Read the prototype rule and its graph evaluation."""
    return call("GET", root(shipment_id) + "/context-rules", params={"field_id": field_id})


@mcp.tool()
def recall_approved_decisions(shipment_id: str) -> dict:
    """Recall active approved memory; stale memory is excluded."""
    return call("GET", root(shipment_id) + "/context-memory")


@mcp.tool()
def get_change_impact(shipment_id: str, document_id: str) -> dict:
    """Traverse dependencies of a source document revision."""
    return call("GET", root(shipment_id) + "/change-impact", params={"document_id": document_id})


@mcp.tool()
def propose_review_task(shipment_id: str, field_id: str, evidence_ids: list[str], reason: str, expected_revision: int) -> dict:
    """Create a pending proposal; this tool cannot approve decisions."""
    return call("POST", root(shipment_id) + "/review-tasks", json={"field_id": field_id,
        "evidence_ids": evidence_ids, "reason": reason, "expected_revision": expected_revision})


if __name__ == "__main__":
    mcp.run(transport="stdio")
