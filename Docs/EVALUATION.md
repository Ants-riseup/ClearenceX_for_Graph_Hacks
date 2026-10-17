# Validation record

Date: 17 October 2026. The exact validation status is updated as implementation checks complete. Code presence alone is not a passing result.

## Completed observations

- All 28 selected tests passed in 144.25 seconds against real local PostgreSQL 16 and FalkorDB v4.12.0. They covered selective source-change invalidation, unrelated approval preservation, graph memory, private PDFs, tenant/session/CSRF denial, role/revocation boundaries, streamed request limits, replay/stale revision behavior, projection replay, graph outage, invented tool/citation rejection and concurrent usage reservations, plus compatible existing domain tests.
- The React/TypeScript production build passed after the Context Agent/authentication changes.
- Frontend dependency audit initially found a high-severity source-map-js advisory. The compatible update was applied; the follow-up audit reported zero vulnerabilities.
- The optional MCP SDK loaded and registered six context tools. Full third-party host/model operation is a separate check.
- Three additional MCP proxy tests passed in 3.24 seconds using an in-process mock HTTP transport: session/CSRF forwarding, denied request propagation and external-origin refusal. Together with the selected suite, 31 tests passed across these runs. This is not a live MCP-host test.
- The installed core/test/MCP Python environment passed dependency consistency checks. An OSV batch advisory check reported no known advisories after compatible web/PDF/MCP dependency updates. This does not cover the optional legacy OCR dependency set or guarantee absence of vulnerabilities.
- Frontend lint completed with warnings, including legacy effect patterns and fast-refresh boundaries. These are not represented as a warning-free result.
- A read-only OpenAI account/model-access check returned HTTP 401 for the previous local key. No completion was sent and live inference is not counted as passing.
- Both production container images built. Runtime startup exposed an obsolete relative upload-directory creation, which was removed. The rebuilt API runs as a non-root user; an image check confirmed private `.env` files are excluded. Dependency consistency passed.
- The application Compose stack started successfully: PostgreSQL, FalkorDB and API were healthy; the frontend container was running and its Nginx configuration passed validation. A newly created synthetic dossier was projected by the actual background worker to graph revision 1, and an actual FalkorDB issue query returned the expected conflict.
- Automated browser access to `http://localhost:8080` was denied by the browser permission gate. No alternate browser method was attempted. Visual rendering and click-through validation remain pending; the container/data-layer results above do not substitute for that check.

## Test boundaries

`npm test` selects the new integration/agent contract tests plus existing canonical resolution, CUSDEC readiness and XML tests. The agent contract uses a clearly labeled scripted provider response while executing real graph queries and persistence. It does not prove an actual OpenAI model will choose the correct tools.

Live OpenAI quality, token prices/account access, real OCR quality, optional OCR container build, GPU/local model inference, production HTTPS, adversarial upload isolation, concurrent load, full restore and official customs acceptance are not established by these tests. No paid model calls or public deployment have been performed in this implementation session.

## Comparison protocol still required before performance claims

Create six labeled synthetic cases and twelve questions with expected field state, citations, action and abstention outcome. Compare graph-backed retrieval with a reasonable flat-text baseline using the same model, facts and context budget. Include corrected evidence and an unrelated decision. Run source-dependency edge ablation separately.

Publish each outcome, correct/expected counts, observed token usage, estimated charges and median/max run latency. Use a separately described repeated-call protocol before reporting p95. No accuracy gain, response-time guarantee or customs-rejection reduction is claimed here.
