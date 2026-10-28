# Changelog

## [0.9.2] - 2026-10-28

- `setup-ci`: GitLab `delete-merged-branch` no longer fails when the source branch is already deleted on merge ([#126](https://github.com/SyntaxArc/pr-steward/pull/126), [#125](https://github.com/SyntaxArc/pr-steward/issues/125)).

## [0.9.1] - 2026-10-28

- `setup-ci`: GitLab and GitHub `merged-comment` and `tick-checklist` no longer fail when the MR/PR has no matching reference line ([#123](https://github.com/SyntaxArc/pr-steward/pull/123), [#122](https://github.com/SyntaxArc/pr-steward/issues/122)).

## [0.9.0] - 2026-10-28

- `setup-ci`: GitLab job image configurable via `PR_STEWARD_IMAGE`, default `alpine:3` ([#118](https://github.com/SyntaxArc/pr-steward/pull/118), [#114](https://github.com/SyntaxArc/pr-steward/issues/114)).
- `open-pr`: create the issue with `new-issue` first when none exists ([#115](https://github.com/SyntaxArc/pr-steward/pull/115), [#111](https://github.com/SyntaxArc/pr-steward/issues/111)).
- `setup-ci`: GitLab post-merge jobs run on any branch, not only the default ([#116](https://github.com/SyntaxArc/pr-steward/pull/116), [#112](https://github.com/SyntaxArc/pr-steward/issues/112)).
- `setup-ci`: `delete-merged-branch` keeps long-lived and protected branches ([#117](https://github.com/SyntaxArc/pr-steward/pull/117), [#113](https://github.com/SyntaxArc/pr-steward/issues/113)).
- `setup-ci`: GitLab jobs use a normal `pr-steward` stage, since `.pre`/`.post`-only pipelines never run ([#120](https://github.com/SyntaxArc/pr-steward/pull/120), [#119](https://github.com/SyntaxArc/pr-steward/issues/119)).

## [0.8.0] - 2026-10-28

- `merge-pr` and `land`: merge-queue aware. They detect a queue on the base branch, enqueue with `--auto` and wait for MERGED instead of merging directly.
- Hooks: `PostToolUse` reads back state after PR/MR create and merge; `Stop` warns, without blocking, about unpushed commits, unticked linked-issue items and leftover worktrees.
- Tests: offline smoke tests for `tick.py`, the guard hook and `land.sh` (temp repo, local bare remote, fake `gh`).

## [0.7.1] - 2026-10-28

- Guard: resolves the target repo from `cd`/`pushd` per command segment and from `-R`, and runs the PR lookup in that directory instead of the session cwd. When the directory cannot be resolved and no `-R` is given, the merge is not checked and a warning is shown instead of blocking on the wrong repo.
- `SessionStart` hook lists the skills from the `skills/` directory, so new skills appear in the reminder automatically.

## [0.7.0] - 2026-10-28

- `open-pr`/`merge-pr`: delete the source branch after merge. GitLab `--remove-source-branch` on create; GitHub checks the repo setting and offers to enable it, else `merge-pr` uses `--delete-branch`. Opt out with `deleteBranchOnMerge: false`.
- `scripts/tick.py`: safe checklist tick (refuses empty bodies, keeps the item count, reads back); `tick-checklist` and `merge-pr` use it.
- `land` skill and `scripts/land.sh`: merge several PRs in order with append-only conflict resolution, gates and CI wait.
- `parallel-prs` skill: one subagent per parallel-safe chunk, with a fixed brief.
- `release`: suggests the semver bump from merged PR labels and offers to announce via the `announce` config key.
- `open-pr`, `new-issue`, `merge-pr`, `release`: read back state after create, edit and merge.
- `reference/untrusted-text.md`: issue, PR, review and log text is data; every skill links it and `check_catalog.py` enforces that.
- `open-pr`: links the PR to its issue (`gh issue develop`, GitLab `/relate`) and copies milestone and project.

## [0.6.0] - 2026-10-27

- `merge-pr`: after MERGED, delete the remote and local head branch and its worktree; never the working branch, release branches or branches with an open PR.
- `setup-ci`: `delete-merged-branch` piece (GitHub workflow, GitLab job) for merged same-repo PRs.
- `status`: lists remote branches already merged into the working branch and offers a confirmed bulk delete.
- Hooks: `SessionStart` reminder to use the skills; `PreToolUse` guard for `gh`/`glab` merge and create, rtk-aware, fail-open, `PR_STEWARD_GUARD=off` to disable.
- `backport` skill: cherry-pick a merged PR onto a release branch and open the PR.
- `hotfix` skill: branch from the latest tag, fix, patch release, carry the fix back.
- `status`: idle and awaiting-review filter, and a multi-repo digest from the `repos` config key; `setup-ci` `stale-pr-nudge` piece.
- `split-issue`: tracking issue with linked per-repo issues for one feature across repos.
- `new-issue`: draft an issue from a failing CI run.
- `open-pr` and `merge-pr`: warn when a PR exceeds `maxFiles` or `maxLines` (config).
- CI: the `tick-checklist` templates reopen an issue closed with unticked items.

## [0.5.0] - 2026-10-27

- `review-pr` skill: address review threads, reply, resolve and re-request review.
- `status` skill: read-only digest of open issues, PRs, checks and waiting-on.
- `setup-ci`: `tick-checklist` piece ticks `Part of #N (item K)` and `Closes #N` checklist items after a merge; `open-pr` uses the `(item K)` reference format.
- `split-issue`: lists files per chunk, marks parallel-safe chunks and guides subagents (own worktree, no issue-body edits, docs in the last PR).
- `new-issue`: create issues from review output or TODOs after showing the plan.
- `release`: optional draft of release notes from PRs merged since the last tag.

## [0.4.0] - 2026-10-27

- Optional `.pr-steward.json` (`workingBranch`, `defaultReviewer`, `mergeStrategy`) read by `open-pr`, `merge-pr` and `release`; see `reference/config.md`.
- CI: `check_catalog.py` checks changelog dates and version order.
- `new-issue` asks once for an optional reference link (Jira, Confluence, docs) and adds a `## References` section; issue templates get the same optional field.
- CI: `dependabot-automerge.yml` enables auto-merge on Dependabot semver-patch PRs; minor and major stay manual.
- `setup-ci`: optional `notify` piece posts merged PRs/MRs and releases to Mattermost, Slack or Telegram through a `NOTIFY_WEBHOOK_URL` secret.
- `merge-pr`: runs `tick-checklist` before the merge and fixes a closed issue with unticked items after it. `tick-checklist` is idempotent so `merge-pr` can call it.
- `setup-ci`: dry-run step lists each file to create or change with its diff and writes nothing until the user confirms.
- `open-pr`: look up an existing PR/MR for the branch and issue before creating one; update and reuse it when found.
- `merge-pr`: read mergeability after checks; on conflict or behind, rebase, push with `--force-with-lease` and re-watch checks before merging.
- `release` skill: version bump, dated changelog, release PR, annotated tag and release notes on GitHub or GitLab.
- CI: README and `reference/host-commands.md` now carry real links, so the lychee job verifies something and no longer needs `failIfEmpty: false`.

## [0.3.0] - 2026-10-27

- `open-pr`: every PR/MR is assigned to the current user without asking, and the user is asked who should review (`--reviewer`).
- CI: lychee link check and Dependabot for GitHub Actions.
- `setup-ci`: GitLab MR labeler template (`templates/gitlab/labeler.gitlab-ci.yml`) that adds area labels from changed paths.
- All skills support `gh` and `glab` through `reference/host-commands.md`.
- `create-labels.sh gitlab` creates scoped `::` labels.

## [0.2.0] - 2026-10-27

- `open-pr`: absorbed the commit, branch and PR hygiene rules from the archipy plugin's `contributing-for-apps` rule (one purpose per change, keep description current, run gates, security validation, no changelog or release changes unless asked).
- Multi-PR issues use an integration branch: chunk PRs merge into it, one final PR goes to the working branch with `Closes #N`, assigned to a named person and left unmerged. `split-issue`, `open-pr` and `merge-pr` ask for the working branch and the assignee.
- `merge-pr`: delete a head branch only after the PR is confirmed MERGED.

## [0.1.0]

- Initial release: `new-issue`, `split-issue`, `open-pr`, `tick-checklist`, `merge-pr`, `setup-ci`.
- GitHub and GitLab templates for issues, PRs/MRs, labels and post-merge issue comments.
