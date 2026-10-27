---
name: open-pr
description: >-
  Create a focused branch, commit with conventional commits, and open a labeled PR/MR that references its issue with Closes or Part of. Use for "open a PR", "send this for review", "fix issue #N".
---

# Open PR

Host commands for `gh` and `glab`: `${CLAUDE_PLUGIN_ROOT}/reference/host-commands.md`. Detect the host from `git remote get-url origin`.

Config (optional `.pr-steward.json`): `${CLAUDE_PLUGIN_ROOT}/reference/config.md`. Read it before asking; ask only for missing keys.

## Steps

1. Read the issue and its checklist. Pick the single chunk this PR completes.
2. Pick the base. Normal PR: the working branch (project rules, then `workingBranch`; ask the user only if neither says: `development`, `main` or `master`). Chunk of a multi-PR issue: the issue's integration branch (create it from the working branch with `split-issue` if missing). Branch from the base: `feat|fix|chore|ci|refactor/<topic>`. Check project rules for forbidden prefixes.
3. Run the project gates first (format, lint, tests; see `AGENTS.md`/`Makefile`).
4. Commit: conventional commits (`feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`, `ci`), imperative subject, reason in body. Focused commits only.
5. Look up an existing PR/MR first: by branch (`gh pr list --head <branch> --state all`) and by issue (search for `#N` in open PRs/MRs). Found: push to the branch, update its labels, assignee and description with the edit command, report its number, and do not create another. Reopen it only if closed and unmerged. Not found: push and open the PR/MR with the host command, with the assignee and reviewer from steps 8-9 (ask the reviewer question before opening).
6. PR body: what changed, why, how tested, then **exactly one** reference line:
   - chunk PR into an integration branch: `Part of #N`
   - final PR from the integration branch to the working branch: `Closes #N`
   - single-PR issue: `Closes #N`
7. Labels: copy from the issue.
8. Assign every PR/MR (chunk, single and final) to the current user: `--assignee @me` (GitLab: `--assignee <username>` from `glab api user`). Do not ask who to assign.
9. Reviewer: `defaultReviewer` if set; else ask who should review (GitHub login or GitLab username). Pass `--reviewer <login>` when known; if the user names no one, skip it. Final PR: ask unless `defaultReviewer` is set. Never merge the final PR; the reviewer reviews and merges.
10. Run `tick-checklist` before merge if checks already pass.

## Hygiene

- Keep each change to one purpose and preserve the user's existing uncommitted changes.
- Keep the PR description current when behavior changes during review.
- Run the project's configured formatter, linter/type checker, targeted tests and security checks before opening; security-sensitive changes (network adapters, auth, cryptography, uploads, secrets/config) need security validation.
- Do not touch changelogs, versions, tags or releases unless the project policy or the user asks.

## Do not

- Mix unrelated changes or lockfile churn.
- Include secrets, generated credentials or large artifacts.
- Use `Closes #N` on a chunk PR; only the final PR or a single-PR issue closes it.
- Open the final PR before every checklist item is ticked.
- Mention AI tools in commits or PR text.
