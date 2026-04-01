# Bug Reports Collection

Bug reporting workflow for agent-index orgs. Any member can submit bug reports against any collection. Org admins can view, triage, and selectively forward reports to the agent-index log collection server.

## Included Capabilities

- **report-bug** (task) — Walk through submitting a bug report. Collects collection name, title, description, reproduction steps, and severity. Writes an individual bug file to the shared filesystem and updates the manifest index. Available to all members.

- **view-bugs** (skill) — Interactive admin interface for browsing, filtering, and managing bug reports. Supports filtering by status, severity, collection, and reporter. Admins can update status (open → acknowledged → forwarded → closed), add notes, and search across all reports. Admin roles only.

- **forward-bug** (task) — Forward a selected bug report to the upstream agent-index log collection server. Packages the bug into the log collector's expected JSON envelope, authenticates with the configured API key, and sends via HTTP. Marks the bug as forwarded in the shared log. Admin roles only.

## How It Works

Each bug report is stored as an individual markdown file on the remote filesystem (`/shared/bug-reports/bugs/{id}.md` by default). Each file has YAML frontmatter for structured querying and a markdown body with the full details. A companion manifest file (`bug-manifest.json`) indexes all bugs for fast lookups without reading every file.

The workflow is:
1. Any member runs `@ai:report-bug` to submit a bug
2. An admin runs `@ai:view-bugs` to review, acknowledge, and add notes
3. The admin runs `@ai:forward-bug` to send selected bugs to agent-index

## Prerequisites

- agent-index-core 2.0.0 or later
- agent-index-filesystem MCP server connected (for shared bug log access)
- Python 3 (for the forwarding script)
- At least one org role configured in `org-config.json` (for admin access control)

## Version History

See [CHANGELOG.md](CHANGELOG.md).
