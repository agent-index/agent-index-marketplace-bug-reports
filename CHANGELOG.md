# Changelog

## [1.5.0] — <RELEASE_DATE> — bug platform: follow forwarded bugs to the fix

Pairs with the log collector's bug platform (agent-index project `bug-admin-platform`). Older log servers keep working: the new checks and status calls are skipped when the server doesn't offer them.

### Added
- **`my-bugs` (skill 1.0.0):** "show my bugs" — a member's own bugs with the org's status and agent-index's status, note, open question and fix version, as last synced by the admin's `view-bugs`; members answer questions here, and `view-bugs` sends the answers. Members never read the org's log-server key or call the log server (decision 50). Own bugs only (decision A). This is a view, not a storage boundary: like every version since 1.3.0, the bug log is readable by all members.
- **`apps/upstream.py`:** key check, status, claim and reply calls to the log server (standard library; keys, tokens and texts read from files, never the command line).
- **Tutorial topic "What happens after a bug is forwarded"** (bug-reports-tutorial 1.2.0).

### Changed
- **forward-bug 1.3.0:** sends member hashes only — no names or email addresses — and tells the admin the bug text goes as written (decision B); adds `client` and the org's versions (`environment`); saves agent-index's reference and status token in the bug file (`upstream:`); checks the key with the server first and **never offers the community key to an org on an enterprise key** (bug platform finding 2).
- **view-bugs 1.4.0:** claims older forwarded bugs once (by server reference and org hash), fetches agent-index's status for every forwarded bug and saves it, shows "fixed in X, your org has Y", offers (never forces) to close fixed bugs, and lets admins answer agent-index's questions.
- **Admin access with no org roles (view-bugs, forward-bug):** org admins (org-config `admins[]`) always have access, and with `admin_roles` empty only they do — as collection setup already said. Read literally, both refused every member when `admin_roles` was empty (found in the bug platform's Phase 0 test, ms_install_9).
- **Bug log addressed by id on Google Drive (report-bug 1.2.3, update-bug 1.0.3, view-bugs, forward-bug, my-bugs):** every read, list and write under `bug_log_path` now goes through `id:{shared_root}/…` on Google Drive. These tasks used the bare `/shared/bug-reports/…` path, so a member outside the Shared Drive couldn't file or update a bug at all (`BACKEND_ERROR: File not found`). Found in the bug platform's Phase 0 test, Dev One member four (finding 38). OneDrive is unchanged.
- **Bug titles reach the index:** report-bug 1.2.3 writes `title` in the bug file's frontmatter, and view-bugs takes the first `## ` heading when an older file has none. Before this, reconcile indexed every member-filed bug with a null title (Phase 0, Dev One admin). report-bug's confirmation now points members at `@ai:my-bugs`.
- **`org_hash` is the org's `org_uuid` (forward-bug, view-bugs):** forward-bug only said "the org's identifier hash", and org-config has no such field, so agents computed different values (bug platform finding 41). A hash of the org name (core's install-log rule) was tried first, but two orgs with the same name collided (finding 54), so 1.5.0 sends `org_uuid` as written. view-bugs' one-time claim of older forwards also tries the legacy name hash, so forwards from before 1.5.0 still link.
- **forward-bug finds bugs the index hasn't caught up with:** it lists bug files missing from `bug-manifest.json` (report-bug never writes the manifest), reads a named bug from its file, and adds the manifest entry when it forwards one (bug platform finding 45).
- **my-bugs and update-bug match the member on `reporter.member_hash`:** both said `reporter_hash`, a field the manifest doesn't have, so read literally a member's own bugs never matched (bug platform finding 49).
- **forward-bug sends the reporter's updates:** `### Reporter Updates` entries (from update-bug) go with `additional_context`, dated, without names. Before this they were silently left out (bug platform finding 52).
- **Collection setup 1.2.0:** checks the log-server key with the server ("Key accepted: enterprise, {org}") and records its tier; runs the key check with the collection's own `apps/upstream.py` (read to a temporary file, since members' apps aren't synced yet at setup time); writes a `log_server_auth_key: stored in …` placeholder so updates stop reporting a missing value (dev_source_2 FINDINGS 102).

### Upgrade
- Setup changed, so after upgrading the admin runs `@ai:install-collection bug-reports` once and keeps the current key. Nothing else to do; older forwarded bugs get their agent-index status the next time an admin opens `@ai:view-bugs`. `@ai:update` brings members' installed bug-reports skills to 1.5.0 but doesn't add new ones: a member adds `my-bugs` by saying `@ai:setup` (bug platform finding 36).

## [1.4.5] — 2026-11-10 — setup reads org-config and writes its responses by backend

Pairs with core 4.1.1 (Kallista Salak, bug-reports#6, CI-019).

### Fixed
- **Collection setup reads `org-config.json` by backend:** Google Drive `id:{org_config_id}`, OneDrive `/org-config.json`. A bare path returned not found for an admin outside the Shared Drive.
- **Collection setup writes `collection-setup-responses.md` to this collection's own `setup/` folder** (Google Drive `id:{folder_id}/setup/`, OneDrive `/bug-reports/setup/`). It said `/setup/`, a folder at the drive root.

## [1.4.4] — 2026-10-17 — standards.md citations re-pointed

Pairs with core 4.1.0, which retires `standards.md`: forward-bug 1.2.2, report-bug 1.2.2, update-bug 1.0.2, view-bugs 1.3.2 and their setup files cite core `runtime-reference.md` § "Addressing: Owned Content and Sharing" for the backend read rule (finding 63). No behaviour change.

## [1.4.3] — 2026-10-17 — setup-responses format

### Fixed (4.0.1 pass — OneDrive and Google Drive live tests)
- Setup writes its responses in the canonical setup-responses format; the tutorial's empty responses file carries the canonical sections and the collection-qualified install path (finding 14).
- **OneDrive reads org-config, the registry and the setup responses by path** (report-bug 1.2.1, update-bug 1.0.1, forward-bug 1.2.1, view-bugs 1.3.1 and their setup checks); the id-only rules are gdrive-only (finding 63).

## [1.4.2] — 2026-10-13 — reconfigure keeps bug data

### Fixed
- **A reconfigure no longer resets `bug-manifest.json` or `auth-key.txt` (`reconfigresetsdata`, Dev Two live test finding 30).** Setup writes the empty manifest only when none exists, and keeps the existing log-server key unless the admin enters a new one. Bug files were never deleted, but the index was reset to `bugs: []` and an enterprise key was replaced by the community default.

### License
- Proprietary, as before: `LICENSE` added and the `collection.json` `license` field set to `proprietary` (it said `open`).

## [1.4.1] — 2026-10-13 — collaborative-acls description

### Changed
- **`collaborative-acls.json`** description: grants are provisioned through the core permission-changes procedure (agent-index-core 3.32.0 / marketplace 2.22.0) instead of the retired permission-change-helper. No behaviour change. Part of retiring the helper (design record: `/shared/projects/core-improvements/artifacts/retire-permission-helper-*.md`).
- **Setup: org roles are optional (`bugrolesprereq`, found in the 3.32.0 live test).** With no org roles, `admin_roles` is empty and only org admins triage. Before, setup called roles a hard prerequisite, contradicting core create-org.
- Originally staged on `channel/dev-1` as 1.3.3; re-staged as 1.4.1 on top of the 1.4.0 hotfix (failed-forward recovery), which shipped from `main` first.

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
