# Local setup, operation and recovery

## Application

1. Install Docker/Compose and Node only if doing host development. The default Docker flow needs no hosted database or authentication subscription.
2. Run `powershell -ExecutionPolicy Bypass -File scripts/setup-local.ps1` from the root. It creates `.env.graphhacks` with generated passwords and does not overwrite an existing file. Linux/macOS users can copy the example and generate passwords themselves.
3. Run `docker compose --env-file .env.graphhacks up --build -d`.
4. Create an account with `docker compose --env-file .env.graphhacks exec api python -m context_app.admin create-user --email you@example.com`.
5. Open `http://localhost:8080`. Save the generated account password privately; it is not a shared fixture password.

During this implementation session the local stack was started and a reviewer account plus one synthetic dossier were created. Their generated credentials are saved privately in the ignored `tmp/local-access.txt` file. Do not publish that file or include it in the competition submission. The browser walkthrough remains pending because the browser permission gate denied access in this session.

Additional accounts: use the same `--tenant` name to add a teammate, or a different name to create an isolated workspace. `--role viewer` creates a read-only account; `--role admin` is available for local administration. Public signup is disabled. Historical unowned dossiers are not assigned by guessing an owner. Account recovery and ownership migration require an explicit administrative process; no email-recovery service is simulated.

The API uses one process/ingestion worker in Compose. Run `python -m context_app.admin migrate` for an explicit repeatable additive schema setup. Five ordered transactional migrations record the additive schema, indexes, workspace settings, export/batch tables and reviewed-goods provenance in `cx_schema_migrations`. Existing legacy records are preserved; no automatic downgrade or data deletion runs. `python -m context_app.admin migration-status` prints applied versions. Review database changes and take a backup before migrating an existing database. Startup also ensures the additive tables exist. Automatic destructive migrations are not performed.

## Optional inference

Configure the backend model key/name and budget/prices in `.env.graphhacks` as described in README. Live inference starts disabled. Synthetic demo evidence, review, graph traversal and source-change actions work without it. A failed/unconfigured model is displayed as unavailable.

This release implements the OpenAI provider. Ollama is retained in the work plan as an optional future adapter; it is not silently claimed operational. OpenAI vision/embeddings inside legacy OCR are not automatically enabled. The local extraction worker deliberately strips provider credentials, while the explicit agent uses the budget ledger.

## Optional OCR

The default image provides actual local digital-PDF text extraction as well as the graph/agent workflow and PDF validation. Labeled fields are parsed across pages; explicit pipe-delimited goods rows keep page/row provenance and require review. This is actual extraction, not precomputed fixture data. Scanned PDFs need the optional OCR engine. Set `WITH_OCR=true` and rebuild to attempt installation of the historical PaddleOCR dependency set. Its large downloads, platform compatibility, image quality and multipage/table accuracy need separate validation. Scanned/unsupported uploads fail honestly if OCR is unavailable; no demo values are substituted.

Each document is processed in a credential-isolated subprocess with a 120-second timeout. Linux extraction processes have a 2 GiB address-space and 90-second CPU cap. Validation uses a separate 512 MiB/5-second parser process with a 10-second parent timeout. Windows does not apply these Unix resource limits. This remains a prototype subprocess boundary, not a hardened hostile-file sandbox. Do not expose uploads to arbitrary public traffic before further parser/resource isolation review.

Pending uploads are durable in PostgreSQL. If the API stops during extraction, stop **all** API processes, run `python -m context_app.admin recover-uploads`, then restart one API. Affected uploads can be retried at `POST /api/upload/{id}/retry`. Do not run recovery concurrently with an active worker. Source context is published only when all documents complete successfully.

## Graph recovery

Outbox events persist and retry after restart. In Context Agent select **Retry synchronization** after restoring FalkorDB. This rebuilds the current dossier snapshot idempotently. `graph_revision` must match the dossier revision before proposals/approvals/impact tools run. No fallback computes a successful graph investigation from SQL.

Stop services with `docker compose --env-file .env.graphhacks stop`; resume with `up -d`. Named volumes retain data. Avoid removing volumes unless you intend to delete all application data. A backup/restore drill has passed for PostgreSQL, a FalkorDB snapshot and private PDF hashes. Automated destructive retention is not enabled; workspace settings expose a review preview.

## MCP

The optional stdio adapter exposes the same six narrow tools through authenticated HTTP routes. The default API image includes the MCP dependency set. For host development install `backend/requirements-mcp.txt` in the chosen Python environment. Run `python -m context_app.mcp_server` with:

