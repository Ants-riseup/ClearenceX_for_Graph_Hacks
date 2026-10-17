# Project Submission Readiness Audit (Phases 11-15)

## PHASE 11: Environment Variables
- Document all required environment variables (`.env.example`).
- Ensure no real secrets, passwords, or API keys are committed to the repo.
- Verify Docker correctly receives and utilizes necessary variables.

## PHASE 12: Dockerfile Audit
Inspect every Dockerfile for correctness:
- Base image, working directory, dependencies, and `COPY` commands.
- Ensure correct build/start commands and exposed ports.
- Fix issues like wrong package manager, missing source files, or incorrect start commands.

## PHASE 13: Docker Compose Audit
Inspect `docker-compose.yml`:
- Verify services (frontend, backend, db), contexts, and Dockerfile paths.
- Check mapped ports, environment variables, volumes, and service dependencies.
- Evaluators should not need to manually configure or start individual services.

## PHASE 14: Docker Actual Testing
Run the system as an evaluator would:
- Build: `docker compose build`
- Start: `docker compose up -d --build`
- Verify services stay running (`docker compose ps`, `docker compose logs`).
- Test endpoints (e.g., `curl http://localhost:<port>`). Frontend and backend must communicate successfully.

## PHASE 15: Docker Restart Test
Test system resilience:
- Stop the system: `docker compose down`
- Restart the system: `docker compose up -d`
- Verify the application still starts and works correctly.
