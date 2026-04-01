---
name: report-bug-setup
type: setup
version: 1.0.0
collection: bug-reports
description: Setup for the report-bug task — minimal member-level setup since all configuration is org-mandated at collection install time.
target: report-bug
target_type: task
upgrade_compatible: true
---

## Setup Overview

Report Bug requires no member-specific configuration. All parameters (bug log path, severity levels) are org-mandated and set during collection setup. This setup simply validates that the collection is properly installed and the member can access the shared filesystem.

---

## Pre-Setup Checks

- Collection setup has been completed (verify `collection-setup-responses.md` exists in the collection's setup directory via `aifs_read`) → if not: "Your org admin needs to complete the bug-reports collection setup first. Contact your admin."
- Remote filesystem is accessible (test with `aifs_auth_status()`) → if not: "Please check your remote filesystem connection or run '@ai:member-bootstrap'."

---

## Parameters

No member-defined parameters. All configuration is inherited from the collection setup.

---

## Setup Completion

1. Validate remote filesystem access.
2. Verify the bug log and manifest exist at the configured `bug_log_path` via `aifs_read`.
3. Register entry in `member-index.json` with alias `@ai:report-bug`.
4. Confirm to member: "Bug Reports is ready. Say '@ai:report-bug' anytime to submit a bug."

---

## Upgrade Behavior

### Preserved Responses
- None (no member-specific parameters)

### Reset on Upgrade
- None

### Requires Member Attention
- None — org-level changes (like new severity levels) are picked up automatically at runtime.

### Migration Notes
- v1.0 → future versions: migration notes will be added here as new versions are published.
