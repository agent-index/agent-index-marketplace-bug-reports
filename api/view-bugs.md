---
name: view-bugs
type: skill
version: 1.4.0
collection: bug-reports
description: Interactive admin interface for viewing, filtering, and triaging bug reports. Admins can browse all submitted bugs, update status, add notes, select bugs for forwarding, and (1.4.0) see what agent-index is doing with forwarded bugs — status, notes, questions to answer, and the release that fixes them.
stateful: true
always_on_eligible: false
dependencies:
  skills: []
  tasks: []
external_dependencies:
  - Remote filesystem access
---

## About This Skill

View Bugs is the admin-facing interface for bug reports. It reads the shared manifest and individual bug files from the remote filesystem, presents bugs in a filterable summary view, and lets admins update status, add notes, and mark bugs for forwarding. Only members whose org role matches the configured `admin_roles` can use this skill.

**1.4.0 (bug platform).** For bugs the org has forwarded, View Bugs also shows agent-index's side: the **upstream status** (submitted, in review, needs more information, accepted, fixed — waiting for release, fixed and released, or closed as won't do / duplicate / can't reproduce / works as intended), the note agent-index wrote for the org, any question waiting for a reply, and the release with the fix compared with what the org runs. It fetches this from the log server each time it runs and saves it in the bug files. Orgs are not notified of changes; this is where they see them. Members follow their own bugs with `my-bugs`.

---

## Directives

### Invocation

When the member invokes this skill:

