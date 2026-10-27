---
name: tick-checklist
description: >-
  Tick the finished item in an issue checklist and add a result note plus the next chunk. Use after a PR is ready or merged, or for "update the issue", "update the checklist".
---

# Tick Checklist

A merged PR never leaves its issue checklist stale. Neither GitHub nor GitLab ticks checklist items on merge.

Host commands for `gh` and `glab`: `${CLAUDE_PLUGIN_ROOT}/reference/host-commands.md`. Detect the host from `git remote get-url origin`.

Safe to call from `merge-pr` before the merge: it is idempotent. An item already `[x]` is left unchanged, with no duplicate note or comment.

## Steps

1. Tick the item this PR completes through `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tick.py ISSUE ITEM` (ITEM is the 1-based number or the exact item text) instead of editing the body by hand. It re-reads the body, refuses an empty body or a changed item count, writes once, and verifies by reading back. An item already `[x]` is left unchanged. Add `--host glab` or `--repo OWNER/REPO` when needed.
2. Give the PR link and a one-line result (measured numbers, behavior change) in the comment of step 4, not by rewriting the body.
3. Never write a body that came from a failed or empty fetch.
4. Add a short comment naming the next chunk, if any.
5. All items ticked and the PR used `Closes #N` -> issue closes on merge. Items left unticked after a close -> tick them if done, else reopen with the host command.

When `pr-merged-issue-comment` CI is installed it comments the PR link on the issue; ticking and notes stay manual.