- `CLEARANCEX_MCP_API`: loopback HTTP API origin, default `http://127.0.0.1:8000`.
- `CLEARANCEX_MCP_SESSION`: an existing opaque development session, injected privately through the MCP host environment, never a tool argument or committed config.
- `CLEARANCEX_MCP_ORIGIN`: an allowed browser/API origin, default `http://localhost:8080`.

Run inside the API container or a local host-development setup where the API is reachable on loopback; the default Compose setup does not publish the API port separately. Install the optional dependency set there before use. Session expiry, logout and membership revocation continue to apply. The adapter has no approve/export/shell/arbitrary-query tools.

The packaged smoke `docker compose --env-file .env.graphhacks exec -T api python -m evaluation.mcp_smoke` passed using an actual stdio MCP client, HTTP session/CSRF, real evidence retrieval, a persisted proposal and logout denial. A particular desktop host configuration, model choosing MCP tools and cross-agent handoff remain unverified.

## Host development and tests

Create `.venv`, install `backend/requirements-test.txt`, and run `npm --prefix frontend ci`. Start isolated infrastructure with `npm run test:infra`; ports are 5449 and 6399. Run `npm test`.

For a host API point `DATABASE_URL`, `FALKORDB_HOST/PORT/PASSWORD`, `UPLOAD_ROOT` and `CORS_ORIGINS` at your intended local services. From backend run `python -m uvicorn main:app --port 8000`; root `npm run dev` starts Vite with a same-origin `/api` proxy. Keep origins consistent: localhost and 127.0.0.1 differ for cookies and origin checks.

If a corporate network uses a custom TLS certificate, install/trust its actual CA in the development/container runtime. Do not disable TLS verification. Initial downloads require internet. App runtime still needs internet in OpenAI mode. UI fonts and icons are bundled locally; the core synthetic demo has no font CDN dependency.



## Persistence and backup

FalkorDB's named volume is mounted at its actual directory, `/var/lib/falkordb/data`; PostgreSQL uses its own named volume. The pinned FalkorDB v4.12.0 instance crashed while replaying the prior AOF during a recreate test. This deployment now uses RDB snapshots (`save 60 1`, AOF disabled) with PostgreSQL as authoritative source history. The old files were preserved. This is an observed local compatibility failure, not a claim that all FalkorDB AOF configurations fail.

API startup checks each nonempty dossier's graph snapshot and queues reconstruction if missing or older. Graph tools fail closed if a supposedly synced snapshot is missing. A snapshot alone can lag recent writes; the SQL outbox/reconstruction is essential. Run `python -m context_app.admin reconcile-graphs` to queue missing projections explicitly.

Run `./scripts/backup-local.ps1` from PowerShell to pause application writers, dump PostgreSQL, save/copy the graph snapshot, copy private PDFs, and resume the app. Backups are stored under ignored `output/private-backups/`. They contain private documents and authentication records: do not publish them. Keep private configuration separately. The graph and database backup must be taken with writers paused for a coherent point.

For recovery, stop writers and restore into NEW isolated services first. Restore the PostgreSQL custom-format dump with `pg_restore`, place `graph.rdb` at the graph data directory as `dump.rdb` with AOF disabled, and restore PDFs under their original `/data/uploads` layout. Verify migrations, dossier counts, graph snapshots and stored content hashes before any production switch. Revoke restored sessions as part of an operator-reviewed real recovery because backup sessions may be older than subsequent revocations. No automatic destructive restore over live data is provided.

The performed drill restored five dossiers and four migration records into a separate database, read a shipment from a separate snapshot-loaded graph container, and verified 16 restored private PDF references/hashes. Source data was not overwritten or deleted.

## Local source review package

Run `python scripts/package_project.py` to build `output/release/ClearanceX_Graph_Hacks_Source.zip` from an explicit allowlist. It excludes private environments, PDFs/caches and local backups; selected source is checked for API-key patterns and a SHA-256 manifest is included. Inspect rights and the final archive before publishing. This command does not create a public repository or submit to the competition.


## Source-linked goods review

Open declaration readiness and verify each extracted invoice item against its source PDF. HS code, two-letter origin and item weight/package allocations are required. Matching packing rows supply source-linked defaults for review. Review every invoice row; completing processing alone never authorizes export. The app apportions evidenced freight/insurance and reconciles item values and allocation totals before preparation.

Migration 5 preserves old goods rows as unverified and stales older export artifacts. New reviews have a unique current invoice-row identity, source revision and graph dependencies. Repeating the same review is safe; source changes make dependent reviews stale. Existing old extractions are preserved: use a fresh upload for the improved parser rather than overwriting historical evidence.
