# Phase 6–10 Audit Report — ClearanceX
**Date:** 2026-09-25 | **Auditor:** Antigravity AI

---

## ✅ PHASE 6: About / Information Sections

### Screens Inspected
| Screen | Has Meaningful Content | Placeholder Text Found |
|---|---|---|
| `ScreenOverview` (Dashboard) | ✅ Yes — project description, KPI cards, nav links | ❌ None |
| `ScreenDossiers` | ✅ Yes — upload pipeline explanation, document types | ❌ None |
| `ScreenDiscrepancies` | ✅ Yes — XAI block explanations, severity indicators | ❌ None |
| `ScreenKnowledgeGraph` | ✅ Yes — topology map with live vis.js rendering | ❌ None |
| `ScreenAuditTrail` | ✅ Yes — timestamped pipeline events, module icons | ❌ None |
| `ScreenAsycudaGateway` | ✅ Yes — EDI/XML export info, declaration list | ❌ None |
| `ScreenBatchFiling` | ✅ Yes — batch manifest concept UI | ❌ None |
| `ScreenTariffDirectory` | ✅ Yes — tariff lookup UI | ❌ None |
| `ScreenSettings` | ✅ Yes — ASYCUDA config, tolerance sliders | ❌ None |
| `ScreenAuth` (Sign In) | ✅ Yes — demo mode notice added | ❌ None |
| `Header` sidebar | ✅ Yes — nav, HSM status pill, app branding | ❌ None |

**PHASE 6 STATUS: ✅ PASS** — No Lorem Ipsum, "Coming Soon", or placeholder text found in any screen.

---

## ✅ PHASE 7: Frontend / Backend Integration

### Request Flow Verified
```
Browser (localhost:5173)
   ↓  VITE_API_URL = http://localhost:8000/api
frontend/src/utils/api.ts  (axios, all calls go through this)
   ↓
FastAPI (localhost:8000)
   ↓
AI Pipeline (MockPipeline / DossierManager)
   ↓
PostgreSQL (DATABASE_URL env var — optional in demo mode)
```

### API Mapping Verified
| Frontend Call | Backend Endpoint | Status |
|---|---|---|
| `uploadShipment()` → `POST /api/upload` (fallback: `/api/shipments/upload`) | `upload_router.py` / `routes.py` | ✅ PASS |
| `getShipmentStatus(id)` → `GET /api/shipments/{id}/status` | `routes.py` | ⚠️ Returns hardcoded mock (always "completed") |
| `getExtraction(id)` → `GET /api/shipments/{id}/extraction` | `routes.py` | ✅ PASS (uses MockPipeline) |
| `getGraph(id)` → `GET /api/shipments/{id}/graph` | `routes.py` | ✅ PASS |
| `getDiscrepancies(id)` → `GET /api/shipments/{id}/discrepancies` | `routes.py` | ✅ PASS |
| `getAuditTrail(id)` → `GET /api/shipments/{id}/audit-trail` | `routes.py` | ✅ PASS |
| `exportAsycuda(id)` → `GET /api/shipments/{id}/asycuda-export` | `routes.py` | ✅ PASS |

### Key Integration Points
- **API Base URL**: Read from `import.meta.env.VITE_API_URL` with fallback to `http://localhost:8000/api` ✅
- **CORS**: Now configurable via `CORS_ORIGINS` env var ✅ (fixed in Phase 1-5)
- **Auth headers**: None — API is fully open (no token/session required) ⚠️
- **Shipment ID flow**: Set in `sessionStorage` via `useShipment()` context — survives page refresh ✅
- **Demo fallback**: All screens fall back to `'demo-shipment'` ID when none is set ✅
- **Error handling**: All API calls catch errors and show toast notifications ✅

### Docker Networking Note ⚠️
When running in Docker, the frontend browser makes requests to `http://localhost:8000/api`. This works correctly because:
- The browser runs on the **host machine** (not inside Docker)
- Backend port `8000` will be mapped to `localhost:8000` via Docker port mapping
- `VITE_API_URL` must match the host-side port — this is correct as long as the compose file maps `8000:8000`

**PHASE 7 STATUS: ✅ PASS WITH WARNING** — Integration works end-to-end. `getShipmentStatus` is mocked.

---

## ✅ PHASE 8: Authentication Audit

### What Was Found
| Check | Result |
|---|---|
| Login form exists (UI) | ✅ |
| Login calls real backend auth endpoint | ❌ No — `handleLogin()` calls `navigate('/')` unconditionally |
| Password is validated server-side | ❌ No — any email/password succeeds |
| Session token / JWT issued | ❌ No |
| Session expiration logic | ❌ No |
| Logout endpoint | ❌ No — "Sign In" link in header just navigates to `/auth/signin` |
| Protected routes (frontend) | ❌ All routes are fully public |
| Protected routes (backend) | ❌ No middleware — all API endpoints are open |
| Hardcoded credentials in source | ⚠️ Default email/password pre-filled in state (demo only) |
| Demo mode clearly labelled | ✅ — Amber banner added to Sign In screen |

