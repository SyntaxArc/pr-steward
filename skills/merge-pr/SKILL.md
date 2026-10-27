---
name: merge-pr
description: >-
  Watch PR/MR checks, merge once green, then verify the linked issue state. Use for "merge it", "land this PR", "merge when checks pass".
---

# Merge PR

Repos without required checks merge immediately on `--auto`, so watch checks first.

## Steps

1. `gh pr checks <N> --watch` (GitLab: `glab ci status --live`). Stop and report any failure with the failing job and last error line.
2. Confirm the checklist item is ticked (`tick-checklist`).
3. Chunk PR into an integration branch: merge automatically once checks are green and the item is ticked. Final PR to the working branch: do not merge; confirm it is assigned and leave it to the assignee, unless the user explicitly says to merge it.
4. Merge: `gh pr merge <N> --merge` (use the strategy the repo already uses; check `git log` for merge vs squash).
5. Verify the linked issue: closed only if every item is ticked; otherwise `gh issue reopen <N>`.
6. Delete the head branch only after the PR shows MERGED (never before: deleting the head of an open PR closes it). Delete the integration branch after its final PR merges. Sync the working branch locally.

## Do not

- Merge with red or pending checks.
- Delete a branch before confirming the PR state is MERGED.
- Skip the issue check after merge.
