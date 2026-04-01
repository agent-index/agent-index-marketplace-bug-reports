---
name: view-bugs-setup
type: setup
version: 1.0.0
collection: bug-reports
description: Setup for the view-bugs skill — validates admin role access and remote filesystem connectivity.
target: view-bugs
target_type: skill
upgrade_compatible: true
---

## Setup Overview

View Bugs requires no member-specific configuration. Access is controlled by the `admin_roles` parameter set during collection setup. This setup validates that the member has an admin role and can access the shared filesystem.

---

## Pre-Setup Checks

- Collection setup has been completed (verify `collection-setup-responses.md` exists via `aifs_read`) → if not: "Your org admin needs to complete the bug-reports collection setup first. Contact your admin."
- Remote filesystem is accessible (test with `aifs_auth_status()`) → if not: "Please check your remote filesystem connection or run '@ai:member-bootstrap'."
- Member's org role is in the configured `admin_roles` list → if not: "View Bugs is restricted to admin roles ({admin_roles}). Your current role ({member_role}) does not have access. Contact your org admin if you need access."

---

## Parameters

No member-defined parameters. Access control is inherited from collection setup.

---

## Setup Completion

1. Validate remote filesystem access.
2. Verify the member's org role is in `admin_roles`.
3. Verify the bug log and manifest exist at the configured `bug_log_path` via `aifs_read`.
4. Register entry in `member-index.json` with alias `@ai:view-bugs`.
5. Confirm to member: "View Bugs is ready. Say '@ai:view-bugs' to browse and manage bug reports."

---

## Upgrade Behavior

### Preserved Responses
- None (no member-specific parameters)

### Reset on Upgrade
- None

### Requires Member Attention
- If the admin changes `admin_roles` and the member's role is removed, the skill will deny access at invocation time.

### Migration Notes
- v1.0 → future versions: migration notes will be added here as new versions are published.
