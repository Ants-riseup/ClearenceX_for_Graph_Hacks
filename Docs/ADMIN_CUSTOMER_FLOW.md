# ClearanceX administrator and customer flow

Updated 18 October 2026. This replaces the earlier interpretation of an admin managing roles inside one customer's workspace.

ClearanceX is the product supplied to export companies. The **ClearanceX administrator** adds customer login accounts. An added **customer user** signs in to the existing product and processes their shipments in a private company workspace.

## Administrator

Open `/admin/companies` after signing in. The admin dashboard provides:

- **Add customer user:** company name, customer email, optional contact name and password. A password is generated if omitted.
- The new user's login details, displayed once with a masked password and Show/Dismiss controls. Share them privately; no email is sent.
- Search by company name or customer email, customer status and shipment counts.
- Edit company/contact details, reset customer passwords, disable/restore access and remove access while retaining shipment history.
- Recent customer-administration activity.

The dashboard does not offer a customer-to-platform-admin role selector. Platform administration is an explicit operator privilege; an existing workspace `admin` role alone does not grant it. Its APIs expose company access management, not shipment contents. The platform administrator is redirected to this dashboard and cannot enter customer shipment APIs with that account.

Removal means removing access, not erasing customer documents. It is reversible. No irreversible deletion or unrequested customer-data migration has been performed.

## Customer

The added user signs in at `/auth/signin`, chooses a private password at `/auth/change-password`, then enters the existing product: Overview, PDF upload, review, Context Agent, graph, audit and supported export/batch workflows. The Overview design and these shipment screens are retained. Customers cannot create their own account through public signup, access the admin portal, or read another company's shipments.

Each dashboard onboarding creates one company workspace and its initial User login. Existing company memberships/data are preserved. The initial account is not placed into the platform administrator's existing customer workspace.

## Local accounts and setup

The existing local administrator and customer email/password choices are preserved. Private details remain in ignored `tmp/admin-access.json` and `tmp/local-access.txt`; never publish those files. The admin credential file points to the new dashboard.

For a new installation, create the initial operator account using `context_app.admin create-user --email <operator-email> --role admin`, then explicitly run `context_app.admin grant-platform-admin --email <operator-email>` inside the API container. Subsequent customers are added through the dashboard. The explicit CLI grant revokes that operator's prior sessions and does not promote other accounts automatically.

Migration 7 adds company status/profile/version, an explicit platform privilege and company-administration events. A private backup was taken before applying it locally. Password hashing, session revocation, origin/CSRF checks, password confirmation throttling, bound SQL values, fixed graph queries and version conflicts remain enforced.

Migration 8 adds first-login password setup. New accounts and future admin resets require a customer-chosen password; previous local accounts remain unchanged. Password changes rotate the current session/CSRF and revoke other sessions. Admin actions now have confirmation dialogs, status filters and focused search after creation. See [WEB_POLISH_REPORT.md](WEB_POLISH_REPORT.md).

## Verification

- Full selected backend suite: **78 passed, 1 skipped**. Customer/platform security tests cover onboarding, product access, platform denial, isolation, password reset, access suspension/restoration, retained shipments, SQL/Cypher inputs and concurrent edits. The existing Windows stdio MCP skip remains.
- Frontend: **28 interaction tests passed**, including seven dashboard tests and nine auth/graph-preview tests; the same tests pass in the Linux container build.
- API/frontend containers rebuilt successfully; migration versions 1–8 are applied locally. Existing lint warnings remain; splitting routes reduced the main entry to about 315 kB.
- Running customer smoke: use `python scripts/verify_customers.py --pdf-folder "Docs/TEST FILE"` with private operator credentials. It exercises customer creation/login, forced password setup, product access, cross-company denial, password reset and supplied digital PDFs; QA access is disabled afterward. Its results are saved in `output/verification/customer-runtime.json` after a successful run.
- **Running result: 38 checks passed**, including successful extraction of all four supplied PDFs by a newly added customer. A second company was denied access to that upload. Existing local operator/customer login choices were also verified unchanged. The first smoke used the legacy shipment-status endpoint's completion vocabulary; the harness was corrected to poll the durable upload-status endpoint and then passed. That initial harness failure is not counted as a successful run.
- No new real-browser visual sign-off is claimed; the prior saved browser policy remains a separate limitation. Component interactions and actual HTTP/data behavior are tested separately.

The customer workflow is retained and tested within its existing supported scope. This change does not certify arbitrary PDF layouts, official customs acceptance, production security or completion of every competition roadmap item.
