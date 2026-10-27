# Changelog

## [Unreleased]

- `merge-pr`: runs `tick-checklist` before the merge and fixes a closed issue with unticked items after it. `tick-checklist` is idempotent so `merge-pr` can call it.
- `setup-ci`: dry-run step lists each file to create or change with its diff and writes nothing until the user confirms.

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
