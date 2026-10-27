---
name: tick-checklist
description: >-
  Tick the finished item in an issue checklist and add a result note plus the next chunk. Use after a PR is ready or merged, or for "update the issue", "update the checklist".
---

# Tick Checklist

A merged PR never leaves its issue checklist stale. Neither GitHub nor GitLab ticks checklist items on merge.

## Steps

1. Fetch body: `gh issue view <N> --json body -q .body > /tmp/body.md` (use the session scratchpad dir, not `/tmp`, when one is set).
2. Change only the item this PR completes: `- [ ]` -> `- [x]`, append the PR link and a one-line result (measured numbers, behavior change).
3. Write back: `gh issue edit <N> --body-file <file>`.
4. Add a short comment naming the next chunk, if any.
5. All items ticked and the PR used `Closes #N` -> issue closes on merge. Items left unticked after a close -> `gh issue reopen <N>`.

When `pr-merged-issue-comment` CI is installed it comments the PR link on the issue; ticking and notes stay manual.
