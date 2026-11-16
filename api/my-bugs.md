---
name: my-bugs
type: skill
version: 1.0.0
collection: bug-reports
description: Shows a member the bugs they reported and what happened to them — the org's own status and, for bugs forwarded to agent-index, agent-index's status, its note, any question waiting for the member, and the release that fixes it. The member can answer a question from here.
stateful: true
always_on_eligible: false
dependencies:
  skills: []
  tasks: []
external_dependencies:
  - Remote filesystem access
---

## About This Skill

A member who reports a bug usually never hears about it again. My Bugs closes that loop for **the member's own bugs only** (bug platform decision A): the full bug list stays with admins in `view-bugs`.

For each of the member's bugs it shows the org's status (open, acknowledged, forwarded, closed) and, once an admin has forwarded it to agent-index, agent-index's side: in review, needs more information, accepted, fixed (waiting for release), fixed and released — with the version and whether the org already has it — or closed as won't do, duplicate ("known issue"), can't reproduce, or works as intended, plus any note agent-index wrote for the org. If agent-index asked a question, the member can answer it here; the admin's `view-bugs` sends the answer.

### When This Skill Is Active

"Show my bugs", "what happened to my bug", "any news on my bugs", "did they fix the bug I reported", "answer agent-index's question about my bug".

### What This Skill Does Not Cover

- Reporting a bug (`report-bug`) or adding detail to one (`update-bug`).
- Anyone else's bugs. Admins use `view-bugs`.
- Forwarding to agent-index (an admin decision, `forward-bug`).

---

## Directives

### Behavior

Show the member's bugs compactly, newest first, with what changed in plain words; offer to answer any waiting question; write nothing else.

### Workflow

**Step 1 — Configuration and identity.** As `update-bug` Step 1 (same id-anchor rules on Google Drive, path reads on OneDrive): read org-config, the `bug-reports` setup responses (`bug_log_path`), and the members registry for the current member's `member_hash` and `display_name`.

**Resolve the bug log location — `{bug_log}` (1.5.0, bug platform finding 38).** `bug_log_path` is an org path such as `/shared/bug-reports/`. On gdrive, address it through org-config's `resource_ids.shared_root`: `/shared/{rest}` becomes `id:{shared_root}/{rest}` (no trailing slash), and every `{bug_log}/...` read, list and write in this file uses that id anchor. Never use the bare `/shared/...` path on gdrive: for a member outside the Shared Drive it fails with `BACKEND_ERROR` / `FILE_NOT_FOUND` (core runtime-reference.md § "Addressing: Owned Content and Sharing", `memberpathreads`). If `shared_root` is missing, halt and name it. On OneDrive, `{bug_log}` is `bug_log_path` as written, without the trailing slash.

**Step 2 — Find the member's bugs.** Read `{bug_log}/bug-manifest.json` via `aifs_read` and keep entries whose `reporter.member_hash` (manifest entries copy the bug file's `reporter` block; accept a flat `reporter_hash` too, for older manifests) is the member's hash. Read each of those bug files (`{bug_log}/bugs/{id}.md`). Bugs filed since an admin last ran `view-bugs` may not be in the manifest yet: say "If a bug you filed recently isn't here, give me its ID" and accept an ID directly (check `reporter.member_hash` before showing it).

**Step 3 — Status comes from the bug files (decision 50).** Members never read the org's log-server key (`config/auth-key.txt`) and never call the log server. agent-index's side of each bug is what the org admin's `view-bugs` last saved in the bug file's `upstream` block. Show it with "(as of {synced_at})" when `synced_at` is more than a day old. Don't try to refresh it.

**Step 4 — Show.** One line per bug, newest first:

```
20261113-8d20ea22-…  "Projects list is empty after update"   forwarded · agent-index: fixed in projects 4.4.4 (your org has 4.4.3 — ask an admin to publish updates)
20261102-8d20ea22-…  "Digest shows the wrong week"            forwarded · agent-index: ❓ waiting for your answer
20261020-8d20ea22-…  "Typo in tutorial"                       closed
```

Version wording follows `view-bugs` (org version from org-config for collections, `/shared/dist/manifest.json` for core and adapters). For a duplicate: "known issue — agent-index is tracking it with an existing report". For `content_deleted`: "details removed under agent-index's retention rule". For status `deleted`: "deleted at your org's request". Then show any agent-index note for the org, and any waiting question in full. Never show `upstream.token`.

**Step 5 — Answer a question (only if the member wants to).** Show their answer back and ask "Add this answer to your bug? Your org admin's bug list sends it to agent-index." On yes, append to the member's own bug file under `### Replies` (create the section at the end if missing) `- **{DATE} ({display_name}):** {answer} (to send)`, and write it back via `aifs_write`. Members already write their own bug files (`update-bug`); this is the only write this skill makes. Then say: "Saved. It goes to agent-index the next time your admin opens the bug list (`view-bugs`); I'll show it as sent after that." An entry ending "(sent to agent-index)" was already sent.

### Constraints

- Only the member's own bugs (`reporter.member_hash` = the member's hash). Never list or open anyone else's, even by ID.
- Write only the `### Replies` section of the member's own bug file. Never change status, frontmatter or other sections, and never write the manifest.
- Never read `config/auth-key.txt`, never call the log server, and never show, copy or note `upstream.token`.
- Never send an answer without showing it and getting the member's yes.
- Use `aifs_read` / `aifs_write` for shared data; native Write only for the temporary local files, which are deleted after use.

### Edge Cases

- **No bugs** → "You haven't reported any bugs yet. Say 'report a bug' if something's wrong."
- **Not yet forwarded** → show the org status only; don't speculate about whether it will be.
- **Forwarded before the org updated to 1.5.0** and not yet linked → "forwarded — agent-index status appears after your admin next opens the bug list".
- **Unlinked** (`upstream.status: unlinked`) → "forwarded — agent-index couldn't link this older report; ask your admin".

### Error Handling

- Remote filesystem unavailable: "I couldn't read the bug log. Check your connection or run '@ai:member-bootstrap'."
- Manifest missing: ask for the bug ID directly.

### Outputs

Answers in chat; at most one appended reply in the member's own bug file.
