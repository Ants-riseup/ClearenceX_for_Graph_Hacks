# Local setup, operation and recovery

## Application

1. Install Docker/Compose and Node only if doing host development. The default Docker flow needs no hosted database or authentication subscription.
2. Run `powershell -ExecutionPolicy Bypass -File scripts/setup-local.ps1` from the root. It creates `.env.graphhacks` with generated passwords and does not overwrite an existing file. Linux/macOS users can copy the example and generate passwords themselves.
3. Run `docker compose --env-file .env.graphhacks up --build -d`.
4. Create an account with `docker compose --env-file .env.graphhacks exec api python -m context_app.admin create-user --email you@example.com`.
5. Open `http://localhost:8080`. Save the generated account password privately; it is not a shared fixture password.

During this implementation session the local stack was started and a reviewer account plus one synthetic dossier were created. Their generated credentials are saved privately in the ignored `tmp/local-access.txt` file. Do not publish that file or include it in the competition submission. The browser walkthrough remains pending because the browser permission gate denied access in this session.

Additional accounts: use the same `--tenant` name to add a teammate, or a different name to create an isolated workspace. `--role viewer` creates a read-only account; `--role admin` is available for local administration. Public signup is disabled. Historical unowned dossiers are not assigned by guessing an owner. Account recovery and ownership migration require an explicit administrative process; no email-recovery service is simulated.

The API uses one process/ingestion worker in Compose. Run `python -m context_app.admin migrate` for an explicit repeatable additive schema setup. This release adds `cx_*` tables and does not alter or delete legacy tables. Review database changes and take a backup before migrating an existing database. Startup also ensures the additive tables exist. Automatic destructive migrations are not performed.

## Optional inference

Configure the backend model key/name and budget/prices in `.env.graphhacks` as described in README. Live inference starts disabled. Synthetic demo evidence, review, graph traversal and source-change actions work without it. A failed/unconfigured model is displayed as unavailable.

This release implements the OpenAI provider. Ollama is retained in the work plan as an optional future adapter; it is not silently claimed operational. OpenAI vision/embeddings inside legacy OCR are not automatically enabled. The local extraction worker deliberately strips provider credentials, while the explicit agent uses the budget ledger.

## Optional OCR

The lightweight image provides the graph/agent workflow and PDF validation. Set `WITH_OCR=true` and rebuild to attempt installation of the historical PaddleOCR dependency set. Its large downloads, platform compatibility, image quality and multipage/table accuracy need separate validation. Local uploads fail honestly if OCR is unavailable; no demo values are substituted.

Each document is processed in a credential-isolated subprocess with a 120-second timeout. It remains a prototype boundary, not a hardened sandbox or strict process memory limit. Do not expose uploads to arbitrary public traffic before further parser/resource isolation review.

Pending uploads are durable in PostgreSQL. If the API stops during extraction, stop **all** API processes, run `python -m context_app.admin recover-uploads`, then restart one API. Affected uploads can be retried at `POST /api/upload/{id}/retry`. Do not run recovery concurrently with an active worker. Source context is published only when all documents complete successfully.

## Graph recovery

Outbox events persist and retry after restart. In Context Agent select **Retry synchronization** after restoring FalkorDB. This rebuilds the current dossier snapshot idempotently. `graph_revision` must match the dossier revision before proposals/approvals/impact tools run. No fallback computes a successful graph investigation from SQL.

Stop services with `docker compose --env-file .env.graphhacks stop`; resume with `up -d`. Named volumes retain data. Avoid removing volumes unless you intend to delete all application data. Backups/restore drills and automated retention remain production work.

## MCP

The optional stdio adapter exposes the same six narrow tools through authenticated HTTP routes. Install `backend/requirements-mcp.txt` in the chosen Python environment. Run `python -m context_app.mcp_server` with:

- `CLEARANCEX_MCP_API`: loopback HTTP API origin, default `http://127.0.0.1:8000`.
- `CLEARANCEX_MCP_SESSION`: an existing opaque development session, injected privately through the MCP host environment, never a tool argument or committed config.
- `CLEARANCEX_MCP_ORIGIN`: an allowed browser/API origin, default `http://localhost:8080`.

Run inside the API container or a local host-development setup where the API is reachable on loopback; the default Compose setup does not publish the API port separately. Install the optional dependency set there before use. Session expiry, logout and membership revocation continue to apply. The adapter has no approve/export/shell/arbitrary-query tools.

Tool registration and HTTP contract behavior are tested separately from a particular third-party MCP host. A specific host configuration, live model choosing MCP tools and cross-agent handoff are not yet validated.

## Host development and tests

Create `.venv`, install `backend/requirements-test.txt`, and run `npm --prefix frontend ci`. Start isolated infrastructure with `npm run test:infra`; ports are 5449 and 6399. Run `npm test`.

For a host API point `DATABASE_URL`, `FALKORDB_HOST/PORT/PASSWORD`, `UPLOAD_ROOT` and `CORS_ORIGINS` at your intended local services. From backend run `python -m uvicorn main:app --port 8000`; root `npm run dev` starts Vite with a same-origin `/api` proxy. Keep origins consistent: localhost and 127.0.0.1 differ for cookies and origin checks.

If a corporate network uses a custom TLS certificate, install/trust its actual CA in the development/container runtime. Do not disable TLS verification. Initial downloads require internet. App runtime still needs internet in OpenAI mode. UI fonts and icons are bundled locally; the core synthetic demo has no font CDN dependency.

