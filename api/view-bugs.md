---
name: view-bugs
type: skill
version: 1.2.0
collection: bug-reports
description: Interactive admin interface for viewing, filtering, and triaging bug reports. Admins can browse all submitted bugs, update status, add notes, and select bugs for forwarding.
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

---

## Directives

### Invocation

When the member invokes this skill:

1. **Check admin access.** Read `collection-setup-responses.md` via `aifs_read` to get `admin_roles` and `bug_log_path`. Read the members registry via `aifs_read("/members-registry.json")` and look up the current member's `org_role`. If their role is not in `admin_roles`, respond: "Bug report admin access is restricted to {admin_roles} roles. You can submit bugs with '@ai:report-bug'." and exit.

2. **Load and reconcile the manifest.** (Reconcile-on-read added in v1.2.0; closes bug `20260513-8d20ea22`.) The manifest is a denormalized cache of the individual bug files under `{bug_log_path}/bugs/*.md`. Writers (this skill's status-update path, `report-bug`, ad-hoc edits via other sessions) are supposed to keep both in sync, but in practice the manifest drifts: new bug files don't get inserted, status changes on individual files don't get reflected in the manifest. Trusting the manifest blindly produces stale reports — a known bug.

   To prevent this, view-bugs **always reconciles before rendering**:

   1. `aifs_list("{bug_log_path}/bugs/")` to enumerate every `.md` file.
   2. For each, `aifs_read("{bug_log_path}/bugs/{filename}")` and parse the YAML frontmatter (id, title, collection, severity, status, reporter, reported_date, forwarded_date, closed_date).
   3. Build the canonical bug list from those individual files. This is the authoritative source.
   4. `aifs_read("{bug_log_path}/bug-manifest.json")` (best-effort; tolerate missing/corrupt — treat as `{ bugs: [] }`).
   5. Diff the canonical list against the manifest's `bugs` array. If they differ in any way (missing entries, extra entries, status mismatches, title mismatches): rebuild the manifest from the canonical list and write it back via `aifs_write("{bug_log_path}/bug-manifest.json", ...)`. Set `last_updated` to the current ISO timestamp.
   6. Surface a one-line notice if a reconcile actually rewrote the manifest: "Reconciled bug-manifest.json — {N_added} added, {N_status_changed} status changes, {N_removed} removed from manifest." (Suppress this notice in the cleanly-aligned case.)

   **Cost.** One `aifs_list` plus N `aifs_read` calls per view-bugs invocation, where N is the bug count. For a typical install with 10–50 bugs, that's bounded and fast (parallel reads finish in 1–3 seconds). View-bugs runs interactively so the cost is acceptable.

   **Failure tolerance.** If individual file reads fail (network, malformed frontmatter), still attempt to render from the partial reconciliation and surface the failures. Do NOT write a half-reconciled manifest back — leave the old manifest in place if any read failed, surface the issue, ask the admin to retry.

   Proceed with the reconciled bugs list (in memory) for the rest of this skill's operations.

3. **Show summary.** Display a summary of the current bug log:
   - Total bugs: {count}
   - Open: {count} | Acknowledged: {count} | Forwarded: {count} | Closed: {count}
   - By severity: Critical: {n}, High: {n}, Medium: {n}, Low: {n}
   - Most recent: "{title}" ({id}, {severity}, {reported_date})

4. **Ask what the admin wants to do.**

### Supported Operations

**List bugs (with filters)**
Show all bugs, or filter by status, severity, collection, or reporter. For each bug, display: ID, title, collection, severity, status, reporter display_name, and reported date. Keep it compact — one line per bug.
- "Show me all open bugs" → filter status=open
- "Show critical bugs" → filter severity=critical
- "Show bugs in email-triage" → filter collection=email-triage
- "Show everything" → no filter, show all

**View bug details**
When the admin asks about a specific bug (by ID or title), read the individual bug file from `{bug_log_path}/bugs/{id}.md` via `aifs_read`. Display all fields from the YAML frontmatter and the markdown body including admin notes.

**Update bug status**
Let the admin change a bug's status. Valid transitions:
- `open` → `acknowledged` — admin has seen it and is aware
- `open` → `closed` — not a real bug, duplicate, or resolved
- `acknowledged` → `forwarded` — forwarded to agent-index (typically done by `forward-bug`, but can be set manually)
- `acknowledged` → `closed` — resolved without forwarding
- `forwarded` → `closed` — agent-index has addressed it
- `closed` → `open` — reopen a previously closed bug

To update status:
1. Read the bug file via `aifs_read("{bug_log_path}/bugs/{id}.md")`.
2. Update the `status` field in the YAML frontmatter. If transitioning to `closed`, set `closed_date` to the current date. If transitioning to `forwarded`, set `forwarded_date` to the current date.
3. Write the updated bug file back via `aifs_write("{bug_log_path}/bugs/{id}.md", content)`.
4. Update the matching entry in `bug-manifest.json` via `aifs_read` then `aifs_write`.
5. Confirm: "Bug {id} status updated to {new_status}."

**Add admin notes**
Let the admin append a note to a bug entry. Notes are appended under the `### Admin Notes` section of the bug's markdown body.

Format:
```markdown
- **{DATE} ({admin_display_name}):** {note text}
```

Read the bug file via `aifs_read("{bug_log_path}/bugs/{id}.md")`, find the `### Admin Notes` section, append the note, write back via `aifs_write("{bug_log_path}/bugs/{id}.md", content)`.

**Search bugs**
Search across bug titles, descriptions, and collections for a keyword. Use the manifest for initial filtering by title and collection. For deeper content search, read individual bug files via `aifs_read("{bug_log_path}/bugs/{id}.md")` for bugs that might match. Return matching bugs in the same compact one-line format as list.

### Guardrails

- Never delete bug entries from the log or manifest. Bugs can be closed but never removed.
- Never modify the bug's reporter information, reported date, or original description.
- Never modify collection-level setup parameters (bug_log_path, admin_roles, etc.).
- Always use `aifs_read` and `aifs_write` for all remote file operations — never native Read/Write.
- Always confirm status changes before writing.
- If the remote filesystem is unavailable, inform the admin and suggest checking connectivity. Do not cache or display stale data without noting it may be outdated.

---

## Error Handling

- If remote filesystem access fails: "Could not access the bug log. Please check your remote filesystem connection."
- If the manifest is missing or corrupt: attempt to reconstruct by listing all `.md` files in `{bug_log_path}/bugs/` via `aifs_list` and reading their YAML frontmatter. If the `bugs/` directory is empty or missing, report: "No bug reports found at {bug_log_path}. Has the collection setup been completed?"
- If a bug ID referenced by the admin doesn't exist in the manifest: "No bug found with ID '{id}'. Use 'list bugs' to see all current bugs."
- If a status transition is invalid (e.g., `closed` → `forwarded`): explain the valid transitions and ask the admin to choose.