1. **Check admin access.** On gdrive, resolve both reads by id anchor, never by bare path (OneDrive: read `/org-config.json`, `/bug-reports/setup/collection-setup-responses.md` and `/members-registry.json` by path instead — a bare `id:` resolves against the caller's own drive there; backend from local `agent-index.json` `remote_filesystem.backend`; core runtime-reference.md § "Addressing: Owned Content and Sharing", finding 63): read `org_config_id` from the local `agent-index.json` (`remote_filesystem.connection.org_config_id`) and read org-config via `aifs_read("id:{org_config_id}")`; take the `bug-reports` entry's `folder_id` in `installed_collections[]` and `resource_ids.members_registry`. Read `aifs_read("id:{folder_id}/setup/collection-setup-responses.md")` to get `admin_roles` and `bug_log_path`. Read the members registry via `aifs_read("id:{members_registry}")` and look up the current member's `org_role`. On gdrive, do not read `/org-config.json`, `/members-registry.json`, or `/bug-reports/...` by bare path — for a non-Shared-Drive member they return FILE_NOT_FOUND or resolve to the same-named `/shared/bug-reports` data folder (`memberdupcollfolders`/`nameambig`; bug `20260921-8d20ea22-185412-c4e7`); if any id is missing, halt and name it rather than falling back. Access is granted when the member's `org_role` is in `admin_roles`, **or** the member is an org admin (their member hash is in org-config `admins[]`); when `admin_roles` is empty, only org admins have access (1.4.0; matches collection setup — before this, an org with no roles locked out its own admins). Otherwise respond: "Bug report admin access is restricted to {admin_roles or 'org admins'}. You can submit bugs with '@ai:report-bug'." and exit.

1a. **Resolve the bug log location — `{bug_log}` (1.5.0, bug platform finding 38).** `bug_log_path` is an org path such as `/shared/bug-reports/`. On gdrive, address it through org-config's `resource_ids.shared_root`: `/shared/{rest}` becomes `id:{shared_root}/{rest}` (no trailing slash), and every `{bug_log}/...` read, list and write in this file uses that id anchor. Never use the bare `/shared/...` path on gdrive: for a member outside the Shared Drive it fails with `BACKEND_ERROR` / `FILE_NOT_FOUND` (core runtime-reference.md § "Addressing: Owned Content and Sharing", `memberpathreads`). If `shared_root` is missing, halt and name it. On OneDrive, `{bug_log}` is `bug_log_path` as written, without the trailing slash.

2. **Load and reconcile the manifest.** (Reconcile-on-read added in v1.2.0; closes bug `20260513-8d20ea22`.) The manifest is a denormalized cache of the individual bug files under `{bug_log}/bugs/*.md`. Writers (this skill's status-update path, `report-bug`, ad-hoc edits via other sessions) are supposed to keep both in sync, but in practice the manifest drifts: new bug files don't get inserted, status changes on individual files don't get reflected in the manifest. Trusting the manifest blindly produces stale reports — a known bug.

   To prevent this, view-bugs **always reconciles before rendering**:

   1. `aifs_list("{bug_log}/bugs/")` to enumerate every `.md` file.
   2. For each, `aifs_read("{bug_log}/bugs/{filename}")` and parse the YAML frontmatter (id, title, collection, severity, status, reporter, reported_date, forwarded_date, closed_date, forward_failed_at). `forward_failed_at` (1.3.0) is set by `forward-bug` 1.2.0+ when a forward attempt fails and cleared when one succeeds; carry it into the manifest and treat a mismatch on it like a status mismatch. Files written by report-bug before 1.2.3 have no `title` key: use the text of the first `## ` heading in the body instead (finding 38b).
   3. Build the canonical bug list from those individual files. This is the authoritative source.
   4. `aifs_read("{bug_log}/bug-manifest.json")` (best-effort; tolerate missing/corrupt — treat as `{ bugs: [] }`).
   5. Diff the canonical list against the manifest's `bugs` array. If they differ in any way (missing entries, extra entries, status mismatches, title mismatches): rebuild the manifest from the canonical list and write it back via `aifs_write("{bug_log}/bug-manifest.json", ...)`. Set `last_updated` to the current ISO timestamp.
   6. Surface a one-line notice if a reconcile actually rewrote the manifest: "Reconciled bug-manifest.json — {N_added} added, {N_status_changed} status changes, {N_removed} removed from manifest." (Suppress this notice in the cleanly-aligned case.)

   **Cost.** One `aifs_list` plus N `aifs_read` calls per view-bugs invocation, where N is the bug count. For a typical install with 10–50 bugs, that's bounded and fast (parallel reads finish in 1–3 seconds). View-bugs runs interactively so the cost is acceptable.

   **Failure tolerance.** If individual file reads fail (network, malformed frontmatter), still attempt to render from the partial reconciliation and surface the failures. Do NOT write a half-reconciled manifest back — leave the old manifest in place if any read failed, surface the issue, ask the admin to retry.

   Proceed with the reconciled bugs list (in memory) for the rest of this skill's operations.

2b. **Sync with agent-index (1.4.0).** Only for bugs with `forwarded_date` set. Read `log_server_url` from the setup responses and the key from `{bug_log}/config/auth-key.txt` (`aifs_read`); write the key to a temporary local file (native Write), delete it at the end of this step.

   1. **Claim older forwards** (decision 2). Bugs forwarded before 1.5.0 have a "Server reference: {id}" line in their Admin Notes but no `upstream.token`. Collect those references (at most 200), write them as a JSON list to a temporary file, and run:
      ```bash
      python {apps_path}/upstream.py --server-url "{log_server_url}" --key-file "{temp_key}" claim --org-hash "{org_hash}" --ids-file "{temp_ids}"
      ```
      `org_hash` is org-config's `org_uuid`, as in `forward-bug` Step 5 (findings 41, 54). **Older forwards carry an older org value.** Before 1.5.0, agents computed it in different ways (prod holds all three shapes below). So for the ids still in `not_claimed`, run the claim again with each legacy value in turn, stopping once none are left: (1) `"sha256:"` + the first 16 hex characters of SHA-256 of the lowercase org name (core upload-install-log's rule); (2) the same 16 hex characters without the prefix; (3) the lowercase org name itself; (4) org-config's `org_id`. Treat ids claimed on any call like the first. Only ids no call claims are `not_claimed`. A claim also needs the bug's own reference, so trying these values can't take another org's bug (findings 54, 58). For each `claimed` entry, add to that bug's frontmatter `upstream: {id, token, status: submitted, synced_at}` (the full block shape is in `forward-bug` Step 8). For each `not_claimed` id, set `upstream: {id, status: "unlinked", synced_at}` and list it once: "{n} older forwarded bug(s) couldn't be linked to agent-index — if you need their status, contact agent-index support with the reference." Bugs forwarded during the 2026 outage were never received; they show as unlinked, which is correct.
   2. **Fetch status.** For every bug with `upstream.token`, build `[{"id": upstream.id, "token": upstream.token}]` (at most 200 per call), write it to a temporary file, and run `upstream.py … status --bugs-file "{temp_bugs}"`. For each answer:
      - `found: true` → copy `status`, `org_note`, `question`, `fix_repo`/`fix_version`/`released_at` (into `upstream.fix`), `duplicate`, `content_deleted` into the bug's `upstream` block, set `synced_at`, and write the bug file back **only if something changed**. Mirror `upstream_status`, `upstream_open_question` (true when `question` is set) and `upstream_fix_version` into the manifest entry.
      - `found: false` → leave the saved values; mark the bug "not found at agent-index" in the display (usually a deleted bug or a key change).
   2a. **Send members' answers** (decision 50: members don't hold the key). In each bug file with `upstream.token`, find `### Replies` lines ending "(to send)". For each one, write the token and the answer text to temporary files and run `upstream.py … reply --id "{upstream.id}" --token-file … --member-hash "{reporter.member_hash}" --text-file …`. On success, change that line's ending to "(sent to agent-index)" and write the file back. On 404 or 409, end it with "(not sent: agent-index no longer accepts replies on this bug)". On 2/3/4, leave it for next time. Say once: "Sent {n} member answer(s) to agent-index." Then fetch status (step 2) again for those bugs, so the list shows the new status.
   3. **If the server can't be reached** (exit 3/4) or is older than 1.5.0 (exit 5 with 404): don't change any file; show saved values with "(as of {synced_at})", and say once "Couldn't reach agent-index just now — showing the last saved status." Exit 2 (`auth`): "The log server didn't accept this org's key" and continue without sync.
   4. Delete all temporary files.

   **Version comparison** for bugs with `upstream.status: fixed-released` (decision 7). For a collection repository (`agent-index-marketplace-<name>` or any repo whose collection is in org-config `installed_collections[]`), the org's version is that entry's `version`; for `agent-index-core` and adapters, `/shared/dist/manifest.json` `sources[fix.repo].version`. Compare as semantic versions:
   - org version lower → "Fixed in {repo} {version}; your org has {org_version}. An admin can publish updates to get it."
   - equal or higher → "Fixed in {version}; members get it with @ai:update."
   - unknown (not installed, no dist manifest) → "Fixed in {repo} {version}."
   Known limit: for core and adapters the dist manifest can name a version slightly before the org has actually published it (FINDINGS 100).

