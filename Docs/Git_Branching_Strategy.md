# ClearanceX — Git Branching Strategy & Cross-Member Dependency Guide

> **Problem We're Solving:** Nadija, Aloka, and Kaveen work on different layers of the same system. They have real dependencies on each other's output. Working on separate branches makes merging painful if not planned carefully.

---

## The Core Challenge (Illustrated)

```
Nadija writes:   backend/ai_pipeline/entity_extractor.py  → outputs ExtractionResult JSON
Aloka reads:     backend/reasoning/knowledge_graph.py     → consumes ExtractionResult JSON
Kaveen reads:    frontend/src/types/index.ts              → TypeScript type for ExtractionResult
```

If all 3 work on separate branches and merge late, **type mismatches and import errors** happen at integration time.

**The solution:** Define shared contracts upfront, commit them to `main` first, then branch safely.

---

## Recommended Strategy: Feature Branches + Shared Contracts on Main

### Branch Structure

```
main                    ← Always deployable. Protected. Only merge via PR.
├── feat/ai-pipeline    ← Nadija's branch
├── feat/reasoning      ← Aloka's branch
└── feat/frontend       ← Kaveen's branch
```

### The Golden Rule

> **Shared contract files (types, interfaces, API schemas) always live on `main` first.**
> Everyone pulls from `main` before starting their day.

---

## Step-by-Step Setup

### Step 1 — Initialize & Push Main

```bash
# Nadija already did Phase 01 (React+Vite setup + shared contracts)
# He should push the initial project scaffold to main first
git init
git add README.md .gitignore
git commit -m "chore: initial repo setup"
git branch -M main
git remote add origin https://github.com/codesplash26-hackathon/ants.git
git push -u origin main
```

### Step 2 — Commit Shared Contracts to Main FIRST

> ✅ **Phase 01 was completed by Nadija.** He owns this step.
> Before anyone else branches, Nadija pushes the shared contract files to `main`.
> Kaveen and Aloka are **blocked** until these are on `main`.

```bash
# Nadija runs this — pushes all shared foundation files to main

git add frontend/src/types/index.ts          # TypeScript types (Entity, Discrepancy, GraphData...)
git add frontend/src/utils/api.ts            # API client with endpoint URLs
git add backend/ai_pipeline/mock_pipeline.py # Mock output so Aloka/Kaveen can work without Nadija's real AI
git add backend/api/routes.py                # Stub route definitions (just signatures, no logic)
git add frontend/                            # Vite + React + TypeScript scaffold
git add backend/main.py                      # FastAPI entry point
git commit -m "feat(shared): Phase 01 - Vite scaffold, shared types, mock pipeline, API stubs"
git push origin main

# ✅ After this push: Aloka and Kaveen can branch and work in parallel
```

### Step 3 — Each Member Creates Their Branch

```bash
# Each member runs this on their machine AFTER Step 2 is pushed

# Nadija:
git checkout main && git pull origin main
git checkout -b feat/ai-pipeline

# Aloka:
git checkout main && git pull origin main
git checkout -b feat/reasoning

# Kaveen:
git checkout main && git pull origin main
git checkout -b feat/frontend
```

---

## Daily Workflow (Prevent Merge Hell)

```bash
# Every morning, BEFORE starting work — sync with main
git checkout main
git pull origin main
git checkout feat/your-branch
git merge main    # Bring latest shared contracts into your branch

# Work on your code...

# Commit frequently with clear messages
git add backend/ai_pipeline/ocr_engine.py
git commit -m "feat(ai): Phase 02 - PaddleOCR integration with bbox extraction"
git push origin feat/ai-pipeline
```

---

## Dependency Resolution Protocol

This is the exact order to resolve the cross-member dependencies:

### Phase 01 — Foundation (Kaveen, Day 1, commits to `main` directly)

| File | What It Contains | Who Uses It |
|------|-----------------|-------------|
| `frontend/src/types/index.ts` | `Entity`, `Discrepancy`, `GraphNode`, `AuditEntry` TS types | Kaveen (frontend), Aloka (to match output format) |
| `backend/ai_pipeline/mock_pipeline.py` | Returns fake `ExtractionResult` JSON | Aloka (Phases 2–3), Kaveen (Phase 4+) |
| `backend/api/routes.py` | Empty route stubs with correct signatures | All |
| `backend/main.py` | FastAPI app entry point | All |

**After Kaveen pushes these to `main`, everyone else can branch and work in parallel.**

---

### Dependency Timeline (When Each Person Needs What)

```
Day 1  ✅ ALREADY DONE — Nadija (Phase 01)
─────────────────────────────────────────────────────────────────
Nadija pushes → frontend/src/types/index.ts           ← Aloka can now match output format
Nadija pushes → backend/ai_pipeline/mock_pipeline.py  ← Aloka can test reasoning engine WITHOUT real AI
Nadija pushes → backend/api/routes.py (stubs)         ← Everyone knows the API shape
Nadija pushes → frontend/ (Vite scaffold)             ← Kaveen starts from Phase 02 immediately

Day 2-3
─────────────────────────────────────────────────────────────────
Aloka pushes  → backend/api/routes.py (mock data)  ← Kaveen can wire up frontend
              → GET /shipments/:id/status (mock)
              → GET /shipments/:id/extraction (mock)
              → GET /shipments/:id/graph (mock)
              → GET /shipments/:id/discrepancies (mock)

Nadija pushes → backend/ai_pipeline/ocr_engine.py  ← Aloka verifies bbox format

Day 3-4
─────────────────────────────────────────────────────────────────
Kaveen wires  → frontend components to Aloka's MOCK API (works before real AI exists)
Aloka builds  → reasoning engine consuming mock_pipeline output
Nadija builds → real pipeline to replace mock

Day 4-5
─────────────────────────────────────────────────────────────────
Aloka merges  → real API routes (replaces mocks)
Nadija merges → real ai_pipeline (replaces mock_pipeline.py)
Kaveen tests  → full integration
```

