---
name: bug-reports-collection-setup
type: collection-setup
version: 1.0.0
collection: bug-reports
description: Org-admin setup for the bug-reports collection — configures the shared bug log path, admin roles, log collection server endpoint, and authentication for forwarding bugs upstream.
upgrade_compatible: true
---

## Collection Setup Overview

This setup is run by an org admin when installing the bug-reports collection. It configures where bug reports are stored on the shared filesystem, which org roles have admin access (view, triage, forward), and the upstream log collection server endpoint for forwarding bugs to agent-index.

---

## Prerequisites

- agent-index-filesystem MCP server connected and authenticated (test with `aifs_auth_status()`)
- The org's `org-config.json` must have at least one org role defined (for designating admin roles)

---

## Parameters

### `bug_log_path` [org-mandated]
Remote filesystem path where the shared bug log and manifest are stored.
- Default: `/shared/bug-reports/`
- Ask: "Where should the shared bug log be stored on the remote filesystem? Default is '/shared/bug-reports/'. All members will write bug reports here and admins will read from here."
- The setup will create this directory with: a `bugs/` subdirectory for individual bug files, and a `bug-manifest.json` index file.

### `admin_roles` [org-mandated]
Which org roles have access to the `view-bugs` skill and `forward-bug` task. Members without a matching role can only use `report-bug`.
- Ask: "Which org roles should have admin access to view, triage, and forward bug reports? These roles will be able to see all submitted bugs and forward them to agent-index."
- Read `org-config.json` via `aifs_read("/org-config.json")` and present the available `org_roles` list. Let the admin select one or more.
- Store as an array of `role_id` strings.

### `log_server_url` [org-mandated]
The upstream log collection server endpoint where forwarded bugs are sent.
- Default: `https://v1.logs.agent-index.ai/logs`
- Ask: "What is the log collection server URL for forwarding bugs? Default is the agent-index community server at 'https://v1.logs.agent-index.ai/logs'."

### `log_server_auth_key` [org-mandated]
The API key used to authenticate with the log collection server. Sent as a Bearer token.
- Default: the community key bundled with agent-index-core (read from the org's agent-index config if available)
- Ask: "What API key should be used for the log collection server? If your org uses the community tier, you can use the bundled community key. Enterprise orgs should use their enterprise key."
- Store this value on the **remote filesystem** at `{bug_log_path}/config/auth-key.txt` via `aifs_write`. Do not store it in the collection setup responses file — it's a secret.

### `severity_levels` [org-mandated]
The severity levels available when reporting bugs.
- Default: `["critical", "high", "medium", "low"]`
- Ask: "What severity levels should be available for bug reports? Default is critical, high, medium, low. You can customize these for your org."

---

## Setup Completion

1. Validate remote filesystem access via `aifs_auth_status()`. If not authenticated, attempt `aifs_authenticate`. If that fails, halt and instruct the admin.
2. Create the bug log directory at `{bug_log_path}` on the remote filesystem via `aifs_write`.
3. Create the `bugs/` subdirectory at `{bug_log_path}/bugs/` via `aifs_write` (write a placeholder `.gitkeep` file if needed to create the directory).
4. Write an empty `bug-manifest.json` at `{bug_log_path}/bug-manifest.json` via `aifs_write`:
   ```json
   {
     "version": "1.0.0",
     "last_updated": "{ISO_TIMESTAMP}",
     "bugs": []
   }
   ```
5. Write the auth key to `{bug_log_path}/config/auth-key.txt` via `aifs_write`.
6. Write `collection-setup-responses.md` to `/setup/` with all configured parameters (except the auth key) in YAML format.
7. Confirm to admin: "Bug Reports is set up. Members can submit bugs with '@ai:report-bug'. Admins with {admin_roles} roles can view bugs with '@ai:view-bugs' and forward them with '@ai:forward-bug'."

---

## Upgrade Behavior

### Preserved Responses
- `bug_log_path`
- `admin_roles`
- `log_server_url`
- `log_server_auth_key` (stored separately on remote filesystem)
- `severity_levels`
- All existing bug log entries and manifest data

### Reset on Upgrade
- None

### Requires Member Attention
- If new severity levels are added by the org, existing bugs retain their original severity
- If admin roles change, access changes take effect on next invocation

### Migration Notes
- v1.0 → future versions: migration notes will be added here as new versions are published.
