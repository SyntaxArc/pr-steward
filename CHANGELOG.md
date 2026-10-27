# Changelog

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
