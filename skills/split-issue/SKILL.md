---
name: split-issue
description: >-
  Split a large issue or finding into PR-sized chunks, either as a checklist with Part-of PRs or as several issues. Use for "this is too big", "break this down", "plan the PRs".
---

# Split Issue

One PR moves one small chunk, never a whole plan.

## Choose a shape

- **Checklist**: one issue, several PRs. Each PR says `Part of #N`; only the last says `Closes #N`.
- **Several issues**: one issue per chunk, each closed by its own PR. Use when chunks ship independently or have different labels/owners.

## Steps

1. Read the issue: `gh issue view <N>`.
2. Cut chunks so each is reviewable alone, passes checks alone, and leaves the repo working (no half-migrations).
3. Order chunks; note dependencies ("blocked by #M").
4. Checklist shape: edit the issue body with `gh issue edit <N> --body-file ...` adding one `- [ ]` per chunk.
5. Several-issues shape: create child issues (use `new-issue`), then link them in the parent checklist as `- [ ] #M`. On GitHub, add them as sub-issues when available.
6. Copy the parent labels to each child.
