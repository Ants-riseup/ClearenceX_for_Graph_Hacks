# Competition release readiness

Updated 18 October 2026, Asia/Colombo. This is a local release record, not a submission receipt or a guaranteed score.

## Completed locally

- Rewritten competition-focused README with Track 01, actual graph-dependent behavior, architecture, setup, security, evaluation and limitations.
- Judge guide, submission draft, concrete manual acceptance checklist and existing/new-work disclosure.
- Cross-platform setup generates private database credentials and preserves existing configuration.
- GitHub Actions workflow added for isolated backend/frontend tests, build, lint and source packaging. Remote execution is not yet verified.
- Ten fresh acceptance dossiers/twenty questions and a frozen, cost-bounded first model comparison: **19/20 graph versus 13/20 flat**, $0.0455048 estimated. The failure is retained.
- Fresh selected backend suite: **79 passed, 1 skipped**, one existing Starlette/httpx deprecation warning, 145.33 seconds. The skip is the Windows stdio case; retained packaged Linux MCP evidence is separate.
- Fresh frontend suite: **29 passed**. TypeScript/Vite production build passes; no main-chunk size warning. Lint has no errors and nine existing React warnings.
- Source packaging explicitly includes the new company backend, admin page, tests, evaluator, workflow and submission documentation. It excludes private configuration, credentials, PDFs, caches and backups and verifies archived SHA-256 hashes.

## Final external/human gates

| Gate | Status |
|---|---|
| Current reviewed source publicly available and links verified signed out | Not established; local packaging/versioning does not prove publication |
| Actual working demo video | Pending human recording; use DEMO.md |
| Full visual/keyboard/mobile walkthrough | Pending; browser security layer denied automation |
| Registration, actual team and submitted tracks | Team confirmation required; documentation explicitly focuses Track 01 |
| Reuse eligibility and event-time contribution | Team/organizer confirmation required; inherited work disclosed |
| Data/assets licensing and publication rights | Team review required; private PDFs excluded from the release |
| Official submission and confirmation | Not performed |

Do not publish the existing Git history without checking it: supplied PDFs and environment files were previously tracked. The reviewed source archive provides a clean current-source boundary without those files, but does not erase older history. Replace any exposed provider credentials before sharing/deployment.

The first-run comparison still has a repeated-correction reasoning failure; deterministic graph state/impact remains tested. It would be misleading to label this release 10/10 or the whole roadmap complete. General OCR, official customs validation and later memory/Company Brain/production features retain their documented scope.