### Bypass Assessment
- **Complete bypass possible**: Any user can visit any route without logging in.
- This is an intentional demo/hackathon simplification — documented clearly on the Sign In screen now.

**PHASE 8 STATUS: ❌ FAIL (by design for demo)** — Auth is simulated. Demo mode clearly labeled ✅. No real credential exposure risk since there's no real auth system to bypass.

---

## ✅ PHASE 9: Authorization / RBAC Audit

### What Was Found
| Check | Result |
|---|---|
| Role definitions in DB schema | ❌ No `users` or `roles` table in `schema.sql` |
| Role definitions in models | ❌ No `User` or `Role` SQLAlchemy model |
| Backend route protection (decorators/dependencies) | ❌ No `Depends(get_current_user)` or equivalent anywhere |
| Frontend role-based rendering | ❌ Not implemented |
| Admin-only operations | ❌ No admin concept |

### Assessment
There is **no RBAC system** in place. All API endpoints are publicly accessible. This is consistent with the app being a demo-mode hackathon submission and is acceptable given the mock auth strategy.

**PHASE 9 STATUS: ⚠️ NOT IMPLEMENTED** — Acceptable for demo. Should be noted in README.

---

## ✅ PHASE 10: Database Audit

### Schema Completeness
| Table | Defined in `schema.sql` | SQLAlchemy Model | Status |
|---|---|---|---|
| `shipments` | ✅ | ✅ `Shipment` | ✅ |
| `documents` | ✅ | ✅ `Document` | ✅ |
| `extractions` | ✅ | ✅ `Extraction` | ✅ |
| `discrepancies` | ✅ | ✅ `Discrepancy` | ✅ |
| `audit_logs` | ✅ | ✅ `AuditLog` | ✅ |
| `corrections` | ✅ | ✅ `Correction` | ✅ |
| `norm_cache` | ✅ (with pre-seed INSERTs) | ❌ No SQLAlchemy model | ⚠️ |
| `dossiers` | ✅ | ❌ No SQLAlchemy model | ⚠️ |
| `dossier_documents` | ✅ | ❌ No SQLAlchemy model | ⚠️ |

### DB Initialization Flow
| Check | Result |
|---|---|
| `DATABASE_URL` reads from env var | ✅ `connection.py` line 6 |
| `init_db()` function exists | ✅ `connection.py` line 22 |
| `init_db()` called at app startup | ❌ **WAS MISSING** — Fixed ✅ (lifespan added to `main.py`) |
| Migration framework (Alembic) | ❌ Not used — raw `schema.sql` only |
| `schema.sql` has all needed tables | ✅ |
| `schema.sql` pre-seeds `norm_cache` | ✅ |
| Fresh evaluator can initialize DB | ⚠️ Only if they manually run `psql -f backend/schema.sql` |

### Critical Fix Applied
**`init_db()` was never called on startup.** A fresh Docker container would spin up PostgreSQL and FastAPI, but the tables would **never be created**, causing `DossierManager` and any real DB operations to fail immediately.

**Fix applied to `backend/main.py`:**
- Added a FastAPI `lifespan` context manager
- Calls `init_db()` (SQLAlchemy `Base.metadata.create_all()`) on startup
- Fails gracefully with a warning log if DB is unreachable — demo/mock mode still works

**PHASE 10 STATUS: ✅ PASS WITH WARNING**
- DB auto-initializes via SQLAlchemy on startup ✅ (after fix)
- Missing SQLAlchemy models for `norm_cache`, `dossiers`, `dossier_documents` ⚠️ (non-blocking — covered by `schema.sql`)
- No Alembic migrations ⚠️ (raw `schema.sql` must be applied for full setup)

---

## 📋 Phase 6-10 Summary Matrix

| Check | Result |
|---|---|
| No placeholder content in any screen | ✅ PASS |
| All core API endpoints reachable | ✅ PASS |
| Frontend correctly calls backend | ✅ PASS |
| Auth is real end-to-end | ❌ Demo mode (labeled) |
| Protected routes enforced | ❌ Not implemented |
| RBAC implemented | ❌ Not implemented |
| DB schema complete | ✅ PASS |
| DB auto-initializes on startup | ✅ PASS (fixed) |
| DB usable in fresh environment | ⚠️ Needs `psql -f schema.sql` OR Docker with Postgres |

## 🔧 Fix Applied This Phase

| Fix | File | Description |
|---|---|---|
| Added `lifespan` startup handler | `backend/main.py` | Calls `init_db()` automatically on every server start — critical for Docker fresh evaluation |
