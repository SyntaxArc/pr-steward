---
name: split-issue
description: >-
  Split a large issue or finding into PR-sized chunks, either as a checklist with Part-of PRs or as several issues. Use for "this is too big", "break this down", "plan the PRs".
---

# Split Issue

One PR moves one small chunk, never a whole plan.

Host commands for `gh` and `glab`: `${CLAUDE_PLUGIN_ROOT}/reference/host-commands.md`. Detect the host from `git remote get-url origin`.

## Choose a shape

- **Checklist**: one issue, several PRs straight to the working branch. Each PR says `Part of #N`; only the last says `Closes #N`. Use only when the user does not want an integration branch.
- **Checklist + integration branch**: one issue, several PRs, default for a multi-PR checklist. Chunk PRs merge into an integration branch; one final PR goes to the working branch with `Closes #N` (see below).
- **Several issues**: one issue per chunk, each closed by its own PR. Use when chunks ship independently or have different labels/owners.

## Steps

1. Read the issue.
2. Cut chunks so each is reviewable alone, passes checks alone, and leaves the repo working (no half-migrations).
3. Order chunks; note dependencies ("blocked by #M").
4. Checklist shape: edit the issue body with the host command, adding one `- [ ]` per chunk.
5. Several-issues shape: create child issues (use `new-issue`), then link them in the parent checklist as `- [ ] #M`. On GitHub, add them as sub-issues when available; GitLab renders `- [ ] #M` as a task list.
6. Copy the parent labels to each child.

## Integration branch

For the checklist shape:

1. Ask the user which branch is the **working branch** (`development`, `main` or `master`) unless project rules or the conversation already say.
2. Create the integration branch from the working branch (`feat|fix|chore|ci/<topic>`) and push it.
3. Note the integration branch in the issue body, so every chunk PR targets it.

## Parallel plan

For two or more chunks:

1. List the files each chunk touches.
2. Mark chunks with disjoint files **parallel-safe**. Chunks sharing a file are **sequential**; order them by dependency.
3. Recommend one subagent per parallel-safe chunk, each in its own git worktree off the integration branch (or the working branch when there is none).
4. Keep README and changelog edits for the last chunk's PR only.
5. Subagents must not edit the issue body. The main session ticks items once, so edits do not overwrite each other.
6. The main session rebases and merges chunk PRs in order.

Record the plan in the issue body, one line per chunk: `- [ ] <chunk> (files: a, b; parallel-safe | after <chunk>)`.
