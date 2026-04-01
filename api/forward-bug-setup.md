---
name: forward-bug-setup
type: setup
version: 1.0.0
collection: bug-reports
description: Setup for the forward-bug task — validates admin role access, remote filesystem connectivity, and log server configuration.
target: forward-bug
target_type: task
upgrade_compatible: true
---

## Setup Overview

Forward Bug requires no member-specific configuration. All parameters (log server URL, auth key, admin roles) are org-mandated and set during collection setup. This setup validates that the member has an admin role, the log server is configured, and the forwarding script is available.

---

## Pre-Setup Checks

- Collection setup has been completed (verify `collection-setup-responses.md` exists via `aifs_read`) → if not: "Your org admin needs to complete the bug-reports collection setup first. Contact your admin."
- Remote filesystem is accessible (test with `aifs_auth_status()`) → if not: "Please check your remote filesystem connection or run '@ai:member-bootstrap'."
- Member's org role is in the configured `admin_roles` list → if not: "Forward Bug is restricted to admin roles ({admin_roles}). Your current role ({member_role}) does not have access."
- Auth key exists at `{bug_log_path}/config/auth-key.txt` on the remote filesystem → if not: "No API key configured for the log server. Contact your org admin."
- Forwarding script exists at `{apps_path}/forward-bug.py` → if not: "The forwarding script is missing. The collection may need to be reinstalled."
- Python 3 is available for running the forwarding script → if not: "Python 3 is required for forwarding bugs. Please install it."

---

## Parameters

No member-defined parameters. All configuration is inherited from collection setup.

---

## Setup Completion

1. Validate remote filesystem access.
2. Verify the member's org role is in `admin_roles`.
3. Verify the auth key file exists.
4. Verify the forwarding script exists and is executable.
5. Register entry in `member-index.json` with alias `@ai:forward-bug`.
6. Confirm to member: "Forward Bug is ready. Say '@ai:forward-bug' to forward a bug report to agent-index."

---

## Upgrade Behavior

### Preserved Responses
- None (no member-specific parameters)

### Reset on Upgrade
- None

### Requires Member Attention
- If the log server URL or auth key changes, the admin updates those via collection setup — no member action needed.

### Migration Notes
- v1.0 → future versions: migration notes will be added here as new versions are published.
