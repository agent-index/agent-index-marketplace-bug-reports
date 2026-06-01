---
name: report-bug
type: task
version: 1.2.0
collection: bug-reports
description: Walk a member through submitting a bug report — collect details about the issue, severity, and reproduction steps, then write the report as an individual file. The shared index is maintained by view-bugs (reconcile-on-read), not this task.
stateful: true
produces_artifacts: false
produces_shared_artifacts: true
dependencies:
  skills: []
  tasks: []
external_dependencies:
  - Remote filesystem access
reads_from: "/shared/bug-reports/"
writes_to: "/shared/bug-reports/bugs/"
---

## About This Task

Report Bug is the submission task available to every member in the org. It interviews the member about the bug they encountered, collects structured information (which collection, what happened, steps to reproduce, severity), generates a collision-free bug ID, and writes the report as an individual markdown file on the remote filesystem. The bug file is the source of truth; the shared index (`bug-manifest.json`) is rebuilt from the bug files by the admin-only `view-bugs` skill (reconcile-on-read, v1.2.0+), so this task never writes the manifest. Members are granted writer on `bugs/` only — provisioned at collection install via `collaborative-acls.json`.

No special role is required — any org member can report a bug.

---

## Configuration

This task reads its configuration from `collection-setup-responses.md` at runtime. All parameters are org-mandated (set by the admin at collection install time).

### Required Parameters

- **`bug_log_path`** — Remote filesystem path to the shared bug log directory (default: `/shared/bug-reports/`)
- **`severity_levels`** — Available severity levels for bug reports (default: `["critical", "high", "medium", "low"]`)

---

## Workflow

### Step 1 — Load Configuration

Read `collection-setup-responses.md` from the collection's setup directory via `aifs_read` to get `bug_log_path` and `severity_levels`.

Read the members registry via `aifs_read("/members-registry.json")` to resolve the current member's identity (display_name, member_hash, email) for attribution.

If remote filesystem access fails: attempt re-authentication via `aifs_authenticate`. If that fails, halt with: "Bug Reports needs remote filesystem access to submit your report. Please check your connection or run '@ai:member-bootstrap'."

### Step 2 — Collect Bug Details

Interview the member to gather the following information. Ask questions conversationally, one at a time, using progressive disclosure.

**2a. Collection name.**
Ask: "Which collection did you encounter the bug in? (e.g., 'email-triage', 'projects', or 'agent-index-core')"
- Accept any string. This is a free-text field — the member might report bugs against collections not installed in this org, or against agent-index-core itself.

**2b. Bug title.**
Ask: "Give this bug a short title — one sentence describing what went wrong."
- Should be brief and descriptive, like a commit message.

**2c. What happened.**
Ask: "What happened? Describe the actual behavior you saw."

**2d. What you expected.**
Ask: "What did you expect to happen instead?"

**2e. Steps to reproduce.**
Ask: "Can you describe the steps to reproduce this? Walk me through what you did before the bug appeared."
- This can be multiple steps. Record them as a numbered list.
- If the member says they can't reproduce it or aren't sure, that's fine — record "Not reproducible / unclear" and move on.

**2f. Severity.**
Ask: "How severe is this? Options: {severity_levels}"
- Present the configured severity levels.
- If the member isn't sure, suggest `medium` as a reasonable default.

**2g. Additional context (optional).**
Ask: "Anything else worth noting? Error messages, screenshots you can describe, workarounds you found? (Or say 'no' to skip.)"

### Step 3 — Generate Bug ID

Create a collision-free bug ID using the format: `{YYYYMMDD}-{first 8 chars of member_hash}-{HHMMSS}-{4 random lowercase hex}` (UTC time-of-day plus a short random token as the suffix).

The `member_hash` component guarantees no collision between different members; `{HHMMSS}` plus the 4-hex random token guarantees no collision even if the same member files more than one bug in the same second. Because the ID is unique by construction, **do not read `bug-manifest.json` and do not list `bugs/`** — the member's write path is a single `aifs_write` and must not depend on reading shared state (members have writer on `bugs/`, but read-before-write would couple this task to listing/inheritance behavior we deliberately avoid).

### Step 4 — Confirm With Member

Present the full bug report back to the member for confirmation before writing:

```
Bug ID: {id}
Collection: {collection}
Title: {title}
Severity: {severity}
Reported by: {display_name}

What happened: {description}
Expected: {expected}
Steps to reproduce: {steps}
Additional context: {context}
```

Ask: "Does this look right? I'll submit it to the shared bug log."

If the member wants to change anything, go back to the relevant sub-step in Step 2.

### Step 5 — Write Bug File

Write the bug report as an individual markdown file at `{bug_log_path}/bugs/{id}.md` via `aifs_write`. Each bug file uses this format:

```markdown
---
id: "{id}"
status: "open"
reporter:
  display_name: "{display_name}"
  member_hash: "{member_hash}"
  email: "{email}"
collection: "{collection}"
severity: "{severity}"
reported_date: "{DATE}"
forwarded_date: null
closed_date: null
---

## {title}

**What happened:** {description}

**Expected:** {expected}

**Steps to reproduce:**
{numbered_steps}

**Additional context:** {context}

### Admin Notes
(none)
```

Write the file via `aifs_write("{bug_log_path}/bugs/{id}.md", content)`. This is the only write this task performs — it does **not** touch `bug-manifest.json` (see About: `view-bugs` reconciles the index from the bug files).

### Step 6 — Confirm Submission

Tell the member: "Bug {id} has been submitted. Your org admin can see it in the bug log and forward it to agent-index if needed. You can check on it by asking an admin to run '@ai:view-bugs'."

---

## Directives

- Any member can run this task regardless of their org role.
- Never modify existing bug files — only create new ones. (Members update their *own* bugs via `@ai:update-bug`, not this task.)
- Never delete bug files.
- This task never reads or writes `bug-manifest.json`. The index is admin-maintained by `view-bugs` (reconcile-on-read).
- Always confirm the report with the member before writing (Step 4).
- If the remote filesystem is unavailable, do not attempt to write locally as a fallback — the bug log must be on the shared filesystem so admins can see it. Halt and explain.
- Use `aifs_read` and `aifs_write` for all remote file operations — never native Read/Write.

---

## Error Handling

- If remote filesystem access fails at any step (auth/connectivity): halt and instruct the member to check their connection or run `@ai:member-bootstrap`. Do not lose the collected bug details — offer to retry once connectivity is restored.
- **If the `aifs_write` to `bugs/` fails with a permission/authorization error (NOT an auth/connectivity error):** the member has not been granted writer on the shared bug log. Surface: "You don't appear to have write access to the shared bug log. This is an org setup step — ask your admin to run `@ai:install-collection bug-reports` to provision member write access, then try again." Do **not** route the member to `@ai:member-bootstrap` (that is for auth/connectivity, not authorization). Preserve the collected details for retry.
- If the member abandons the interview partway through: do not write anything. Incomplete bugs are not submitted.
