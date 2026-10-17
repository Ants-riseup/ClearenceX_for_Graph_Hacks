# ClearanceX graph model

The primary graph database is FalkorDB. PostgreSQL stores transactional source records, session/tenant ownership, decisions, jobs and API usage. It is not used as a substitute when graph-dependent operations fail.

Each tenant gets `clearancex_<trusted tenant UUID>`. Only the authenticated backend selects that name. Every node contains shipment and snapshot revision. Keys are `shipment_id:revision:node_id`. The projector batches nodes and edges into idempotent writes and publishes `graph_revision` only after a complete snapshot. Readers lock/check the same PostgreSQL dossier row; a failed projection leaves context pending.

## Nodes and relationships

```text
Shipment -HAS_DOCUMENT-> Document -CONTAINS-> Assertion
Shipment -HAS_FIELD-> CanonicalField <-ASSERTS_VALUE_FOR- Assertion
RuleEvaluation -EVALUATES-> CanonicalField
RuleEvaluation -USES_RULE-> Rule
RuleEvaluation -SUPPORTED_BY-> Assertion
ReviewTask -ABOUT-> CanonicalField
ReviewTask -DEPENDS_ON-> Assertion
Decision -RESOLVES-> ReviewTask
Decision -BASED_ON/DEPENDS_ON-> Assertion -DEPENDS_ON-> Document
Memory -DERIVED_FROM/DEPENDS_ON-> Decision
AgentRun -INVESTIGATED-> Shipment
AgentRun -RETRIEVED-> Assertion
AgentRun -PROPOSED-> ReviewTask
AgentRun -RECALLED-> Memory
ExportSnapshot -DEPENDS_ON-> Decision
```

Graph properties contain scalar routing/identity fields and a JSON-encoded payload string. The payload preserves raw/normalized values, units, page, source IDs, prototype rule description and decision provenance. Private filesystem paths and PDF bytes are excluded. A missing bbox is kept empty rather than invented.

## Why the graph matters

Approve a packing-list assertion and a separate invoice package count. Replacing the packing list traverses reverse `DEPENDS_ON` paths, bounded to four edges, to find derived artifacts. Only affected current decisions become stale. The approved status/time remains historical; validity is tracked separately. Stale decision memory is excluded from subsequent recall. The unrelated invoice decision remains current.

Impact retrieval must complete before the source change commits. If graph connectivity fails or more than 100 affected artifacts would be returned, the operation fails without applying partial invalidation. The outbox then projects the updated source and validity state into a new snapshot. Other graph-dependent actions remain blocked while it is pending.

Essential executed queries live in `backend/context_app/queries/`: evidence, issues, rules, memory, impact and visualization. Input values use parameters. Labels/relationship types in projection come from fixed code allowlists. No model-generated Cypher is executed.

The current prototype policy is `comparison-v2`: decimal comparison, exact integer counts, money tolerance 0.01 and a default absolute weight tolerance of 0.01. Administrators can version weight tolerance; affected approvals then require review. Mixed units need review. The same policy module drives canonical clustering and deterministic numeric checks. This is a technical prototype policy, not a customs regulation.

Nodes also carry a fixed `node_type` and `ContextNode` label. Range indexes support snapshot/identity lookup. Artifact types do not depend on `labels()` ordering. Field context includes stale decision IDs and old source IDs so an agent can discover changed-source dependencies.

## Concurrency and durability

PostgreSQL row locks serialize dossier mutations. Expected revision checks reject stale proposals/approvals. Idempotency keys avoid duplicate decisions; repeated projection uses MERGE. The durable outbox retries with backoff and retains a failed state after eight attempts. The UI can enqueue an explicit retry.

Snapshots are retained for history. Automatic compaction/retention is not implemented; monitor disk/memory and add tested retention before production workloads. Tenant graph names are logical segregation backed by API authorization, not separate database credentials. The application database/graph accounts remain powerful within their private network; this is not a hostile multi-tenant database isolation claim.
