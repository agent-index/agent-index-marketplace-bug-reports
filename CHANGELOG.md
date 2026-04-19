# Changelog

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
