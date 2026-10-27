---
name: merge-pr
description: >-
  Watch PR/MR checks, merge once green, then verify the linked issue state. Use for "merge it", "land this PR", "merge when checks pass".
---

# Merge PR

Repos without required checks merge immediately on `--auto`, so watch checks first.

Host commands for `gh` and `glab`: `${CLAUDE_PLUGIN_ROOT}/reference/host-commands.md`. Detect the host from `git remote get-url origin`.

## Steps

1. Watch checks/pipeline. Stop and report any failure with the failing job and last error line.
2. After checks pass, read mergeability (see host commands). Stop on `DIRTY`/`CONFLICTING` or `BEHIND`: do not merge. Rebase the head branch on the base (`git fetch origin && git rebase origin/BASE`), resolve conflicts with the user, push with `--force-with-lease`, then watch checks again (step 1). Merge only when mergeability is clean.
3. Run `tick-checklist` for this PR's chunk, then confirm the item is `[x]`. Do not only check it: tick it before merging.
4. Chunk PR into an integration branch: merge automatically once checks are green and the item is ticked. Final PR to the working branch: do not merge; confirm a reviewer is named and leave it to them, unless the user explicitly says to merge it.
5. Merge with the strategy the repo already uses (check `git log` for merge vs squash).
6. Verify the linked issue against the checklist: closed only if every item is ticked. Closed with unticked items -> tick the finished ones or reopen it. Never leave a closed issue with unticked items unless the user says so.
7. Delete the head branch only after the PR shows MERGED (never before: deleting the head of an open PR closes it). Delete the integration branch after its final PR merges. Sync the working branch locally.

## Do not

- Merge with red or pending checks.
- Merge a conflicting or behind PR, or force-push without `--force-with-lease`.
- Delete a branch before confirming the PR state is MERGED.
- Skip the issue check after merge.
- Merge with the checklist item unticked.
