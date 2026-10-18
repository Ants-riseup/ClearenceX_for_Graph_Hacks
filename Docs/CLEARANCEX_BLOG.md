# When Shipment Evidence Changes, Your AI Should Change Its Mind

## Building ClearanceX with FalkorDB for Graph Hacks

*18 October 2026 · ClearanceX project team*

An invoice says a shipment weighs 450 kg. A packing list agrees. A transport document says 440 kg. A reviewer investigates, selects supporting evidence and approves a value.

Then someone uploads a corrected packing list.

The difficult question is no longer simply, “What is the weight?” It is: **Which previous decisions can we still trust?**

That question shaped our Graph Hacks work on ClearanceX, an AI-assisted document-review workspace for export teams. We use FalkorDB to connect source evidence, reviewer decisions and their dependencies, so a changed document can trigger a precise review instead of leaving an old answer looking current.

### The problem: an answer has a history

Shipment documents repeat the same facts in different formats. Values can disagree, sources can be incomplete, and a corrected PDF can arrive after someone has already reviewed the shipment.

Saving the latest extracted value does not capture why a reviewer accepted it. A useful review system also needs the supporting assertion, its document revision, the decision it justified and the later work that depended on that decision.

ClearanceX retains that provenance. Reviewers can inspect evidence, investigate discrepancies and prepare reviewed exports. Human approval remains part of the process; the prototype does not file customs declarations or verify official customs schedules.

### Turning evidence into connected context

Our graph includes shipments, document revisions, extracted assertions, canonical fields, review tasks, decisions, approved memory and export snapshots. Relationships record how those objects depend on one another.

```text
Document ← Assertion ← Decision ← Approved memory
                           ↑
                      Export snapshot

Arrows here mean “depends on.”
```

FalkorDB gives the agent a way to retrieve the relationships relevant to a question. The graph can connect a decision back to its supporting assertion and source revision, or follow dependency paths to identify artifacts affected by a correction.

The [graph model](https://github.com/Ants-riseup/ClearenceX_for_Graph_Hacks/blob/main/Docs/GRAPH_MODEL.md) and [executed Cypher queries](https://github.com/Ants-riseup/ClearenceX_for_Graph_Hacks/tree/main/backend/context_app/queries) are available in the repository.

### The key behavior: selective invalidation

Consider two approvals in one dossier: a gross-weight decision supported by the packing list, and a package-count decision supported by the invoice.

When the packing list is replaced, ClearanceX queries FalkorDB for dependent artifacts before committing the correction. The traversal follows `DEPENDS_ON` relationships across up to four edges.

The weight decision becomes stale because its supporting source changed. Memory derived from that decision is excluded from later recall. The independent invoice package-count approval remains current.

The previous decision stays in the history. Its approval happened; its evidence is no longer current. Keeping those two facts separate makes the review trail easier to understand.

### Giving the agent useful tools and clear limits

The AI agent can inspect issues, retrieve field evidence, examine rule explanations, recall current approved decisions and investigate change impact. It can propose a pending review task for a person to assess.

Tool execution stays inside the authenticated backend. Inputs are typed, query values are parameterized, and the model cannot execute arbitrary Cypher. Citation IDs are constrained to retrieved assertions. Investigations have bounded tool calls, time limits and database-backed spending reservations.

The agent cannot approve its own recommendation. That boundary matters because a persuasive explanation can still be wrong.

### Keeping graph context synchronized

We use PostgreSQL for authoritative records, ownership, sessions, jobs and usage accounting. FalkorDB holds versioned graph snapshots for connected context and dependency traversal.

A durable outbox coordinates projection into FalkorDB. The application publishes the graph revision only after projection succeeds. Expected-revision checks prevent an action prepared against an older dossier from silently applying to newer evidence.

If graph context is missing or out of sync, graph-dependent actions are blocked. An unavailable dependency must not produce a confident-looking decision based on incomplete context.

### What we measured

We froze ten new synthetic dossiers and twenty questions, then compared graph context with flat context using the same model, task prompt, underlying facts and output limit. The cases included missing fields, tolerance boundaries, hostile document text, source replacements and repeated corrections.

| Measure | Graph context | Flat context |
|---|---:|---:|
| Safe outcomes under the scoring contract | 19/20 | 13/20 |
| Input tokens | 30,149 | 51,461 |
| Expected citation hits | 36/36 | 36/36 |

Graph context used approximately 41% fewer input tokens in this run. The combined estimated model cost was about $0.0455 using `gpt-4.1-mini-2025-04-14`.

This was a small, same-team synthetic evaluation, not independent validation or a general accuracy guarantee. Graph mode received derived status and dependency context; the comparison measures that context representation. It does not establish that another storage system could never compute equivalent information. Retrieval in this benchmark was selected by its questions; autonomous tool selection has separate test evidence.

The [evaluation protocol](https://github.com/Ants-riseup/ClearenceX_for_Graph_Hacks/blob/main/Docs/ACCEPTANCE_EVALUATION.md) and [frozen first-run results](https://github.com/Ants-riseup/ClearenceX_for_Graph_Hacks/blob/main/output/verification/acceptance-v1.json) are public.

### The failure that taught us the most

Both modes failed one repeated-correction question. The model returned two historical affected decision IDs when the question required only the decision associated with the specific latest replaced source.

The deterministic dependency traversal and stale-memory checks passed. The failure was in how the model combined the history into its final answer.

That distinction changed how we think about validation. Correct retrieval and valid citations are necessary, but they do not prove that an answer respects the scope of the question. Both modes achieved all expected citation hits while producing different overall outcomes.

The next step is stricter source-specific impact validation, followed by fresh evaluation cases. We retained the original failure and results instead of replacing them with a more flattering rerun.

### What we learned while building

The most useful context includes validity: where a fact came from, which revision supported it and whether that support is still current. Dependency relationships make those questions explicit.

We also learned to distinguish a deterministic system failure from a model reasoning failure. That helps us choose the right repair: fix traversal when dependencies are wrong, and tighten answer contracts when the model combines correct evidence incorrectly.

Finally, building on a budget encouraged us to make costs and limits visible. Digital PDFs can be extracted locally without a paid document service. OpenAI calls are optional and budgeted. Tenant authorization, opaque sessions, CSRF protection and private document access are enforced in the backend, independently of the model.

### Try the project and inspect the work

The [hosted ClearanceX app](https://clearencexforgraphhacks.vercel.app/) uses company accounts provided by an administrator. It is a synthetic-data competition demo. Free hosting can sleep, and its storage, transport and retention limits make it unsuitable for real customer records in its current configuration. Hosted readiness and administrator sign-in have been verified; a complete customer workflow acceptance pass remains pending.

ClearanceX existed before this Graph Hacks work. We retained its document-review foundation and added the graph context, dependency invalidation and bounded agent workflow described in the [implementation record](https://github.com/Ants-riseup/ClearenceX_for_Graph_Hacks/blob/main/Docs/GRAPH_HACKS_DELTA.md). Codex assisted implementation, testing and documentation. General scanned-document extraction, maintained official tariffs and cross-shipment learning remain unfinished areas.

Explore the [source, setup instructions and competition materials](https://github.com/Ants-riseup/ClearenceX_for_Graph_Hacks). Our central design question remains simple: when the evidence changes, can the system explain exactly which decisions need another look?