3. **Show summary.** Display a summary of the current bug log:
   - Total bugs: {count}
   - Open: {count} | Acknowledged: {count} | Forwarded: {count} | Closed: {count}
   - By severity: Critical: {n}, High: {n}, Medium: {n}, Low: {n}
   - Most recent: "{title}" ({id}, {severity}, {reported_date})
   - If any open/acknowledged bug has `forward_failed_at`: "⚠ {N} bug(s) failed to forward to agent-index — say 'retry failed forwards' to resend." (Routes to `forward-bug`.)
   - **1.4.0:** if any forwarded bug has `upstream.question`: "❓ agent-index asked about {N} bug(s) — say 'answer agent-index' to reply." List these first.
   - **1.4.0:** if any forwarded bug is `fixed-released` and still open locally: "✓ {N} forwarded bug(s) are fixed and released" with the version message, and offer to close them locally (never close without the admin saying yes).

4. **Ask what the admin wants to do.**

### Supported Operations

**List bugs (with filters)**
Show all bugs, or filter by status, severity, collection, or reporter. For each bug, display: ID, title, collection, severity, status, reporter display_name, and reported date. Append "⚠ forward failed" to any bug with `forward_failed_at`. **1.4.0:** for forwarded bugs append the upstream status in plain words ("agent-index: in review", "agent-index: fixed in 1.5.0"), `❓` when a question is waiting, and "known issue" when `upstream.duplicate` is true. Keep it compact — one line per bug.
- "Show bugs that failed to forward" → filter `forward_failed_at` set
- "Show me all open bugs" → filter status=open
- "Show critical bugs" → filter severity=critical
- "Show bugs in email-triage" → filter collection=email-triage
- "Show everything" → no filter, show all

**View bug details**
When the admin asks about a specific bug (by ID or title), read the individual bug file from `{bug_log}/bugs/{id}.md` via `aifs_read`. Display all fields from the YAML frontmatter and the markdown body including admin notes. **1.4.0:** show the `upstream` block in words — agent-index status, its note to the org, an open question, the fix with the version message, "known issue, tracked with an existing report" for a duplicate, "details removed by agent-index's retention rule" when `content_deleted`, "deleted at your org's request" when the status is `deleted`, and "as of {synced_at}". Never show `upstream.token`.

