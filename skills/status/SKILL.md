---
name: status
description: >-
  Print a read-only digest of open issues and PRs/MRs: next checklist item, check state, mergeability, who each waits on. Use for "what's open", "status of the issues", "what is waiting on review".
---

# Status

Read-only. Never create, edit, merge, tick, label or comment. Run list/view commands only.

Host commands for `gh` and `glab`: `${CLAUDE_PLUGIN_ROOT}/reference/host-commands.md`. Detect the host from `git remote get-url origin`.

## Steps

1. List open issues and open PRs/MRs (see host commands).
2. Per issue: read the body, find the first `- [ ]` item. None left -> "all ticked".
3. Per PR/MR: read check state and mergeability. Link it to its issue via `Closes`/`Part of #N` in the body.
4. Name who each item waits on:
   - failing or pending checks -> author
   - conflict or behind -> author
   - green, clean, reviewer requested -> that reviewer
   - green, clean, no reviewer -> "needs a reviewer"
   - draft -> author
   - issue with no open PR -> assignee, or "unassigned"
5. Print one compact digest, no preamble:

```
Issues
#40 feat: add a status skill | next: write skills/status/SKILL.md | PR #45 | waits: author
PRs
#45 feat/status-skill | checks: pass | clean | waits: reviewer @name
```

Group conflicting or failing PRs first. Zero open items: say "nothing open".

## Do not

- Run any command that writes (create, edit, comment, merge, close, label).
- Tick checklist items: that is `tick-checklist`.
- Pad the digest with bodies, logs or history.
