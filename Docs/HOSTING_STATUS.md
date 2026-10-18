# Hosting status

Updated 18 October 2026.

Frontend: https://clearencexforgraphhacks.vercel.app/

Vercel team: Nadija (Hobby). Project: `clearencex_for_graph_hacks`.
Git integration deploys `main`. The initial build failed because root installation
did not install frontend dependencies. The corrected installation and output paths
produced a Ready production deployment at commit `2f3d35b`.

## Full application status

**Partial deployment.** The FastAPI backend, PostgreSQL, FalkorDB and durable PDF
storage have not been provisioned in the cloud. Hosted login and shipment processing
are unavailable. API requests deliberately return 503 until a real backend is
connected; they must not receive the frontend HTML as a successful response.

No paid plans have been enabled. Laptop databases and private environment files
are not uploaded. Local accounts are not automatically copied into cloud hosting.

## Required remaining work

1. Sign in to the chosen backend/database providers and select free plans.
2. Provision an isolated cloud PostgreSQL database and FalkorDB instance.
3. Deploy the API as a container with one worker, its ingestion/projection loops,
   and durable PDF storage. A free Render service has ephemeral storage, so it
   needs a durable object-storage adapter before it can safely retain uploads.
4. Set secrets privately, `COOKIE_SECURE=true`, and the exact Vercel origin in
   `CORS_ORIGINS`. Keep graph and database connections authenticated and encrypted.
5. Replace the `/api/:path*` unavailable rewrite with the actual backend HTTPS
   origin, preserving same-origin session cookies. Remove the temporary handler.
6. Bootstrap a cloud administrator through the supported private management flow.
7. Verify sign-in, onboarding, upload, graph retrieval, corrections, audit and export
   against the cloud services before calling this a working competition demo.

Provider limitations checked against official documentation:

- https://render.com/docs/free — free services sleep, have ephemeral filesystems;
  free Render PostgreSQL expires after 30 days. Neon Free is an alternative for
  PostgreSQL: https://neon.com/pricing.
- https://www.falkordb.com/plans/ — the advertised free cloud tier currently omits
  TLS and VPC. Confirm encrypted transport is available before sending real
  customer data; do not disable certificate verification or silently use plaintext.

Provider account sign-in, terms acceptance, and credentials remain external setup
steps. Do not paste tokens or passwords into a public issue or submission document.
