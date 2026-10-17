# Repeatable demo

Use only the generated synthetic dossier. Account setup and model configuration are in README/LOCAL_SETUP. Do not include credentials, private files or API keys in the recording.

1. Open Context Agent and create a synthetic example. Wait for the synced indicator.
2. Show three real PDF files with explicitly precomputed extraction: invoice/packing-list 450 kg and AWB 440 kg. Click the source page.
3. If the OpenAI model is configured, ask why the dossier is blocked. Show actual tool activity, citations, model identity and usage. Otherwise demonstrate deterministic graph evidence and say the live agent still needs configuration; do not record an unconfigured run as agent success.
4. Enter a reason, create a weight review task and approve the packing-list assertion after synchronization.
5. Create/approve a separate task for invoice package count 12. This decision should survive the next change.
6. Apply the synthetic packing-list correction to 440 kg. Show the graph-derived impact, the weight decision becoming stale, and package count staying current.
7. Ask the agent to investigate the changed evidence and propose a new review task. Approval remains a human action.
8. Reopen the session/dossier and show persisted history, current memory and export blockers. The prototype is not a customs filing integration.

Record a short video matching any actual submission-form limit. Start with the conflict/change result, then show the evidence and action. Include the relevant Cypher file, passing check results and one denied cross-tenant access case. Trim idle time honestly; do not imply unmeasured latency. A video is a team deliverable and has not been fabricated by the implementation.

For repeat demonstrations, create a fresh synthetic example. Existing real dossiers are never reset/deleted by a demo action. Reapplying the correction creates another explicit source revision and is not a hidden fixture reset.

## Additional implemented controls

Show listing search/status/sort and the real document-count processing stages. In Context Agent, show reference/type correction, replacement and source history, extraction warnings, raw versus normalized values, private saved review reason and next unresolved field. Workspace settings are persisted and versioned; changing weight tolerance invalidates affected approvals. Batch preparation accepts selected dossiers and reports each item, including blocked ones; download produces a ZIP with a manifest, not customs transmission.

The packaged automated live/API flow and MCP checks have passed; visual clicking remains blocked by browser policy in this session. Use the team technical brief and submission checklist to prepare an actual human-recorded demo. Never record an API script as a browser walkthrough.
