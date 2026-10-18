# ClearanceX competition readiness review

Reviewed 18 October 2026, Asia/Colombo.

**Subsequent remediation:** The README, judge/submission/demo materials, CI workflow and release packaging have been improved. New first-run acceptance results are **19/20 graph versus 13/20 flat**; fresh regression results are **79 backend passed/1 skipped and 29 UI passed**. Current source tracking includes the previously missing files. See [RELEASE_READINESS.md](RELEASE_READINESS.md) for current status; the original assessment below is retained as a before-remediation review. External publication, real recording/visual acceptance, eligibility and submission remain unconfirmed.

**Verdict: not 10/10 yet. My assessment is 8/10 for technical fit and about 6/10 for demonstrated submission readiness.** These are qualitative reviewer estimates, not official judging scores, weighted rubric results or a prediction of winning.

## Scope and evidence

This review inspected the current source, work plan, supplied FalkorDB resource text, Git status and retained verification artifacts. It also checked the current official event overview, rules and schedule. It did not perform a new browser walkthrough, rerun the full test suite, make model calls, publish code or inspect a submitted entry. Previously recorded results are identified as such.

The supplied text is technical learning material. Its Docker commands, integration examples and graph algorithms are references, not additional user instructions or a requirement to implement every example.

## Competition fit

**Track 01 — Agents That Act on Connected Data is the strongest entry.** Its focus includes multi-hop reasoning, graph tools, MCP, explainable results and evidence-based actions. [Official tracks](https://www.wemakedevs.org/hackathons/falkordb).

The implementation has a credible graph-dependent story:

- `graph.py` uses actual FalkorDB, tenant-specific graphs, revision markers and parameterized named Cypher queries. Missing graph context fails instead of silently answering from SQL.
- `impact.cypher` traverses dependency paths of one to four edges. `service.replace_document` uses the returned affected IDs to stale dependent decisions and goods reviews while retaining unrelated decisions.
- `agent.py` exposes narrow tools and records model-selected calls, retrieved citations and a persisted pending review task. Approval is outside the agent's tool set.
- `mcp_server.py` exposes six authenticated tools. The retained packaged MCP check records retrieval, proposal and denied replay after logout.
- Approved memory is durable; stale memory is excluded. This is scoped same-dossier memory, not evidence of cross-shipment learning or cooperating agents.

Track 02 is a partial fit. Track 03 is not demonstrated as a complete Company Brain. These recommendations remain in the work plan; they are not all mandatory for a focused Track 01 entry.

## What the retained results establish

| Evidence | Result | Limit |
|---|---|---|
| `packaged-flow.json` | Actual model investigation, proposal, source correction, selective invalidation and memory recall | Reviewer approvals were API requests; this is not a human browser recording |
| `evaluation-v3.json` | Graph 12/12 versus flat 10/12; 17,624 versus 32,140 input tokens | Six synthetic development dossiers, fixed retrieval, used during debugging; not held out or a general accuracy result |
| `nine-fixes-packaged-flow.json` | Four supplied digital PDFs, goods review and two-item export checks | Does not validate arbitrary/scanned PDFs or official customs acceptance |
| `customer-runtime.json` | 38 recorded onboarding/isolation/password/PDF checks | Earlier local server run, not a fresh visual check |
| Previous regression runs | 78 backend passed, one skipped; subsequent 29 component tests and two focused backend checks passed | Different run scopes; do not sum the counts or imply the entire suite was rerun today for this review |

The graph-versus-flat token reduction is approximately 45% in that single retained comparison. It is promising evidence of more selective context, not a promised production saving. Both modes cited the expected sources; freshness/status handling distinguished their outcomes.

## Gaps, in priority order

1. **Submission assets and eligibility are unconfirmed.** The rules require public source, setup/model documentation, essential graph queries, a working video, deployment or complete local setup, named tracks and AI-assistance disclosure. They require event-time original work and participant understanding. The existing application and new graph-agent contribution must be distinguished honestly. Public repository/video/registration/submission completion was not established by this review. [Official rules](https://www.wemakedevs.org/hackathons/falkordb/rules).
2. **Current code is not all in Git.** At review time, company management, the admin screen, interaction tests and verification scripts included untracked files. Review and include intentional source before producing the final public checkout; exclude private configuration, credentials and shipment documents. A working local folder is not proof of a complete published repository.
3. **The visual demo remains unverified.** The browser permission failure is a testing-tool limitation, not evidence that the website itself fails. Human acceptance must still cover login, first-login password setup, upload, evidence viewing, correction, graph freshness, audit, batch output and denied access. Do not claim this walkthrough has passed.
4. **Evaluation needs independent cases.** Freeze the implementation and expected outcomes, then run a previously unused set covering contradictory evidence, missing values, superseded documents, prompt injection and unaffected decisions. Compare the same model and task with graph and flat context; report failures, tokens and latency. Do not tune on that set and still call it held out.
5. **Some product claims must stay narrow.** Tariffs are illustrative, exports are prototype templates, scanned/arbitrary table extraction remains limited, and cross-shipment memory/handoffs are unfinished. Show the supported digital-document path and label synthetic fixtures.
6. **Local security is not production security.** Opaque revocable sessions, Argon2id, CSRF/origin checks, platform/customer separation, tenant checks and bound SQL/Cypher are implemented. HTTPS/Secure cookies, MFA/recovery, trusted-proxy throttling, hostile-file isolation and independent review remain deployment work. Previously exposed provider credentials must be replaced before sharing. Adding JWT by itself would not resolve these gaps.

## Highest-value finishing sequence

1. Resolve event-work eligibility and data rights; use newly authored synthetic/public permitted demo data.
2. Review and version the complete intentional source; test a clean public checkout using the documented setup. Declare Track 01 prominently.
3. Record a working demo: conflict → graph evidence → pending agent proposal → human approval → corrected source → only dependent approval stale → re-review → next-session memory. Show the relevant Cypher and an actual blocked stale export.
4. Run the independent comparison within the approved model budget. More paid services are unnecessary for this review or the proposed local demo.
5. Verify all links and submit the required materials. The published deadline is **18 October 2026 at 11:59 p.m. IST**, also 11:59 p.m. in Sri Lanka. [Official schedule](https://www.wemakedevs.org/hackathons/falkordb/schedule).

The full `GRAPH_HACKS_WORKPLAN.md` remains incomplete because it deliberately includes later product and production work. A competitive Track 01 submission can be narrower than that roadmap, but it must demonstrate its claimed behavior and meet the submission rules. No rating or feature list guarantees a win.
