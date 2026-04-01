---
name: forward-bug
type: task
version: 1.0.0
collection: bug-reports
description: Forward a selected bug report to the agent-index log collection server. Admin-only — packages the bug into the log collector's expected payload format and sends it via HTTP.
stateful: true
produces_artifacts: false
produces_shared_artifacts: true
dependencies:
  skills: []
  tasks: ["report-bug"]
external_dependencies:
  - agent-index-filesystem MCP
reads_from: "/shared/bug-reports/"
writes_to: "/shared/bug-reports/"
---

## About This Task

Forward Bug takes a bug report from the shared log and sends it to the upstream agent-index log collection server. This is the mechanism by which org admins selectively escalate bugs to the agent-index team. Only members whose org role matches the configured `admin_roles` can run this task.

The task packages the bug into the log collector's expected JSON envelope (schema version, log type, run ID, org/member hashes, and the bug entry as the payload), authenticates with the configured API key, and POSTs to the server. On success, it marks the bug as `forwarded` in the shared log and manifest.

---

## Configuration

This task reads its configuration from `collection-setup-responses.md` at runtime.

### Required Parameters

- **`bug_log_path`** — Remote filesystem path to the shared bug log directory
- **`log_server_url`** — Upstream log collection server endpoint (default: `https://v1.logs.agent-index.ai/logs`)
- **`log_server_auth_key`** — API key for the log server (stored separately at `{bug_log_path}/config/auth-key.txt`)
- **`admin_roles`** — Org roles allowed to forward bugs

---

## Workflow

### Step 1 — Validate Admin Access

Read `collection-setup-responses.md` via `aifs_read` to get `admin_roles`, `bug_log_path`, and `log_server_url`.

Read the members registry via `aifs_read("/members-registry.json")` and look up the current member's `org_role`. If their role is not in `admin_roles`, respond: "Forwarding bugs is restricted to {admin_roles} roles. You can submit bugs with '@ai:report-bug'." and exit.

### Step 2 — Select Bug to Forward

Read the manifest from `{bug_log_path}/bug-manifest.json` via `aifs_read`.

If the member specified a bug ID, find it in the manifest. If not, show all bugs with status `open` or `acknowledged` (not already forwarded or closed) and ask the admin to select one.

If the selected bug's status is `forwarded`, warn: "Bug {id} was already forwarded on {forwarded_date}. Do you want to forward it again?" If yes, proceed. If no, exit or let them select another bug.

If no eligible bugs exist, inform: "No open or acknowledged bugs to forward. All bugs are either already forwarded or closed."

### Step 3 — Load Bug Details

Read the individual bug file from `{bug_log_path}/bugs/{id}.md` via `aifs_read`. Parse the YAML frontmatter and markdown body. Extract all fields: id, title, collection, severity, reporter, description, expected behavior, steps to reproduce, additional context, and admin notes.

### Step 4 — Load Auth Key

Read the API key from `{bug_log_path}/config/auth-key.txt` via `aifs_read`. Trim any whitespace.

If the auth key file doesn't exist or is empty, halt: "No API key configured for the log collection server. Your org admin needs to provide one during collection setup."

### Step 5 — Build Payload

Construct the log collector's expected JSON payload:

```json
{
  "schema_version": "1",
  "log_type": "bug-report",
  "run_id": "{uuid}",
  "org_hash": "{org_hash}",
  "member_hash": "{reporter_member_hash}",
  "agent_index_version": "{agent_index_version}",
  "submitted_at": "{ISO_TIMESTAMP}",
  "entries": [
    {
      "bug_id": "{id}",
      "title": "{title}",
      "collection": "{collection}",
      "severity": "{severity}",
      "status": "{status}",
      "reporter": {
        "display_name": "{reporter_display_name}",
        "member_hash": "{reporter_member_hash}",
        "email": "{reporter_email}"
      },
      "reported_date": "{reported_date}",
      "description": "{what_happened}",
      "expected": "{expected_behavior}",
      "steps_to_reproduce": "{steps}",
      "additional_context": "{context}",
      "admin_notes": "{admin_notes}",
      "forwarded_by": {
        "display_name": "{admin_display_name}",
        "member_hash": "{admin_member_hash}"
      },
      "forwarded_at": "{ISO_TIMESTAMP}"
    }
  ]
}
```

Notes:
- `run_id`: generate a UUID v4 for this forwarding event.
- `org_hash`: read from `org-config.json` via `aifs_read("/org-config.json")` — use the org's identifier hash.
- `member_hash`: use the original bug reporter's hash, not the admin's.
- `agent_index_version`: read from the local agent-index-core version if available, otherwise use `"unknown"`.

### Step 6 — Confirm With Admin

Show the admin a summary of what will be sent:

```
Forwarding to: {log_server_url}
Bug: {id} — {title}
Collection: {collection}
Severity: {severity}
Reporter: {reporter_display_name}
```

Ask: "Ready to forward this bug to agent-index?"

### Step 7 — Send to Log Server

Run the forwarding script from the collection's `/apps/` directory:

```bash
python {apps_path}/forward-bug.py \
    --server-url "{log_server_url}" \
    --auth-key "{auth_key}" \
    --payload-file "{temp_payload_path}"
```

Before calling the script:
1. Write the JSON payload to a temporary local file using native Write.
2. Run the script.
3. Check the exit code and stdout.

If the script returns exit code 0 and the response contains `"message": "log received"`, the forward succeeded. Parse the response `id` for reference.

If the script returns a non-zero exit code, read stderr for the error message and report it to the admin.

### Step 8 — Update Bug Status

On successful forwarding:

1. Read the bug file via `aifs_read("{bug_log_path}/bugs/{id}.md")`.
2. Update the YAML frontmatter: set `status: "forwarded"` and `forwarded_date: "{DATE}"`.
3. Append a note under `### Admin Notes`:
   ```
   - **{DATE} ({admin_display_name}):** Forwarded to agent-index. Server reference: {server_response_id}.
   ```
4. Write back via `aifs_write("{bug_log_path}/bugs/{id}.md", content)`.
5. Update the manifest entry via `aifs_read` then `aifs_write` on `bug-manifest.json`.

### Step 9 — Confirm

Tell the admin: "Bug {id} has been forwarded to agent-index. Server reference: {server_response_id}. Status updated to 'forwarded'."

---

## Directives

- Only members with admin roles can run this task. Check at Step 1 before doing anything else.
- Never forward a bug without explicit admin confirmation (Step 6).
- Never modify the bug's original content (reporter, description, dates) — only update status, forwarded_date, and admin notes.
- Never send the auth key to any endpoint other than the configured `log_server_url`.
- Always use `aifs_read` and `aifs_write` for all remote file operations — never native Read/Write for shared data.
- The temporary payload file written locally in Step 7 should be cleaned up after the script completes.

---

## Error Handling

- If remote filesystem access fails: halt and instruct the admin to check connectivity.
- If the auth key is missing: halt and instruct the admin to complete collection setup.
- If the forwarding script fails with a 401 or 403: "Authentication failed. The API key may be invalid or expired. Contact your org admin to update the key."
- If the forwarding script fails with a 413: "The bug report payload is too large for the log server (5 MB limit). Try trimming the additional context or admin notes."
- If the forwarding script fails with a 5xx: "The log collection server returned an error. This may be temporary — try again in a few minutes."
- If the script fails with a network error: "Could not reach the log server at {log_server_url}. Check network connectivity."
- If the bug log update fails after a successful forward: inform the admin that the bug was forwarded but the local status wasn't updated. The admin can update it manually via `view-bugs`.
