---
name: bug-reports-tutorial-setup
type: setup
version: 1.0.0
collection: bug-reports
description: Setup for the bug-reports-tutorial skill
target: bug-reports-tutorial
target_type: skill
upgrade_compatible: true
---

## Setup Overview

This installs the Bug Reports Tutorial skill. Say '@ai:bug-tutorial' at any time to get a guided walkthrough of how the bug reporting system works or to ask specific questions about filing and managing bugs.

---

## Pre-Setup Checks

None.

---

## Parameters

No member-configurable parameters.

---

## Setup Completion

1. Write the installed instance to `/members/{member_hash}/skills/bug-reports-tutorial/`
2. Write `manifest.json`
3. Write empty `setup-responses.md`
4. Register entry in `member-index.json` with alias `@ai:bug-tutorial`
5. Confirm to member: "Bug Reports Tutorial is installed. Say '@ai:bug-tutorial' anytime to learn how to report bugs."

---

## Upgrade Behavior

### Preserved Responses
N/A.

### Reset on Upgrade
N/A.

### Requires Member Attention
None. The tutorial content updates automatically with the collection — no member action needed.

### Migration Notes
- v1.0 → future versions: migration notes will be added here as new versions are published.
