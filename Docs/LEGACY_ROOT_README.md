# Ants — your hackathon workspace

A complete React + TypeScript app for Team Ants to save future hackathons, track applications, divide the work, and keep important links together.

## Start

```sh
npm install
npm run dev
```

Open the local URL printed by Vite. The app works immediately in local mode; it does not require an account or a working database. Existing `ants_team_demo_v1` browser data is retained.

```sh
npm test          # Data integrity and Postgres/RLS integration checks
npm run build    # TypeScript check and optimized production build
npm run preview  # Preview dist/
```

## What is included

- Dark launchpad with lime accents, top navigation, a next-event game plan, immediate tasks, and a deadline timeline.
- Hackathon create/edit/delete; stages, priority, application deadline, event date, lead, prizes, requirements, notes, and official links.
- Discover / Prepare / Compete / Results pipeline, plus card and list views with stage/priority filters. Open any opportunity to update its stage.
- Tasks linked to hackathons with assignees, due dates, completion, and filters.
- Calendar with application deadlines, event days, and task dates. Small screens use a readable monthly agenda. Export `.ics` files to a calendar app.
- Resource library for repositories, pitch decks, documents, videos, and application links.
- Global search with Ctrl/Command + K.
- JSON backups, validated local restore, CSV export with spreadsheet formula protection.
- Native accessible dialogs, keyboard dismissal/focus restoration, mobile navigation, and reduced-motion support.
- Supabase email sign-in, private workspace creation/joining, high-entropy invitation codes, and atomic local-to-cloud import.

The sample events are examples carried over from the original project. Their registration dates and eligibility have **not** been verified. Replace them with confirmed event details or choose **Team & settings → Start a fresh local workspace**.

## Turn on private team syncing

1. Create or restore a working Supabase project. Set `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` in `.env.local` (copy the structure from `.env.example`). Never use a service-role or secret key in the browser.
2. Run `supabase/schema.sql` in the project's SQL Editor. This is an additive, repeatable setup transaction: it creates the `ants_*` tables and does **not** drop or modify legacy tables.
3. Enable email authentication. Add the app's exact URL to the Supabase Auth redirect allowlist, including your local URL for development.
4. Restart Vite after environment changes. In **Team & settings**, request a sign-in link using your own email, then create your workspace.
5. In an empty cloud workspace, use **Copy local data to this team** to copy your local hackathons/tasks/resources in one atomic database operation. Original local data is retained. IDs are remapped while preserving associations.
6. Give teammates the invitation code privately. Each teammate signs in with their own email and selects **Join a team**.

Each account currently belongs to one workspace. Members can edit/delete shared records; roles are descriptive except that membership creation is restricted to the guarded create/join functions. Changes made by other members appear when you press **Refresh** or reload the app. Background notifications and automatic real-time syncing are not implemented.

Local and cloud workspaces are intentionally separate. Local storage is specific to the browser **and URL origin** (`localhost` and `127.0.0.1` are different stores). Clearing browser data deletes local records. Use JSON backups before moving devices or resetting.

## Database design

`ants_workspaces`, `ants_members`, `ants_competitions`, `ants_tasks`, and `ants_resources` have RLS enabled. Anonymous users have no table access. Policies require actual membership, and compound foreign keys prevent linking tasks or resources across workspaces. Membership writes occur only inside explicit authenticated create/join functions. Privileged functions live in `ants_private`, which should never be exposed as a Data API schema. Deleting a hackathon unlinks its tasks and resources without deleting them.

If the old public tables were previously deployed with RLS disabled, this new schema does not silently change them. Export their data first; then retire their public grants separately. The rebuilt app never reads or writes those tables. There is no automatic migration from the old public database. Local JSON data can be restored and imported using the UI.

Reference: [Supabase row-level security](https://supabase.com/docs/guides/database/postgres/row-level-security), [email magic links](https://supabase.com/docs/guides/auth/auth-email-passwordless).

## Verification and current setup status

- Production build and TypeScript pass.
- `tests/model.mjs` checks malformed backups, duplicate IDs, invalid dates, missing relationships, safe URL handling, CSV injection protection, date boundaries, and calendar export.
- `tests/database.mjs` runs the real schema twice against an isolated PGlite Postgres engine, then checks separate owners/members, cross-team data isolation, denied inserts/updates, membership escalation, invalid invites, linked deletion behavior, local import, and anonymous access denial.
- Browser checks covered creating/editing hackathons, persisted reloads, dates, linked tasks, task completion, stages, linked resources, unsafe URL rejection, calendar export, and mobile navigation/agenda.
- The pre-existing configured Supabase REST endpoints returned HTTP 404 during inspection. No production database schema was applied, no live emails were sent, and hosted sign-in/sync still need the setup above. No deployment was published.

## Deploy

Deploy `dist/` to any static host after `npm run build`. The existing Vercel rewrite configuration supports serving the app. Configure your current Supabase public environment values at build time, and add the deployed URL to the authentication redirect allowlist.

## Source map

- `src/App.tsx`: navigation, overview, hackathons, tasks, resources, details.
- `src/Editor.tsx`, `src/ui.tsx`: validated editing and shared UI primitives.
- `src/Calendar.tsx`, `src/Team.tsx`: calendar, account, invitations, backups.
- `src/useWorkspace.ts`, `src/db.ts`: persistence, authentication, database access.
- `src/model.ts`: pure data operations, validation, and exports.
- `src/data.ts`: shared types and existing starter content.
- `src/style.css`: responsive design system.
- `supabase/schema.sql`: non-destructive private database setup.
