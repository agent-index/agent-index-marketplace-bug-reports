---
name: bug-reports-tutorial
type: skill
version: 1.0.0
collection: bug-reports
description: Explains the bug-reports collection to members — its concepts, workflows, and how to report bugs and understand the admin triage process — through a guided tour or targeted answers to specific questions.
stateful: false
always_on_eligible: false
dependencies:
  skills: []
  tasks: []
external_dependencies: []
---

## About This Skill

The bug-reports collection provides a structured workflow for reporting, triaging, and escalating bugs to the agent-index project. Members encounter it when they want to submit a bug, and admins encounter it when managing the shared bug log. This skill explains the system — it does not perform operations.

### When This Skill Is Active

When invoked, Claude shifts into explanatory mode. The skill remains active for the tutorial conversation.

### What This Skill Does Not Cover

This skill covers the bug-reports collection's concepts and workflows. It does not cover troubleshooting filesystem issues. It does not cover the agent-index project's bug triage process beyond escalation. It does not cover internal file format details.

---

## Directives

### Behavior

When invoked, determine whether the member wants a guided tour or has a specific question.

For a guided tour: run the structured tour sequence. Check in after each topic.

For a specific question: answer directly.

Read the collection setup responses before responding, so examples reflect the configured bug log path and severity levels.

### Guided Tour Sequence

Five topics in order. After each, check in.

**Topic 1: What the bug-reports collection does**

The bug-reports collection gives your org a way to track bugs systematically. Any member can report a bug they encounter — in any collection, in agent-index-core itself, or anywhere in the system. Those reports go to a shared log that your org admins can review, organize, and selectively forward to the agent-index team.

Without a structured bug log, bugs get reported in chat, emails, or notes, and then they get lost. With this collection, every bug is captured, tracked, and visible to the people who need to see it.

The workflow is simple: members report, admins review and triage, admins forward to agent-index when needed.

**Topic 2: Filing a bug report**

When you encounter a bug, say `@ai:report-bug`. Claude will interview you about what happened — which collection, what went wrong, what you expected, how to reproduce it, and how severe it is. You answer conversationally, one question at a time.

After you answer, Claude summarizes the report back to you for confirmation. If it looks right, the report gets written to the shared bug log where your org admins can see it. You don't need to worry about formatting or organizing — Claude handles all of that.

Bug reports require no special permissions — any member can file one.

You can file a bug against any collection, even ones that aren't installed in your org. You can also report bugs in agent-index-core itself.

**Topic 3: Viewing and triaging bugs**

This is the admin side. Admins run `@ai:view-bugs` to access the shared bug log. They see a summary of all bugs — how many are open, how many are critical, which collections have the most reports. They can filter by status (open, acknowledged, forwarded, closed), severity (critical, high, medium, low), collection, or reporter. They can drill into any bug to see the full details.

Admins can also triage bugs — mark them as acknowledged (we've seen this), update the status, and add notes explaining what's being done about it. These notes are visible to everyone and help members understand that their report is being tracked.

The view-bugs skill is admin-only — only members whose org role matches the configured admin_roles can use it.

**Topic 4: Forwarding bugs to agent-index**

When your org wants to escalate a bug to the agent-index team, an admin runs `@ai:forward-bug` to send the report upstream. The task packages the bug into the format the agent-index log server expects, authenticates, and sends it.

Once a bug is forwarded, it's marked as such in your shared log. The admin notes field will show when it was forwarded and what the upstream server reference is.

Forwarding is admin-only and always requires explicit confirmation before sending.

**Topic 5: Making the system work**

The system only works if two things happen: members report bugs when they find them, and admins review reports on a regular cadence.

As a member: When you hit something broken, report it immediately. Don't wait for a "good time" or assume someone else noticed it. The bug log is where broken things go, not chat. Include as much context as you can — error messages, what you were trying to do, whether it's reproducible. This makes it much easier for admins to understand and forward.

As an admin: Check the bug log regularly. Acknowledge reports so members know you've seen them. Leave notes so people understand what's happening. Forward critical issues quickly. Close bugs that are false alarms or already fixed.

If you have questions about a specific bug, you can always ask the admin — they can add notes visible to everyone.

---

## Directives

### Invocation

When the member invokes this skill:

1. **Determine mode.** Is the member asking for a guided tour ("walk me through it," "how does this work," "I'm new to this," bare invocation) or a specific question?

2. **Guided tour:** Run the five-topic sequence above. After each topic, ask: "Does that make sense, or would you like me to go deeper on anything?" Let the member move at their own pace.

3. **Specific question:** Answer directly and completely. After answering, ask if they have related questions.

4. **Concrete examples:** Use the member's configured parameters. If you can reference configured severity levels or the shared bug log path, do so.

After the tour or question: "Your main command is `@ai:report-bug` to submit a bug report. If you're an admin, `@ai:view-bugs` to review the log, and `@ai:forward-bug` to escalate bugs. Any other questions?"

### Answering Specific Questions

Common patterns:

**"How do I report a bug?"** — Name `@ai:report-bug` and briefly explain the interview workflow. Mention that any member can use it.

**"Who can view bugs?"** — Explain that `@ai:view-bugs` is admin-only, based on your org's configured admin roles. Direct them to an admin if they need to see the log.

**"What goes in a bug report?"** — Explain the fields: which collection, title, what happened, what you expected, steps to reproduce, severity, and optional context.

**"What's the difference between {status A} and {status B}?"** — Explain the status transitions: open (just reported), acknowledged (admin has seen it), forwarded (sent to agent-index), closed (resolved or duplicate).

**"Can I do {something}?"** — Honest answer with how.

### Style & Tone

Practical, concrete, conversational. Use examples from realistic development scenarios. Avoid jargon — this is a simple reporting system, not an enterprise tool.

### Constraints

Do not perform operations while in tutorial mode. Direct to the appropriate `@ai:` command.

Do not provide deep technical details about JSON schemas or remote filesystem operations.

### Edge Cases

If confused: slow down, rebuild from the last clear concept.

If invoked mid-task: brief targeted answer, step back.
