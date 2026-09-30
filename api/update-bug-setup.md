---
name: update-bug-setup
type: setup
version: 1.0.0
collection: bug-reports
description: Setup for the update-bug task — no member-specific configuration; all config is org-mandated at collection install time.
target: update-bug
target_type: task
upgrade_compatible: true
---

## Setup Overview

Update Bug requires no member-specific configuration. It uses the org-mandated `bug_log_path` from the collection setup. This setup validates install and filesystem access only.

---

## Pre-Setup Checks

- Collection setup completed (verify `collection-setup-responses.md` exists at `id:{folder_id}/setup/collection-setup-responses.md`, where `folder_id` is the `bug-reports` entry in org-config's `installed_collections[]` and org-config is read via `aifs_read("id:{org_config_id}")` using `org_config_id` from the local `agent-index.json`. Never check a bare `/bug-reports/...` path: for a non-Shared-Drive member it resolves to the same-named `/shared/bug-reports` data folder and reports setup as incomplete when it is not) → if not: "Your org admin needs to complete the bug-reports collection setup first."
- Remote filesystem accessible (`aifs_auth_status()`) → if not: "Please check your remote filesystem connection or run '@ai:member-bootstrap'."
- Member write access to `bugs/` has been provisioned by the admin (collaborative-acls.json applied via `@ai:install-collection bug-reports`). If a later write fails with an authorization error, update-bug surfaces the admin-provisioning instruction at runtime.

---

## Parameters

No member-defined parameters. All configuration is inherited from the collection setup.

---

## Setup Completion

1. Validate remote filesystem access.
2. Register entry in `member-index.json` with alias `@ai:update-bug`.
3. Confirm to member: "Update Bug is ready. Say '@ai:update-bug' to add detail to a bug you reported."

---

## Upgrade Behavior

### Preserved Responses
- None (no member-specific parameters)

### Reset on Upgrade
- None

### Requires Member Attention
- None

### Migration Notes
- v1.0.0: initial release.