**Answer agent-index (1.4.0)**
For a bug whose `upstream.question` is set (or any forwarded bug the admin wants to add to): show the question, take the admin's answer, show it back and ask "Send this to agent-index?". On yes, write the answer and the bug's `upstream.token` to two temporary local files and run:
```bash
python {apps_path}/upstream.py --server-url "{log_server_url}" --key-file "{temp_key}" reply --id "{upstream.id}" --token-file "{temp_token}" --member-hash "{admin_member_hash}" --text-file "{temp_text}"
```
Delete the temporary files. On success, set `upstream.status` to the returned status, clear `upstream.question`, append under `### Admin Notes` "- **{DATE} ({admin_display_name}):** Replied to agent-index: {first 200 characters}", write the bug file and update the manifest. Exit 5 with 404 → "agent-index doesn't recognise this bug any more"; exit 5 with 409 → "this bug's details were removed at agent-index, so it can't take replies"; 2/3/4 → as in sync.

**Update bug status**
Let the admin change a bug's status. Valid transitions:
- `open` → `acknowledged` — admin has seen it and is aware
- `open` → `closed` — not a real bug, duplicate, or resolved
- `acknowledged` → `forwarded` — forwarded to agent-index (typically done by `forward-bug`, but can be set manually)
- `acknowledged` → `closed` — resolved without forwarding
- `forwarded` → `closed` — agent-index has addressed it (1.4.0: offered automatically when the upstream status is `fixed-released`; never done without the admin's yes)
- `closed` → `open` — reopen a previously closed bug

To update status:
1. Read the bug file via `aifs_read("{bug_log}/bugs/{id}.md")`.
2. Update the `status` field in the YAML frontmatter. If transitioning to `closed`, set `closed_date` to the current date. If transitioning to `forwarded`, set `forwarded_date` to the current date.
3. Write the updated bug file back via `aifs_write("{bug_log}/bugs/{id}.md", content)`.
4. Update the matching entry in `bug-manifest.json` via `aifs_read` then `aifs_write`.
5. Confirm: "Bug {id} status updated to {new_status}."

**Add admin notes**
Let the admin append a note to a bug entry. Notes are appended under the `### Admin Notes` section of the bug's markdown body.

Format:
```markdown
- **{DATE} ({admin_display_name}):** {note text}
```

Read the bug file via `aifs_read("{bug_log}/bugs/{id}.md")`, find the `### Admin Notes` section, append the note, write back via `aifs_write("{bug_log}/bugs/{id}.md", content)`.

**Search bugs**
Search across bug titles, descriptions, and collections for a keyword. Use the manifest for initial filtering by title and collection. For deeper content search, read individual bug files via `aifs_read("{bug_log}/bugs/{id}.md")` for bugs that might match. Return matching bugs in the same compact one-line format as list.

### Guardrails

- Never delete bug entries from the log or manifest. Bugs can be closed but never removed.
- Never modify the bug's reporter information, reported date, or original description.
- Never modify collection-level setup parameters (bug_log_path, admin_roles, etc.).
- Always use `aifs_read` and `aifs_write` for all remote file operations — never native Read/Write.
- Always confirm status changes before writing.
- Never show, copy or note `upstream.token` (1.4.0). It is a per-bug secret; it stays in the bug file.
- Never change the local status because of the upstream status without the admin's yes (1.4.0).
- Never send a reply to agent-index without showing it and getting the admin's yes (1.4.0).
- If the remote filesystem is unavailable, inform the admin and suggest checking connectivity. Do not cache or display stale data without noting it may be outdated.

---

## Error Handling

- If remote filesystem access fails: "Could not access the bug log. Please check your remote filesystem connection."
- If the manifest is missing or corrupt: attempt to reconstruct by listing all `.md` files in `{bug_log}/bugs/` via `aifs_list` and reading their YAML frontmatter. If the `bugs/` directory is empty or missing, report: "No bug reports found at {bug_log_path}. Has the collection setup been completed?"
- If a bug ID referenced by the admin doesn't exist in the manifest: "No bug found with ID '{id}'. Use 'list bugs' to see all current bugs."
- If a status transition is invalid (e.g., `closed` → `forwarded`): explain the valid transitions and ask the admin to choose.
