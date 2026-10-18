# ClearanceX hosting status

Updated 18 October 2026 (Asia/Colombo).

## Live addresses

- Application: https://clearencexforgraphhacks.vercel.app/
- Sign-in: https://clearencexforgraphhacks.vercel.app/auth/signin
- Administration: https://clearencexforgraphhacks.vercel.app/admin/companies
- Readiness: https://clearencexforgraphhacks.vercel.app/health/ready
- API: https://clearancex-api.onrender.com

Company access is by invitation. The initial administrator uses
`admin@clearancex.local` and the password the owner entered privately in Render.
No shared administrator password is published. Judges need a customer account;
platform administration does not grant access to customer shipment documents.

## Deployment

- Vercel: Nadija Hobby / `clearencex_for_graph_hacks`, Git deployment from `main`.
- Render: separate ClearanceX project, `clearancex-api`, Docker Free, Oregon.
- PostgreSQL: Render Free, PostgreSQL 16, `clearancex-db`, private-network access.
  External internet connections are blocked. **Expires 17 November 2026.**
- FalkorDB Cloud: Free instance `instance-c3n0ad6hy`, AWS ap-south-1,
  observed Running / Healthy. Named database-user authentication is configured.
- Private PDF originals: PostgreSQL (`PDF_STORAGE=postgres`); local files are an
  extraction cache. Defaults: 100 MB per tenant, 500 MB overall.
- Backend startup: `python -m context_app.cloud_start`, one API worker with the
  ingestion and projection loops. Readiness checks PostgreSQL and FalkorDB.
- Browser requests to `/api/` are forwarded over HTTPS through Vercel to Render,
  preserving same-origin cookies. The temporary unavailable API was removed.

Initial administrator setup only creates an account in an empty database and
never resets an existing account. Temporary bootstrap variables are removed after
successful sign-in. Customer onboarding retains its first-login password-change
requirement. Local accounts and private environment files were not uploaded.

## Hosted AI

The owner approved copying the existing OpenAI key into Render's private backend
configuration and enabling `gpt-4.1-mini-2025-04-14` with a **$0.25 application
usage ceiling**. Rates configured: $0.40 input / $1.60 output per million tokens.
The key is absent from public source and the frontend bundle. The application
reserves budget before each call and records usage in cloud PostgreSQL. This is
an application limit, not an account-wide OpenAI billing limit.

Configuration is enabled; an authenticated customer model run has not yet been
verified in this hosted environment. Configuration alone is not a successful live
agent demonstration.

## Verification completed

- Render deployment succeeded; public API readiness returned 200 / `ready`.
- Vercel readiness proxy returned 200 JSON.
- Vercel CSRF endpoint returned 200 JSON with a Secure cookie and `no-store`.
- Signed-out identity and dossier routes returned 401 JSON with `no-store`.
- Administrator sign-in succeeded through the Vercel UI; company management loaded.
- Full local backend suite: 82 passed, one Windows-specific skip. The additional
  extraction-after-cache-loss test then passed with the other storage tests.
- Clean committed-source checkout: 60 passed, 12 explicit skips (including cases
  whose fixtures are excluded from the public source).
- GitHub Linux verification succeeded for the hosting changes. Storage tests
  cover tenant isolation, integrity failures, quota rejection and cache loss.

Hosted customer onboarding, PDF upload, graph corrections, audit, exports and a
paid model investigation still need an authenticated cloud acceptance pass.
Successful hosting does not mean every item in `GRAPH_HACKS_WORKPLAN.md` is done.

## Free-tier limits

No paid hosting plans were enabled. Render Free sleeps after inactivity and cold
requests can take 50 seconds or longer. Its PostgreSQL database expires after 30
days; export or migrate data before the date above. Database retention also limits
PDF retention. General scanned OCR is not installed in this lightweight image.

FalkorDB's advertised free tier omits TLS, VPC and automated backups. This
deployment is for **synthetic competition data only**, not real customer records.
Use an encrypted graph connection and appropriate backups before production use.
Vercel and Render enforce their own limits in addition to application upload limits.

Official references: https://render.com/docs/free,
https://www.falkordb.com/plans/, https://vercel.com/docs/routing/rewrites.
