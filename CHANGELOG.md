# Changelog

## [1.4.0] — 2026-10-06 — failed-forward recovery (log-server outage follow-up)

### Context

The agent-index log server rejected **every** submission from 2026-07-11 to 2026-10-05: its API-key config was deleted by an S3 lifecycle rule, and the server answered `403 invalid API key` instead of a server error. `forward-bug` ≤1.1.0 recorded nothing on failure and told admins "The API key may be invalid or expired. Contact your org admin to update the key" — so failed forwards left no trace, and some admins may have changed a key that was correct. The server is fixed (it now returns `503` when it can't load its key config, and is monitored). This release makes the client side recoverable.

### Added

- **`forward-bug` 1.1.0 → 1.2.0: failed attempts are recorded on the bug** — `forward_failed_at`, `forward_last_error`, `forward_attempts` in frontmatter, an admin note, and `forward_failed_at` on the manifest entry. Status is left unchanged. Cleared on the next successful forward.
- **"retry failed forwards"** — new trigger; `forward-bug` leads with pending retries and resends them as one confirmed batch, stopping at the first auth/network failure.
- **Outage-window notice** — once per session, `forward-bug` points out unforwarded open/acknowledged bugs reported 2026-07-01..2026-10-05 and offers to review them (never auto-forwards).
- **Default-key check** — if `{bug_log_path}/config/auth-key.txt` differs from `log_collector_api_key` in `agent-index.json`, `forward-bug` says so and offers to restore the community key (enterprise keys are legitimate, so it never forces it).
- **`view-bugs` 1.2.0 → 1.3.0** — reconcile carries `forward_failed_at` into the manifest; summary and list flag failed forwards; new "show bugs that failed to forward" filter.

### Changed

- **`apps/forward-bug.py`: classified exit codes** — `1 local`, `2 auth` (401/403), `3 server` (5xx), `4 network`, `5 payload` (413/other 4xx); stderr is one `"<class>: <detail>"` line. Previously every failure was exit 1.
- **Transient failures are retried** twice (5s, 15s backoff) for 5xx and network errors. `--no-retry` disables this.
- **Error messages:** a 5xx/network failure now explicitly says it is *not* a key problem and not to change anything; only an `auth` failure points at the key, and it points at the specific file to compare rather than "contact your admin". New directive: never advise a key change for server/network failures.

### Notes

- `collection.json` 1.3.2 → 1.4.0 (hotfix from main; the docs-only 1.3.3 staged on `channel/dev-1` re-stages on top as 1.4.1); all API manifests' `collection_version` → 1.4.0.
- **Also ships CI-010 (PR #1, merged unversioned):** `forward-bug`, `view-bugs`, `report-bug`, `update-bug` and their setup templates read org-config, the members registry and collection setup by id anchor instead of bare path (bug `20260921-8d20ea22-185412-c4e7`).
- No schema migration: the new frontmatter fields are optional and absent on existing bugs. No ACL changes.
- **After upgrading, admins should run `@ai:forward-bug`** — the outage notice will list bugs from the affected window.

---

## [1.3.2] — 2026-06-06 — fleet docs hygiene (post-audit sweep)

### Fixed (docs only)

- README no longer claims report-bug "updates the manifest index" — the index is admin-rebuilt by view-bugs (reconcile-on-read, accurate since 1.2.0).
- Tutorial visibility wording: the bug log is an open commons every member can read (with attribution), not an admins-only surface.
- Tutorial setup template disambiguates the install path as the LOCAL workspace via native file tools (deprecated remote `/members/` spaces are not involved).
- All capability manifests re-stamped with the correct `collection_version` (preflight Check 2 compliance).

## [1.3.1] — 2026-06-01

### Fixed

- **Removed the broken `config/` restriction entry from `collaborative-acls.json`.** The 1.3.0 entry tried to hide `config/auth-key.txt` from members with `{op: share, recipient: all@, role: reader, inherit: false}`. That is the wrong primitive: an `op: share` can only *add or re-assert* a grant for its recipient — it can never *remove* `all@`'s access. Discovered live during dev_install provisioning (the op terminated without effect; `all@` remained a reader on `config/`). The `bugs/` writer grant (the actual non-admin-write feature) is correct and unaffected. The `config/` auth-key hardening — which requires disabling inheritance and granting **only admins** (dropping `all@`), not a share — is tracked separately as bug `20260601-8d20ea22` and will ship as its own properly-rehearsed change.

### Notes

- `collection.json` 1.3.0 → 1.3.1. Per-capability manifest `collection_version` reconciles to 1.3.1 on members' next `apply-updates` (manifest-sync subroutine). No capability `.md`/logic changes in this patch — `collaborative-acls.json` only.

---

## [1.3.0] — 2026-05-31

### Fixed

- **Non-admin members can now file and update bugs** (closes bug `20260531-8d20ea22`). Under the least-privilege access model (core 3.1.0+), non-admin members are reader-only on `/shared`, so `report-bug` — explicitly an every-member task — failed at the `aifs_write` to `/shared/bug-reports/bugs/` for everyone except the admin, and misreported the permission failure as an auth/connectivity problem. This release closes that gap.

### Added

- **`collaborative-acls.json`** (new, collection root) — declares the ACLs the collection needs: `all@{domain}` **writer** on `bugs/` (additive, `inherit:true`) and an `inherit:false` reader restriction on `config/` so the log-server auth key is no longer member-readable. Provisioned by the admin at install time via `install-collection` Step 5.5 (agent-index-marketplace 2.1.0), routed through `permission-change-helper` — never `aifs_share` directly. Requires `permission-helper-go ≥ 0.3.0` for the `config/` restriction.
- **`update-bug` task** (new, 1.0.0) — member-facing, ownership-enforced: a member may revise or add detail to a bug **they reported**. Status changes remain admin-only (`view-bugs`). Ownership is enforced in task logic (folder-level writer grant; soft boundary — documented in the task).

### Changed

- **`report-bug` 1.1.0 → 1.2.0:** collision-free IDs (`{date}-{hash8}-{HHMMSS}-{4hex}`) generated without reading shared state; **no longer writes `bug-manifest.json`** (the index is rebuilt by `view-bugs` reconcile-on-read, shipped in 1.2.0); authorization-specific error message that directs members to ask an admin to run `@ai:install-collection bug-reports` rather than the wrong `@ai:member-bootstrap` path. `writes_to` narrowed to `/shared/bug-reports/bugs/`.
- **`view-bugs`** unchanged in behavior — its 1.2.0 reconcile-on-read already makes the member-never-writes-the-manifest model work.

### Notes

- `collection.json` 1.2.0 → 1.3.0; all API manifests' `collection_version` → 1.3.0.
- **Provisioning is an admin action** and requires an interactive `permission-change-helper` Accept. After upgrading, the admin runs `@ai:install-collection bug-reports` once to provision member write access (idempotent; safe to re-run as backfill). Until provisioned, non-admins still cannot write — no regression vs. prior behavior, but now with a clear error message.

---

## [1.2.0] — 2026-05-13

### Fixed

- **`view-bugs` 1.1.0 → 1.2.0: always reconciles `bug-manifest.json` from individual bug files on read** (closes bug `20260513-8d20ea22`). Pre-1.2.0 trusted the manifest as a cache; in practice writers (this skill's own status-update path, `report-bug`, ad-hoc edits via other sessions) didn't reliably keep the manifest in sync with the per-bug files. Result: a session reading the manifest could miss recently-added bugs and see stale `status` values for resolved ones — observed live on 2026-05-13 where the manifest reported 10 "open" when reality was 0. New Step 2 in view-bugs reconciles before rendering: list `{bug_log_path}/bugs/`, read each `.md`, parse frontmatter, rebuild the canonical bugs list, diff against the on-disk manifest, write back if different. Cost: bounded N reads per invocation (10-50 for typical installs).

### Notes

- `view-bugs` skill version bumped 1.1.0 → 1.2.0. All API manifests' `collection_version` bumped 1.1.1 → 1.2.0.

---


## [1.1.1] — 2026-04-19

### Added
- **Natural language trigger phrases in `collection.json`.** API entries now include trigger arrays that map conversational phrases to capabilities, powering the routing layer introduced in agent-index-core 3.0.5. Members can say things like "report a bug" or "show bugs" instead of using `@ai:` alias syntax. Triggers are customizable per-member via `routing.json`.

## [1.1.0] — 2026-04-02

### Added
- `bug-reports-tutorial` skill — explains bug-reports collection concepts, workflows, member reporting, and admin triage process

## [1.0.0] — 2026-04-01

### Added
- `report-bug` task — member-facing bug submission with guided interview
- `view-bugs` skill — admin interface for browsing, filtering, and triaging bugs
- `forward-bug` task — forward bugs to the agent-index log collection server
- Collection setup with configurable admin roles, severity levels, and log server endpoint
- Shared markdown bug log with YAML frontmatter and JSON manifest index
- Python forwarding script (`forward-bug.py`) for HTTP delivery to log collector.
