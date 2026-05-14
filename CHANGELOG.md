# Changelog

## [1.2.0] — 2026-05-13

### Fixed

- **`view-bugs` 1.1.0 → 1.2.0: always reconciles `bug-manifest.json` from individual bug files on read** (closes bug `20260513-8d20ea22`). Pre-1.2.0 trusted the manifest as a cache; in practice writers (this skill's own status-update path, `report-bug`, ad-hoc edits via other sessions) didn't reliably keep the manifest in sync with the per-bug files. Result: a session reading the manifest could miss recently-added bugs and see stale `status` values for resolved ones — observed live on 2026-05-13 where the manifest reported 10 "open" when reality was 0. New Step 2 in view-bugs reconciles before rendering: list `{bug_log_path}/bugs/`, read each `.md`, parse frontmatter, rebuild the canonical bugs list, diff against the on-disk manifest, write back if different. Cost: bounded N reads per invocation (10-50 for typical installs).

### Notes

- `view-bugs` skill version bumped 1.1.0 → 1.2.0. All API manifests' `collection_version` bumped 1.1.1 → 1.2.0.

---


## [1.1.1] — 2026-04-19

### Added
- **Natural language trigger phrases in `collection.json`.** API entries now include trigger arrays that map conversational phrases to capabilities, powering the routing layer introduced in agent-index-core 3.0.5. Members can say things like "report a bug" or "show bugs" instead of using `@ai:` alias syntax. Triggers are customizable per-member via `routing.json`.

## [1.1.0] — 2026-04-02

### Added
- `bug-reports-tutorial` skill — explains bug-reports collection concepts, workflows, member reporting, and admin triage process

## [1.0.0] — 2026-04-01

### Added
- `report-bug` task — member-facing bug submission with guided interview
- `view-bugs` skill — admin interface for browsing, filtering, and triaging bugs
- `forward-bug` task — forward bugs to the agent-index log collection server
- Collection setup with configurable admin roles, severity levels, and log server endpoint
- Shared markdown bug log with YAML frontmatter and JSON manifest index
- Python forwarding script (`forward-bug.py`) for HTTP delivery to log collector
