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

For each of the member's bugs it shows the org's status (open, acknowledged, forwarded, closed) and, once an admin has forwarded it to agent-index, agent-index's side: in review, needs more information, accepted, fixed (waiting for release), fixed and released — with the version and whether the org already has it — or closed as won't do, duplicate ("known issue"), can't reproduce, or works as intended, plus any note agent-index wrote for the org. If agent-index asked a question, the member can answer it here.

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

**Step 1 — Configuration and identity.** As `update-bug` Step 1 (same id-anchor rules on Google Drive, path reads on OneDrive): read org-config, the `bug-reports` setup responses (`bug_log_path`, `log_server_url`), and the members registry for the current member's `member_hash` and `display_name`.

**Resolve the bug log location — `{bug_log}` (1.5.0, bug platform finding 38).** `bug_log_path` is an org path such as `/shared/bug-reports/`. On gdrive, address it through org-config's `resource_ids.shared_root`: `/shared/{rest}` becomes `id:{shared_root}/{rest}` (no trailing slash), and every `{bug_log}/...` read, list and write in this file uses that id anchor. Never use the bare `/shared/...` path on gdrive: for a member outside the Shared Drive it fails with `BACKEND_ERROR` / `FILE_NOT_FOUND` (core runtime-reference.md § "Addressing: Owned Content and Sharing", `memberpathreads`). If `shared_root` is missing, halt and name it. On OneDrive, `{bug_log}` is `bug_log_path` as written, without the trailing slash.

**Step 2 — Find the member's bugs.** Read `{bug_log}/bug-manifest.json` via `aifs_read` and keep entries whose `reporter_hash` is the member's hash. Read each of those bug files (`{bug_log}/bugs/{id}.md`). Bugs filed since an admin last ran `view-bugs` may not be in the manifest yet: say "If a bug you filed recently isn't here, give me its ID" and accept an ID directly (check `reporter.member_hash` before showing it).

**Step 3 — Fresh status from agent-index (best effort).** For forwarded bugs with `upstream.token`:
1. Read the org's log-server key from `{bug_log}/config/auth-key.txt` via `aifs_read`. If the read is refused or the file is missing, skip to Step 4 and show saved values (members may not be able to read the key; admins' `view-bugs` keeps the saved values current).
2. Write the key and `[{"id": upstream.id, "token": upstream.token}, ...]` to temporary local files (native Write) and run:
   ```bash
   python {apps_path}/upstream.py --server-url "{log_server_url}" --key-file "{temp_key}" status --bugs-file "{temp_bugs}"
   ```
3. Use the answers for display only. **Do not write them back** — keeping the files current is `view-bugs`' job. Delete the temporary files.
4. On exit 2/3/4/5: show saved values with "(as of {synced_at})" and say once "Couldn't check with agent-index just now."

**Step 4 — Show.** One line per bug, newest first:

```
20261113-8d20ea22-…  "Projects list is empty after update"   forwarded · agent-index: fixed in projects 4.4.4 (your org has 4.4.3 — ask an admin to publish updates)
20261102-8d20ea22-…  "Digest shows the wrong week"            forwarded · agent-index: ❓ waiting for your answer
20261020-8d20ea22-…  "Typo in tutorial"                       closed
```

Version wording follows `view-bugs` (org version from org-config for collections, `/shared/dist/manifest.json` for core and adapters). For a duplicate: "known issue — agent-index is tracking it with an existing report". For `content_deleted`: "details removed under agent-index's retention rule". For status `deleted`: "deleted at your org's request". Then show any agent-index note for the org, and any waiting question in full. Never show `upstream.token`.

**Step 5 — Answer a question (only if the member wants to).** Show their answer back and ask "Send this to agent-index?". On yes:
1. If Step 3.1 could not read the key, say "I can't reach agent-index from your account — I've added your answer to the bug so your admin can send it" and append it under a `### Replies` section of the member's own bug file (Step 5.4), then stop.
2. Write the key, the bug's `upstream.token` and the answer to temporary local files and run `upstream.py … reply --id "{upstream.id}" --token-file … --member-hash "{member_hash}" --text-file …`. Delete the temporary files.
3. On success: "Sent. agent-index will see your answer." On 404: "agent-index doesn't recognise this bug any more." On 409: "This bug's details were removed at agent-index, so it can't take replies." On 2/3/4: "Couldn't reach agent-index; I've saved your answer to the bug for your admin."
4. In every case, append to the member's own bug file under `### Replies` (create the section at the end if missing): `- **{DATE} ({display_name}):** {answer}` — and, if sent, " (sent to agent-index)". Write it back via `aifs_write`. Members already write their own bug files (`update-bug`); this is the only write this skill makes.

### Constraints

- Only the member's own bugs (`reporter.member_hash` = the member's hash). Never list or open anyone else's, even by ID.
- Write only the `### Replies` section of the member's own bug file. Never change status, frontmatter or other sections, and never write the manifest.
- Never show, copy or note `upstream.token` or the org's key.
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
