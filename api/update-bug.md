---
name: update-bug
type: task
version: 1.0.0
collection: bug-reports
description: Let a member add detail to or update the status-neutral fields of a bug THEY reported. Ownership-enforced — a member can only edit their own bugs. Admin triage (status changes, notes on any bug) stays in view-bugs.
stateful: true
produces_artifacts: false
produces_shared_artifacts: true
dependencies:
  skills: []
  tasks: []
external_dependencies:
  - Remote filesystem access
reads_from: "/shared/bug-reports/bugs/"
writes_to: "/shared/bug-reports/bugs/"
---

## About This Task

Update Bug lets any member revise a bug **they reported** — for example, adding reproduction detail, attaching new context, or confirming the issue is still happening. It is the member-facing counterpart to the admin-only `view-bugs` triage interface.

Ownership is enforced: the task refuses to edit a bug whose `reporter.member_hash` is not the current member. Status changes (`open`/`acknowledged`/`forwarded`/`closed`) remain an admin action in `view-bugs` — members cannot change status here.

> **Enforcement note (important):** members are granted writer on the whole `bugs/` folder (folder-level ACL), so the per-bug "owner only" rule is enforced **in this task's logic, not by the filesystem**. It is a workflow convention, not a hard security boundary; a determined member could bypass it with a raw `aifs_write`. Hard per-bug enforcement would require per-file `inherit:false` ACLs and is intentionally out of scope. Acceptable for bug tracking.

---

## Configuration

Reads `collection-setup-responses.md` at runtime for `bug_log_path`. No member-defined parameters.

---

## Workflow

### Step 1 — Load Configuration & Identity

Read `collection-setup-responses.md` via `aifs_read` for `bug_log_path`. Read `/members-registry.json` via `aifs_read` to resolve the current member's `member_hash` and `display_name`.

If remote access fails (auth/connectivity): attempt `aifs_authenticate`; if still failing, halt with the standard connectivity message and `@ai:member-bootstrap` suggestion.

### Step 2 — Identify the Target Bug

- If the member names a bug ID, use it.
- If the member says "my bugs" / "the bug I filed", help them find it **without writing shared state**: read the admin-maintained index `{bug_log_path}/bug-manifest.json` via `aifs_read` (members have reader), filter entries where `reporter_hash` == the current member's hash, and present that short list. If the index is unavailable or empty, ask the member for the bug ID directly. Members never write the index.

### Step 3 — Ownership Check

Read the target bug file via `aifs_read("{bug_log_path}/bugs/{id}.md")`. Compare the frontmatter `reporter.member_hash` to the current member's hash.

- If they do **not** match: refuse — "You can only update bugs you reported. Ask an admin to use '@ai:view-bugs' to change someone else's bug." Halt without writing.
- If the file does not exist: "No bug found with ID '{id}'." Halt.

### Step 4 — Collect & Apply the Member-Permitted Edit

Member-editable surface (everything else is admin-only):

- Append a reporter update to the body under a `### Reporter Updates` section (create the section if absent):
  ```markdown
  - **{DATE} ({display_name}):** {update text}
  ```
- Optionally revise the `**What happened:**`, `**Expected:**`, `**Steps to reproduce:**`, or `**Additional context:**` body fields with member-confirmed new text.

The member may **not** change: `status`, `forwarded_date`, `closed_date`, `reporter.*`, `id`, `collection`, `reported_date`, or the `### Admin Notes` section. If the member asks to change status, explain it is an admin action via `view-bugs`.

Confirm the change with the member before writing.

### Step 5 — Write the Bug File

Write the updated file back via `aifs_write("{bug_log_path}/bugs/{id}.md", content)`. This is the only write. **Do not** write `bug-manifest.json` — `view-bugs` reconciles the index from the files on its next load.

### Step 6 — Confirm

Tell the member: "Updated bug {id}. Your admin will see the change next time they run '@ai:view-bugs'."

---

## Directives

- Any member can run this task, but only against bugs they reported (Step 3).
- Never change admin-only fields or another member's bug.
- Never write the manifest.
- Use `aifs_read`/`aifs_write` for all remote operations — never native Read/Write, never `aifs_share`.

---

## Error Handling

- Auth/connectivity failure: halt with the standard message; preserve the member's intended edit for retry.
- Permission/authorization failure on the `aifs_write` to `bugs/`: surface "You don't appear to have write access to the shared bug log — ask your admin to run '@ai:install-collection bug-reports' to provision member write access." Do not route to `@ai:member-bootstrap`.
- Ownership mismatch: see Step 3.
