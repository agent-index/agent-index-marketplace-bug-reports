---
name: forward-bug
type: task
version: 1.3.0
collection: bug-reports
description: Forward a selected bug report to the agent-index log collection server. Admin-only — packages the bug into the log collector's expected payload format and sends it via HTTP.
stateful: true
produces_artifacts: false
produces_shared_artifacts: true
dependencies:
  skills: []
  tasks: ["report-bug"]
external_dependencies:
  - Remote filesystem access
reads_from: "/shared/bug-reports/"
writes_to: "/shared/bug-reports/"
---

## About This Task

Forward Bug takes a bug report from the shared log and sends it to the upstream agent-index log collection server. This is the mechanism by which org admins selectively escalate bugs to the agent-index team. Only members whose org role matches the configured `admin_roles` can run this task.

The task packages the bug into the log collector's expected JSON envelope (schema version, log type, run ID, org/member hashes, and the bug entry as the payload), authenticates with the configured API key, and POSTs to the server. On success, it marks the bug as `forwarded` in the shared log and manifest. On failure (1.2.0+), it records the failed attempt on the bug so it can be found and retried later — a failed forward is never silently lost.

**1.3.0 (bug platform).** Only member hashes leave the org — no names or email addresses (decision B). The server's answer carries an upstream ID and a **status token** for the bug; both are saved in the bug file so `view-bugs` and `my-bugs` can show what agent-index does with it. The envelope says which client sent it (`client`) and the entry carries the org's versions (`environment`), so a fix can be compared with what the org runs. An org on an enterprise key is never offered the community key back.

---

## Configuration

This task reads its configuration from `collection-setup-responses.md` at runtime.

### Required Parameters

- **`bug_log_path`** — Remote filesystem path to the shared bug log directory
- **`log_server_url`** — Upstream log collection server endpoint (default: `https://v1.logs.agent-index.ai/logs`)
- **`log_server_auth_key`** — API key for the log server (stored separately at `{bug_log}/config/auth-key.txt`)
- **`admin_roles`** — Org roles allowed to forward bugs

---

## Workflow

### Step 1 — Validate Admin Access

