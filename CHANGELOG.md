# Changelog

## [Unreleased]

- Multi-PR issues use an integration branch: chunk PRs merge into it, one final PR goes to the working branch with `Closes #N`, assigned to a named person and left unmerged. `split-issue`, `open-pr` and `merge-pr` ask for the working branch and the assignee.
- `merge-pr`: delete a head branch only after the PR is confirmed MERGED.

## [0.1.0]

- Initial release: `new-issue`, `split-issue`, `open-pr`, `tick-checklist`, `merge-pr`, `setup-ci`.
- GitHub and GitLab templates for issues, PRs/MRs, labels and post-merge issue comments.
