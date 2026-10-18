# Hosting status

Updated 18 October 2026.

Frontend: https://clearencexforgraphhacks.vercel.app/

Vercel team: Nadija (Hobby). Project: `clearencex_for_graph_hacks`.
Git integration deploys `main`. The initial build failed because root installation
did not install frontend dependencies. The corrected installation and output paths
produced a Ready production deployment at commit `2f3d35b`.

## Full application status

**Partial deployment.** PostgreSQL 16 is available on Render Free, with external
internet connections blocked. It expires on **17 November 2026**. The FalkorDB Free
instance `instance-c3n0ad6hy` is provisioning; its last observed state was
Deploying / Unhealthy. The API deployment form is prepared but not submitted.
Hosted login and shipment processing
are unavailable. API requests deliberately return 503 until a real backend is
connected; they must not receive the frontend HTML as a successful response.

No paid plans have been enabled. Laptop databases and private environment files
are not uploaded. Local accounts are not automatically copied into cloud hosting.

## Required remaining work

1. Sign in to the chosen backend/database providers and select free plans.
2. Wait for the FalkorDB instance to become healthy and verify connectivity.
3. Deploy the API as a container with one worker, its ingestion/projection loops,
   and durable PDF storage. `PDF_STORAGE=postgres` now stores private PDF originals
   transactionally in PostgreSQL and restores the ephemeral extraction cache.
   Default quotas are 100 MB per tenant and 500 MB overall. Tenant isolation,
   integrity failure, quota rejection and extraction after cache loss were tested.
4. Set secrets privately, `COOKIE_SECURE=true`, and the exact Vercel origin in
   `CORS_ORIGINS`. Keep graph and database connections authenticated and encrypted.
5. Replace the `/api/:path*` unavailable rewrite with the actual backend HTTPS
   origin, preserving same-origin session cookies. Remove the temporary handler.
6. Use `python -m context_app.cloud_start` as the Render Docker Command. Set
   `BOOTSTRAP_ADMIN_EMAIL` and a private `BOOTSTRAP_ADMIN_PASSWORD` of at least
   12 characters for the first deployment, then remove these variables. Bootstrap
   only runs in an empty account database, never resets existing credentials,
   and requires a password change on first sign-in.
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

Verification: 82 backend tests passed, one Windows-specific test skipped. The
additional ingestion-after-cache-loss test subsequently passed with the two other
storage tests. No new paid OpenAI calls were used for this hosting work.