On gdrive, resolve these reads by id anchor, never by bare path (OneDrive: read `/org-config.json`, `/bug-reports/setup/collection-setup-responses.md` and `/members-registry.json` by path instead — a bare `id:` resolves against the caller's own drive there; backend from local `agent-index.json` `remote_filesystem.backend`; core runtime-reference.md § "Addressing: Owned Content and Sharing", finding 63):

1. Read `org_config_id` from the local `agent-index.json` (`remote_filesystem.connection.org_config_id`), then read org-config via `aifs_read("id:{org_config_id}")`. Keep it — Step 5 needs `org_hash` from it.
2. From org-config take the `bug-reports` entry's `folder_id` in `installed_collections[]`, and `resource_ids.members_registry`.
3. Read `aifs_read("id:{folder_id}/setup/collection-setup-responses.md")` to get `admin_roles`, `bug_log_path`, and `log_server_url`.
4. **Resolve the bug log location — `{bug_log}` (1.5.0, bug platform finding 38).** `bug_log_path` is an org path such as `/shared/bug-reports/`. On gdrive, address it through org-config's `resource_ids.shared_root`: `/shared/{rest}` becomes `id:{shared_root}/{rest}` (no trailing slash), and every `{bug_log}/...` read, list and write in this file uses that id anchor. Never use the bare `/shared/...` path on gdrive: for a member outside the Shared Drive it fails with `BACKEND_ERROR` / `FILE_NOT_FOUND` (core runtime-reference.md § "Addressing: Owned Content and Sharing", `memberpathreads`). If `shared_root` is missing, halt and name it. On OneDrive, `{bug_log}` is `bug_log_path` as written, without the trailing slash. Also take `resource_ids.shared_root` from the org-config read in item 1.

On gdrive, do not read `/org-config.json`, `/members-registry.json`, or `/bug-reports/...` by bare path. For a member who is not a Shared Drive member these return FILE_NOT_FOUND, or resolve `/bug-reports` to the same-named `/shared/bug-reports` data folder (`memberdupcollfolders`/`nameambig`; bug `20260921-8d20ea22-185412-c4e7`). If `org_config_id`, `folder_id`, or `members_registry` is missing, halt and name the missing value — do not fall back to a bare path.

Read the members registry via `aifs_read("id:{members_registry}")` (OneDrive: `/members-registry.json` by path) and look up the current member's `org_role`. Access is granted when the member's `org_role` is in `admin_roles`, **or** the member is an org admin (member hash in org-config `admins[]`); when `admin_roles` is empty, only org admins may forward (1.3.0; matches collection setup). Otherwise respond: "Forwarding bugs is restricted to {admin_roles or 'org admins'}. You can submit bugs with '@ai:report-bug'." and exit.

### Step 2 — Select Bug to Forward

Read the manifest from `{bug_log}/bug-manifest.json` via `aifs_read`.

The manifest is only an index: `report-bug` doesn't write it, and it catches up when an admin runs `view-bugs`. So before listing, also `aifs_list("{bug_log}/bugs/")` and treat any bug file missing from the manifest as a candidate too (read its frontmatter for id, title, status, severity). A bug ID the admin names is read from its file even when the manifest has no entry (finding 45).

If the member specified a bug ID, find it in the manifest. If not, show all bugs with status `open` or `acknowledged` (not already forwarded or closed) and ask the admin to select one. List bugs with a `forward_failed_at` value first, marked "⚠ previous forward failed {forward_failed_at}: {forward_last_error}".

**Retry failed forwards (1.2.0).** If any open/acknowledged bug has `forward_failed_at` set, lead with: "{N} bug(s) have a failed forward attempt waiting to be retried. Retry them now?" On yes, run Steps 3–8 for each in turn — confirm once for the whole batch at Step 6 (list every bug), not once per bug. Stop the batch at the first `auth` or `network` failure (the next one will fail the same way); continue past a per-bug `payload` failure. Triggers like "retry failed forwards" or "resend failed bugs" go straight here.

**2026 outage window (one-time notice).** The agent-index log server rejected every submission from **2026-07-11 to 2026-10-05** (a server-side fault). Forwards attempted then were never received, and versions before 1.2.0 didn't record the failure. If any open/acknowledged bug without `forwarded_date` has a `reported_date` on or before 2026-10-05 and on or after 2026-07-01, mention once per session: "The agent-index log server was down from July 11 to October 5, 2026, so any forward attempted in that window didn't arrive. {N} unforwarded bug(s) were reported around then — want to review them for forwarding?" Never auto-forward them; the admin chooses.

If the selected bug's status is `forwarded`, warn: "Bug {id} was already forwarded on {forwarded_date}. Do you want to forward it again?" If yes, proceed. If no, exit or let them select another bug.

If no eligible bugs exist, inform: "No open or acknowledged bugs to forward. All bugs are either already forwarded or closed."

### Step 3 — Load Bug Details

Read the individual bug file from `{bug_log}/bugs/{id}.md` via `aifs_read`. Parse the YAML frontmatter and markdown body. Extract all fields: id, title, collection, severity, reporter, description, expected behavior, steps to reproduce, additional context, admin notes, and the reporter's own later additions (`### Reporter Updates`, written by `update-bug`). Send the Reporter Updates as part of `additional_context`, after the original context, under the line "Reporter updates:", without the display names (keep the dates). They often carry the detail agent-index needs (finding 52).

### Step 4 — Load Auth Key

Read the API key from `{bug_log}/config/auth-key.txt` via `aifs_read`. Trim any whitespace.

If the auth key file doesn't exist or is empty, halt: "No API key configured for the log collection server. Your org admin needs to provide one during collection setup."

**Which key is this? (1.3.0).** Write the key to a temporary local file (native Write) and run:

```bash
python {apps_path}/upstream.py --server-url "{log_server_url}" --key-file "{temp_key_path}" key-check
```

- `{"tier": "enterprise", "org": ...}` → the org's own enterprise key. **Skip the default-key check below entirely** — never offer the community key to an enterprise org (bug platform finding 2). Remember the org name for Step 6.
- `{"tier": "community"}` → the default-key check below can be skipped too (the key is the community key's equal on the server).
- exit 2 (`auth`) → the server does not accept this key: go to Error Handling `auth` now rather than after building the payload.
- exit 5 with HTTP 404, exit 3 or 4 → the server is older than 1.5.0 or unreachable; carry on with the default-key check below, as before.

Keep the temporary key file for Step 7 and delete it there.

**Default-key check (1.2.0; only when `key-check` could not answer).** Read `log_collector_api_key` from the local `agent-index.json` (native Read — it's the community key that ships with agent-index). If it's present and differs from the stored key, note it once before Step 6 — don't block, because enterprise orgs legitimately use their own key:

> "This org's log-server key isn't the standard agent-index community key. That's expected on an enterprise plan. If it was changed after an authentication error between July and October 2026, that error was a server outage, not a bad key — want me to restore the community key?"

On yes, write the community key to `{bug_log}/config/auth-key.txt` via `aifs_write` and use it for this send. Never print either key in full; show at most the first 10 characters.

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
  "client": "bug-reports/1.5.0",
  "entries": [
    {
      "bug_id": "{id}",
      "title": "{title}",
      "collection": "{collection}",
      "severity": "{severity}",
      "status": "{status}",
      "reporter": {
        "member_hash": "{reporter_member_hash}"
      },
      "reported_date": "{reported_date}",
      "description": "{what_happened}",
      "expected": "{expected_behavior}",
      "steps_to_reproduce": "{steps}",
      "additional_context": "{context}",
      "admin_notes": "{admin_notes}",
      "forwarded_by": {
        "member_hash": "{admin_member_hash}"
      },
      "forwarded_at": "{ISO_TIMESTAMP}",
      "environment": {
        "core": "{core_version}",
        "collection_version": "{reported_collection_version}",
        "backend": "{backend}",
        "bug_reports": "1.5.0"
      }
    }
  ]
}
```

Notes:
- `run_id`: generate a UUID v4 for this forwarding event.
- `org_hash`: take from the org-config already read by id anchor in Step 1 (never `aifs_read("/org-config.json")` — that bare path fails for non-Shared-Drive members) — use org-config's `org_uuid` exactly as written (for example `095851c4-890f-41fd-b588-ff4550c6145e`), not hashed. It is unique per org; agent-index matches claims, status, the org's bug list and org deletion by this value. If org-config has no `org_uuid`, stop and say so: "This org has no org_uuid in its configuration; ask agent-index support." (1.5.0, bug platform findings 41 and 54: a hash of the org name collided for two orgs with the same name.)
- `member_hash`: use the original bug reporter's hash, not the admin's.
- `agent_index_version`: read from the local agent-index-core version if available, otherwise use `"unknown"`.
- **No names or email addresses (1.3.0, decision B).** `reporter` and `forwarded_by` carry the member hash only. Do not add display names or emails anywhere in the payload. The bug's own text (description, steps, context, admin notes) is sent as written; Step 6 tells the admin so.
- `client`: always `"bug-reports/1.5.0"` for this version. It tells the server this client saves status tokens.
- `environment`: `core` = local `agent-index.json` `version` (else `"unknown"`); `backend` = local `agent-index.json` `remote_filesystem.backend`; `collection_version` = the reported collection's `version` in org-config `installed_collections[]` when it is installed, else `null` (also `null` for `agent-index-core` or an adapter — the core version is already there).

### Step 6 — Confirm With Admin

Show the admin a summary of what will be sent:

```
Forwarding to: {log_server_url}{ as {enterprise org} if key-check said enterprise}
Bug: {id} — {title}
Collection: {collection}
Severity: {severity}
Reporter: {reporter_display_name} (sent as a member ID only)
```

Then, always: "agent-index receives member IDs, not names or email addresses. The bug's own text — what happened, steps, context and admin notes — goes as written, so check it for anything you don't want to send."

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
4. Delete the temporary payload file and the temporary key file from Step 4.

If the script returns exit code 0 and the response contains `"message": "log received"`, the forward succeeded. Parse the response `id` (the upstream ID, also called the server reference) and, when present, `status_token` (1.3.0; servers before the bug platform don't send one). The token is a secret for this bug: never print it, never put it in admin notes or chat — only in the bug file's `upstream` block (Step 8).

If the script returns a non-zero exit code, the exit code classifies the failure (script 1.2.0+; the script already retries transient server/network errors twice before giving up):

| Exit | Class | Meaning |
|---|---|---|
| 1 | `local` | Bad payload file / missing fields — a bug in this task, not the server |
| 2 | `auth` | 401/403 — the server did not accept the key |
| 3 | `server` | 5xx after retries — the server is down or misconfigured (503 = server can't load its key config; **not a key problem**) |
| 4 | `network` | Could not reach the server after retries |
| 5 | `payload` | 413 / other 4xx — this bug's payload was rejected |

Read stderr for the detail line and go to Step 8.

### Step 8 — Update Bug Status

**On success:**

1. Read the bug file via `aifs_read("{bug_log}/bugs/{id}.md")`.
2. Update the YAML frontmatter: set `status: "forwarded"` and `forwarded_date: "{DATE}"`. Remove `forward_failed_at` and `forward_last_error` if present (keep `forward_attempts` as history). **1.3.0:** add (or replace) the `upstream` block and the `environment` block that was sent:
   ```yaml
   upstream:
     id: "{server_response_id}"
     token: "{status_token}"        # omit the line when the server sent none; view-bugs claims it later
     status: "submitted"
     org_note: null
     question: null
     fix: {repo: null, version: null, released_at: null}
     duplicate: false
     content_deleted: false
     synced_at: "{ISO_TIMESTAMP}"
   environment: {core: "...", collection_version: "...", backend: "...", bug_reports: "1.5.0"}
   ```
3. Append a note under `### Admin Notes`:
   ```
   - **{DATE} ({admin_display_name}):** Forwarded to agent-index. Server reference: {server_response_id}.
   ```
4. Write back via `aifs_write("{bug_log}/bugs/{id}.md", content)`.
5. Update the manifest entry via `aifs_read` then `aifs_write` on `bug-manifest.json` (set `status`, `forwarded_date`, and 1.3.0's `upstream_status: "submitted"`; drop `forward_failed_at`). If the bug has no entry yet, add one built from its frontmatter, in the same shape `view-bugs` uses when it reconciles. The token is never copied into the manifest.

**On failure (1.2.0) — exit codes 2–5.** Record the attempt so it can be retried. Do this even though nothing was sent; it's the only trace the attempt happened.

1. Read the bug file. Leave `status` unchanged.
2. In the frontmatter set `forward_failed_at: "{ISO_TIMESTAMP}"`, `forward_last_error: "{class}: {one-line stderr, max 200 chars}"`, and increment `forward_attempts` (start at 1).
3. Append under `### Admin Notes`:
   ```
   - **{DATE} ({admin_display_name}):** Forward to agent-index failed ({class}). Not sent — retry with "retry failed forwards".
   ```
4. Write back the bug file, then set `forward_failed_at` on the manifest entry.
5. If either write fails, still tell the admin the forward failed — the bug is simply not recorded as pending retry.

Exit code 1 (`local`) is not recorded on the bug: it is a defect in this task's payload construction, so surface it and stop.

### Step 9 — Confirm

On success: "Bug {id} has been forwarded to agent-index (reference {first 8 characters of server_response_id}). You'll see what agent-index does with it in '@ai:view-bugs'; the reporter can follow it with 'show my bugs'."

On failure: the matching Error Handling message below, followed by "I've recorded the failed attempt on bug {id}, so it will show up under 'retry failed forwards'."

For a batch retry, finish with one summary line: "{N_ok} forwarded, {N_failed} still failing ({class})."

---

## Directives

- Only members with admin roles can run this task. Check at Step 1 before doing anything else.
- Never forward a bug without explicit admin confirmation (Step 6).
- Never modify the bug's original content (reporter, description, dates) — only update status, forwarded_date, the `forward_*` attempt fields, the `upstream` and `environment` blocks (1.3.0), and admin notes.
- Never send names or email addresses upstream (1.3.0): member hashes only.
- Never show, log or note the status token; it lives only in the bug file's `upstream.token`.
- Never offer the community key to an org whose key `key-check` reports as `enterprise`.
- Never tell an admin to change the log-server key because of a `server` (5xx) or `network` failure — those are never key problems. Only an `auth` failure points at the key.
- Never send the auth key to any endpoint other than the configured `log_server_url`.
- Always use `aifs_read` and `aifs_write` for all remote file operations — never native Read/Write for shared data.
- The temporary payload file (Step 7) and key file (Step 4) are deleted after use.

---

## Error Handling

- If remote filesystem access fails: halt and instruct the admin to check connectivity.
- If the auth key is missing: halt and instruct the admin to complete collection setup.
- **`auth` (exit 2, 401/403):** "The log server didn't accept this org's key. Check that `{bug_log}/config/auth-key.txt` matches `log_collector_api_key` in your `agent-index.json` (the standard community key) — I can restore it if they differ. If you're on an enterprise plan with your own key, contact agent-index support at https://agent-index.ai/support." Run the Step 4 default-key check if it wasn't already offered. **1.3.0:** if the org's key was recorded as enterprise at setup (`log_server_key_tier: enterprise` in the setup responses), say instead: "The log server no longer accepts your enterprise key — it may have been revoked. Contact agent-index support; don't switch to the community key without talking to them." and do not offer the community key.
- **`server` (exit 3, 5xx):** "The agent-index log server is having a problem on its side (HTTP {code}). This isn't your key or your setup — please don't change anything. Try again later with 'retry failed forwards'."
- **`network` (exit 4):** "Couldn't reach the log server at {log_server_url}. Check your network connection (and, in Cowork, that the host is on the network allowlist — `@ai:verify-network-allowlist`). Retry later with 'retry failed forwards'."
- **`payload` (exit 5, 413 or other 4xx):** for 413: "This bug report is too large for the log server (5 MB limit). Try trimming the additional context or admin notes, then retry." Otherwise show the server's error line.
- **`local` (exit 1):** "The forward payload couldn't be built correctly: {stderr}. This is a defect in forward-bug — please report it with `@ai:report-bug`."
- If the bug log update fails after a successful forward: inform the admin that the bug was forwarded but the local status wasn't updated. The admin can update it manually via `view-bugs`.
