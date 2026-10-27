---
name: open-pr
description: >-
  Create a focused branch, commit with conventional commits, and open a labeled PR/MR that references its issue with Closes or Part of. Use for "open a PR", "send this for review", "fix issue #N".
---

# Open PR

## Steps

1. Read the issue and its checklist. Pick the single chunk this PR completes.
2. Pick the base. Normal PR: the working branch (ask the user: `development`, `main` or `master`, unless rules or the conversation say). Chunk of a multi-PR issue: the issue's integration branch (create it from the working branch with `split-issue` if missing). Branch from the base: `feat|fix|chore|ci|refactor/<topic>`. Check project rules for forbidden prefixes.
3. Run the project gates first (format, lint, tests; see `AGENTS.md`/`Makefile`).
4. Commit: conventional commits (`feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`, `ci`), imperative subject, reason in body. Focused commits only.
5. Push and open: `gh pr create --title ... --body-file ... --label ...` (GitLab: `glab mr create`).
6. PR body: what changed, why, how tested, then **exactly one** reference line:
   - chunk PR into an integration branch: `Part of #N`
   - final PR from the integration branch to the working branch: `Closes #N`
   - single-PR issue: `Closes #N`
7. Labels: copy from the issue.
8. Final PR only: ask the user who to assign it to (GitHub login or name), then pass `--assignee <login>` (GitLab: `--assignee`). Never merge it; the assignee reviews and merges.
9. Run `tick-checklist` before merge if checks already pass.

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
