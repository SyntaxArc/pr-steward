---
name: split-issue
description: >-
  Split a large issue or finding into PR-sized chunks, either as a checklist with Part-of PRs or as several issues. Use for "this is too big", "break this down", "plan the PRs".
---

# Split Issue

One PR moves one small chunk, never a whole plan.

## Choose a shape

- **Checklist**: one issue, several PRs straight to the working branch. Each PR says `Part of #N`; only the last says `Closes #N`. Use only when the user does not want an integration branch.
- **Checklist + integration branch**: one issue, several PRs, default for a multi-PR checklist. Chunk PRs merge into an integration branch; one final PR goes to the working branch with `Closes #N` (see below).
- **Several issues**: one issue per chunk, each closed by its own PR. Use when chunks ship independently or have different labels/owners.

## Steps

1. Read the issue: `gh issue view <N>`.
2. Cut chunks so each is reviewable alone, passes checks alone, and leaves the repo working (no half-migrations).
3. Order chunks; note dependencies ("blocked by #M").
4. Checklist shape: edit the issue body with `gh issue edit <N> --body-file ...` adding one `- [ ]` per chunk.
5. Several-issues shape: create child issues (use `new-issue`), then link them in the parent checklist as `- [ ] #M`. On GitHub, add them as sub-issues when available.
6. Copy the parent labels to each child.

## Integration branch

For the checklist shape:

1. Ask the user which branch is the **working branch** (`development`, `main` or `master`) unless project rules or the conversation already say.
2. Create the integration branch from the working branch (`feat|fix|chore|ci/<topic>`) and push it.
3. Note the integration branch in the issue body, so every chunk PR targets it.
