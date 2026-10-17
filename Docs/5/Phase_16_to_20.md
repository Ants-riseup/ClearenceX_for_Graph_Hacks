# Project Submission Readiness Audit (Phases 16-20)

## PHASE 16: Fresh Evaluator Simulation
Simulate a clean evaluation from scratch:
- Clone repo in a clean directory and follow the `README.md` exactly.
- Do not perform undocumented setup steps.
- Note any points where an evaluator gets stuck (e.g., missing env vars, wrong ports, missing migrations).

## PHASE 17: README Audit
Verify the README includes:
- Overview, Features, Architecture.
- Prerequisites, Env Variables (and `.env.example`).
- Exact Docker setup (Build/Start commands).
- Access URLs (Frontend & Backend).
- Database/Migration setup and Troubleshooting steps.
- Ensure no fake placeholders remain.

## PHASE 18: Git Repository Audit
Inspect repo state before submission:
- `git status`, `git log`.
- Ensure ignored files are not tracked (`.env`, credentials, `node_modules`, `__pycache__`, local DB files).
- Verify `.gitignore` does not accidentally exclude required files (Dockerfiles, migrations, configs).

## PHASE 19: Build / Test Verification
Run actual project checks (e.g., `npm run build`, `pytest`, `npm test`):
- Identify any failures blocking submission.
- Fix issues if reasonable, re-run, and record final results.
- Do not invent test results.

## PHASE 20: Security Sanity Check
Perform a practical release security check:
- Look for hardcoded credentials, exposed API keys, or bypassed auth.
- Check for unprotected sensitive endpoints, unsafe CORS, and exposed stack traces.
