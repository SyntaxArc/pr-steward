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
3. Merge: `gh pr merge <N> --merge` (use the strategy the repo already uses; check `git log` for merge vs squash).
4. Verify the linked issue: closed only if every item is ticked; otherwise `gh issue reopen <N>`.
5. Delete the branch and sync the default branch locally.

## Do not

- Merge with red or pending checks.
- Skip the issue check after merge.
