---
name: merge-pr
description: >-
  Watch PR/MR checks, merge once green, then verify the linked issue state. Use for "merge it", "land this PR", "merge when checks pass".
---

# Merge PR

Repos without required checks merge immediately on `--auto`, so watch checks first.

Host commands for `gh` and `glab`: `${CLAUDE_PLUGIN_ROOT}/reference/host-commands.md`. Detect the host from `git remote get-url origin`.

Config (optional `.pr-steward.json`): `${CLAUDE_PLUGIN_ROOT}/reference/config.md`. Read it before asking; ask only for missing keys.

## Steps

1. Watch checks/pipeline. Stop and report any failure with the failing job and last error line.
2. After checks pass, read mergeability (see host commands). Stop on `DIRTY`/`CONFLICTING` or `BEHIND`: do not merge. Rebase the head branch on the base (`git fetch origin && git rebase origin/BASE`), resolve conflicts with the user, push with `--force-with-lease`, then watch checks again (step 1). Merge only when mergeability is clean.
3. Run `tick-checklist` for this PR's chunk, which ticks through `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tick.py ISSUE ITEM` instead of editing the body by hand, then confirm the item is `[x]`. Do not only check it: tick it before merging.
4. Size check: run `git diff --shortstat BASE...HEAD` (BASE is the PR base) and count changed files and lines (insertions plus deletions). Above `maxFiles` (default 15) or `maxLines` (default 500) from `.pr-steward.json`: warn the user and suggest `split-issue`. A warning only: never block the merge.
5. Chunk PR into an integration branch: merge automatically once checks are green and the item is ticked. Final PR to the working branch: do not merge; confirm a reviewer is named and leave it to them, unless the user explicitly says to merge it.
6. Merge with `mergeStrategy` if set; else the strategy the repo already uses (check `git log` for merge vs squash); ask only if unclear. Read the state afterwards with the PR/MR state row of the host commands (`gh pr view N --json state`); never trust the command exit code, which can be non-zero even when the PR merged.
7. Verify the linked issue against the checklist: closed only if every item is ticked. Closed with unticked items -> tick the finished ones or reopen it. Never leave a closed issue with unticked items unless the user says so.
8. Clean up only after the PR shows MERGED (never before: deleting the head of an open PR closes it). Skip fork PRs. Delete the remote head branch, then the local branch; if `git worktree list` shows a worktree on it, `git worktree remove` it first. Delete the integration branch after its final PR merges. Then `git fetch --prune` and `git worktree prune`. Never delete the working branch (`workingBranch` if set), `main`/`master`, a `release/*` branch (tags are not branches) or a branch that still has an open PR. Sync the working branch locally.

## Do not

- Merge with red or pending checks.
- Merge a conflicting or behind PR, or force-push without `--force-with-lease`.
- Delete a branch before confirming the PR state is MERGED.
- Delete the working branch, `main`/`master`, a `release/*` branch, a fork PR branch or a branch with an open PR.
- Skip the issue check after merge.
- Merge with the checklist item unticked.
