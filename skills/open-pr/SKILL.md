---
name: open-pr
description: >-
  Create a focused branch, commit with conventional commits, and open a labeled PR/MR that references its issue with Closes or Part of. Use for "open a PR", "send this for review", "fix issue #N".
---

# Open PR

## Steps

1. Read the issue and its checklist. Pick the single chunk this PR completes.
2. Branch from the default branch: `feat|fix|chore|ci|refactor/<topic>`. Check project rules for forbidden prefixes.
3. Run the project gates first (format, lint, tests; see `AGENTS.md`/`Makefile`).
4. Commit: conventional commits (`feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`, `ci`), imperative subject, reason in body. Focused commits only.
5. Push and open: `gh pr create --title ... --body-file ... --label ...` (GitLab: `glab mr create`).
6. PR body: what changed, why, how tested, then **exactly one** reference line:
   - last chunk: `Closes #N`
   - any other chunk: `Part of #N`
7. Labels: copy from the issue.
8. Run `tick-checklist` before merge if checks already pass.

## Do not

- Mix unrelated changes or lockfile churn.
- Use `Closes #N` on a non-final chunk.
- Mention AI tools in commits or PR text.
