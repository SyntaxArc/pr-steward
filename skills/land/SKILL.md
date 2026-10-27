---
name: land
description: >-
  Merge several PRs in order: rebase each on its base, resolve append-only conflicts, run gates, wait for checks, merge, verify. Use for "merge these PRs in order", "land the PRs", "land #12 #13 #14".
---

# Land

Landing PRs that touch shared files (changelog, README, tables) means rebase, gates, CI wait and merge, once per PR. `scripts/land.sh` does it in order. GitHub only for now: on GitLab, use `merge-pr` per MR.

Host commands: `${CLAUDE_PLUGIN_ROOT}/reference/host-commands.md`. Merge rules come from `merge-pr`; `.pr-steward.json` `mergeStrategy` is honoured.

## Steps

1. Confirm the PR list and the order with the user. Do not guess either.
2. Run from the repo: `${CLAUDE_PLUGIN_ROOT}/scripts/land.sh PR [PR...]`.
3. The script, per PR: fetches, rebases the head on its base in a temp worktree, union-resolves append-only conflicts (changelog bullets, table rows), runs the project gates, pushes with `--force-with-lease`, waits for checks, merges, reads the state back as MERGED, then deletes the remote head branch.
4. Report each PR: merged, or the exact stop reason (conflict file, failed check, gate output).
5. On a stop, leave the remaining PRs untouched and ask the user how to continue.

## Do not

- Merge a red, pending or conflicting PR.
- Resolve a conflict that is not append-only by guessing: stop and report it.
- Trust the merge exit code: the script reads the state back.
- Delete a branch before the PR shows MERGED.
