# Bug Reports — Roadmap

## Current State

v1.0.0 provides the core bug reporting loop: submit, view, forward. Each bug report is stored as an individual markdown file (`/shared/bug-reports/bugs/{id}.md`) with a JSON manifest for indexing. Forwarding sends reports to the agent-index log collection server via a Python script.

## Known Limitations

- **Manifest as single point of failure.** The manifest (`bug-manifest.json`) is the primary index. If it becomes corrupt, the system can reconstruct it by scanning all files in `bugs/`, but this requires reading every file. For orgs with hundreds of bugs, a rebuild could be slow.

- **Soft access control.** Admin role checking is advisory — it happens at invocation time in the agent, not enforced by the filesystem. A technically savvy member could read the shared bug log directly via `aifs_read`. This matches the rest of agent-index's trust model but means bug reports are not truly private from non-admin members.

- **No duplicate detection.** If two members report the same bug independently, both entries are recorded separately. Admins must manually identify and close duplicates.

- **No attachments.** Members can describe error messages and behavior but can't attach screenshots, log files, or other binary artifacts to a bug report.

## Known Bugs

None yet.

## Wishlist

### v1.1 — Quality of life
- Search within bug descriptions (not just titles and metadata)
- Batch forwarding — forward multiple bugs in a single operation
- Duplicate detection hints — when a new bug is submitted, check for similar titles/collections and suggest possible duplicates to the reporter
- Bug statistics — show trends over time (bugs per week, mean time to forward, most-reported collections)

### v1.2 — Richer reports
- Attachment support — allow members to reference files (error logs, screenshots) stored at a known path on the remote filesystem
- Bug templates — pre-defined templates for common bug types (crash, data loss, classification error, setup failure) with tailored questions
- Auto-populate collection version — read the installed collection version and include it in the report automatically

### v2.0 — Structural changes (breaking)
- Add webhook support as an alternative to the Python script for forwarding
- Add member notification — notify the original reporter when their bug status changes
- Partition bugs into date-based subdirectories (`bugs/2026/04/`) for filesystem performance at very large scale

## Design Notes

- This collection deliberately does not provide a way for non-admin members to view all bugs. The bug log is shared on the remote filesystem (so technically readable), but the `view-bugs` skill gates on admin roles. This is a product decision: bug triage is an admin responsibility, and giving all members a view of the full bug backlog creates noise without value.

- The collection uses one file per bug from v1.0. This avoids the growing-single-file problem and means viewing or updating a bug only requires reading that one file, not the entire log. The manifest provides the index for listing and filtering without scanning all files.

- Forwarding is intentionally manual (admin-initiated, one bug at a time). Auto-forwarding all bugs would flood the log collection server with duplicates, non-bugs, and noise. The admin acts as a quality filter.
