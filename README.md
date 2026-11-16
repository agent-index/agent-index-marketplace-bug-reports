# Bug Reports Collection

Bug reporting workflow for agent-index orgs. Any member can submit bug reports against any collection and follow what happened to their own. Org admins can view, triage, and selectively forward reports to agent-index, then see agent-index's status, notes, questions and fix versions for what they forwarded.

## Included Capabilities

- **report-bug** (task) — Walk through submitting a bug report. Collects collection name, title, description, reproduction steps, and severity. Writes an individual bug file to the shared filesystem (the bug file is the source of truth; the admin-only view-bugs skill rebuilds the index from bug files — report-bug never writes the index). Available to all members.

- **view-bugs** (skill) — Interactive admin interface for browsing, filtering, and managing bug reports. Supports filtering by status, severity, collection, and reporter. Admins can update status (open → acknowledged → forwarded → closed), add notes, and search across all reports. Since 1.5.0 it also shows agent-index's status for forwarded bugs, which release fixes them and whether the org has it, and lets admins answer agent-index's questions. Admin roles only.

- **forward-bug** (task) — Forward a selected bug report to the upstream agent-index log collection server. Packages the bug into the log collector's expected JSON envelope (member IDs only — no names or email addresses), authenticates with the configured API key, and sends via HTTP. Marks the bug as forwarded in the shared log and saves agent-index's reference and status token for it; if the send fails, records the failed attempt on the bug so it can be resent with "retry failed forwards". Admin roles only.

- **my-bugs** (skill, 1.5.0) — "Show my bugs": a member's own bugs with the org's status and agent-index's status, note, question and fix version. Members can answer agent-index's questions here; the admin's view-bugs sends the answers and keeps the status current. Own bugs only (a view: the bug log itself is readable by all members).

- **bug-reports-tutorial** (skill) — Guided walkthrough of how the bug reporting system works. Explains concepts, workflows, and answers specific questions about filing and managing bugs. Say `@ai:bug-tutorial` to start.

## How It Works

Each bug report is stored as an individual markdown file on the remote filesystem (`/shared/bug-reports/bugs/{id}.md` by default). Each file has YAML frontmatter for structured querying and a markdown body with the full details. A companion manifest file (`bug-manifest.json`) indexes all bugs for fast lookups without reading every file.

The workflow is:
1. Any member runs `@ai:report-bug` to submit a bug
2. An admin runs `@ai:view-bugs` to review, acknowledge, and add notes
3. The admin runs `@ai:forward-bug` to send selected bugs to agent-index
4. agent-index triages them; admins see progress in `@ai:view-bugs`, reporters in "show my bugs", and either can answer agent-index's questions

Forwarded bugs carry agent-index's reference and a per-bug status token in their frontmatter (`upstream:`). The token only unlocks that one bug's status at agent-index; it is never shown.

## Prerequisites

- agent-index-core 2.0.0 or later
- Remote filesystem access via `aifs_*` tools (for shared bug log access)
- Python 3 (for the forwarding and status scripts; standard library only)
- Network access to the log server (`v1.logs.agent-index.ai`; in Cowork, on the network allowlist)
- At least one org role configured in `org-config.json` (for admin access control)

## Version History

See [CHANGELOG.md](CHANGELOG.md).