---

## Shared File Ownership (Who Merges What to Main)

These files are **shared** — only one person should own each to prevent conflicts:

| File | Owner | Rule |
|------|-------|------|
| `frontend/src/types/index.ts` | **Kaveen** | If Aloka/Nadija need a new type, ask Kaveen to add it and push to main |
| `backend/api/routes.py` | **Aloka** | Kaveen should NOT edit route logic; only Aloka merges to this file |
| `backend/main.py` | **Kaveen** (setup) → **Aloka** (routes) | Kaveen sets up FastAPI app; Aloka adds router includes |
| `backend/ai_pipeline/mock_pipeline.py` | **Nadija** created → **Nadija** replaces with real pipeline | Do NOT delete until Nadija's real pipeline is tested |
| `requirements.txt` | **Aloka** owns, others submit PRs | One file for all Python deps |
| `package.json` | **Kaveen** owns | Only Kaveen adds npm packages |

---

## Merge Protocol (How to Merge Without Pain)

### When to Merge to `main`

Merge to `main` when a **phase is complete and tested**, not after every commit.

```bash
# Example: Aloka finished Phase 02 (Mock API Endpoints)
git checkout feat/reasoning
git add backend/api/routes.py
git commit -m "feat(api): Phase 02 - all 7 mock endpoints with realistic data"
git push origin feat/reasoning

# Open a Pull Request on GitHub: feat/reasoning → main
# Other members review (just a quick look, not gate-keeping)
# Merge to main
# Everyone pulls main next morning
```

### Resolving Merge Conflicts

The most common conflict will be in `backend/api/routes.py`. Here's how to handle it:

```bash
# You're on your branch, trying to merge main:
git merge main

# If conflict in routes.py:
# Git will show <<<<<<< HEAD (your changes) and >>>>>>> main (their changes)
# Open the file, keep BOTH sets of routes, remove the conflict markers
# Example: Your route + Aloka's route → both should exist

git add backend/api/routes.py
git commit -m "merge: resolve routes.py conflict - keep both endpoints"
```

---

## Hackathon-Specific Rules (Critical for Evaluation)

> Per CodeSplash'26 guidelines: *"Squashed, batched, or single-author commit histories may be questioned."*

### ✅ DO This

```bash
# Small, frequent, descriptive commits under your own account
git commit -m "feat(ai): Phase 03 - document classifier with 7 document types"
git commit -m "feat(ai): Phase 03 - add classification confidence threshold 0.95"
git commit -m "fix(ai): Phase 03 - fix confidence normalization for multi-page docs"
```

### ❌ NEVER Do This

```bash
# One giant commit at the end
git add .
git commit -m "all my work"   # ← Judges will question this

# Committing as another person (using their terminal)
# Each person must commit from their own machine with their own GitHub login
```

### Commit Message Format

Use this format so the history is clean for judges:

```
feat(module): Phase XX - short description

Examples:
feat(ai): Phase 02 - PaddleOCR integration with bbox output
feat(reasoning): Phase 04 - knowledge graph with NetworkX
feat(frontend): Phase 07 - PDF viewer with bbox overlay
fix(api): Phase 14 - fix discrepancy endpoint null handling
chore(deps): add vis-network to package.json
docs: update README setup instructions
```

---

## Emergency: Late Integration Rescue Plan

If you reach Day 4-5 and branches haven't been merged:

```bash
# Step 1: Freeze everyone's branches (no new commits)
# Step 2: Aloka merges reasoning to main first (backend must be stable)
git checkout main && git pull
git merge feat/reasoning
git push origin main

# Step 3: Kaveen rebases frontend onto latest main
git checkout feat/frontend
git rebase main    # Brings in all backend changes
# Fix any conflicts
git push origin feat/frontend --force-with-lease

# Step 4: Nadija merges ai-pipeline
git checkout main && git pull
git merge feat/ai-pipeline
git push origin main

# Step 5: All members pull main and do final integration test
git checkout main && git pull
```

---

## Summary: The 3 Rules That Prevent All Problems

> **Rule 1 — Shared contracts on `main` first.** Types, interfaces, mock data, and API stubs are committed to `main` before anyone branches. Never define these inside a personal branch.

> **Rule 2 — Pull from `main` every morning.** Before writing any code, `git checkout main && git pull && git checkout your-branch && git merge main`. Takes 30 seconds and prevents hours of merge conflict pain.

> **Rule 3 — One owner per shared file.** `routes.py` = Aloka. `types/index.ts` = Kaveen. `requirements.txt` = Aloka. `package.json` = Kaveen. If you need to touch someone else's file, coordinate first on WhatsApp and commit together.
