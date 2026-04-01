---
name: report-bug
type: task
version: 1.0.0
collection: bug-reports
description: Walk a member through submitting a bug report — collect details about the issue, severity, and reproduction steps, then write the report as an individual file and update the manifest index.
stateful: true
produces_artifacts: false
produces_shared_artifacts: true
dependencies:
  skills: []
  tasks: []
external_dependencies:
  - agent-index-filesystem MCP
reads_from: "/shared/bug-reports/"
writes_to: "/shared/bug-reports/"
---

## About This Task

Report Bug is the submission task available to every member in the org. It interviews the member about the bug they encountered, collects structured information (which collection, what happened, steps to reproduce, severity), generates a unique bug ID, writes the report as an individual markdown file on the remote filesystem, and updates the manifest index so the bug is discoverable by admins.

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

Create a unique bug ID using the format: `{YYYYMMDD}-{first 8 chars of member_hash}`.

If a bug with that exact ID already exists in the manifest (the member submitted another bug today), append a sequential suffix: `-2`, `-3`, etc. Check the manifest via `aifs_read("{bug_log_path}/bug-manifest.json")` to verify uniqueness.

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

Write the file via `aifs_write("{bug_log_path}/bugs/{id}.md", content)`.

### Step 6 — Update Manifest

Read the manifest from `{bug_log_path}/bug-manifest.json` via `aifs_read`. Parse it as JSON.

Add a new entry to the `bugs` array:

```json
{
  "id": "{id}",
  "title": "{title}",
  "collection": "{collection}",
  "severity": "{severity}",
  "status": "open",
  "reporter_hash": "{member_hash}",
  "reported_date": "{DATE}",
  "forwarded_date": null,
  "closed_date": null
}
```

Update `last_updated` to the current ISO timestamp.

Write the updated manifest back via `aifs_write("{bug_log_path}/bug-manifest.json", content)`.

### Step 7 — Confirm Submission

Tell the member: "Bug {id} has been submitted. Your org admin can see it in the bug log and forward it to agent-index if needed. You can check on it by asking an admin to run '@ai:view-bugs'."

---

## Directives

- Any member can run this task regardless of their org role.
- Never modify existing bug files — only create new ones.
- Never delete bug files or truncate the manifest.
- Always confirm the report with the member before writing (Step 4).
- If the remote filesystem is unavailable, do not attempt to write locally as a fallback — the bug log must be on the shared filesystem so admins can see it. Halt and explain.
- Use `aifs_read` and `aifs_write` for all remote file operations — never native Read/Write.

---

## Error Handling

- If remote filesystem access fails at any step: halt and instruct the member to check their connection. Do not lose the collected bug details — offer to retry once connectivity is restored.
- If the `bugs/` directory doesn't exist at `{bug_log_path}/bugs/`: create it before writing the bug file.
- If the manifest doesn't exist at `{bug_log_path}/bug-manifest.json`: create it with the base schema before adding the entry.
- If writing the bug file succeeds but the manifest write fails: inform the member that the bug was saved but the index may be out of sync. The bug file still exists at `{bug_log_path}/bugs/{id}.md` and an admin can re-index manually.
- If the member abandons the interview partway through: do not write anything. Incomplete bugs are not submitted.
