---
name: setup-ci
description: >-
  Install issue/PR CI and templates on GitHub or GitLab: labels, issue and PR/MR templates, post-merge issue comment, PR labeler, stale-issue bot. Use for "set up CI for issues", "add templates", "bootstrap the repo workflow".
---

# Setup CI

Installs the files in `${CLAUDE_PLUGIN_ROOT}/templates/` into the current repo.

## Steps

1. Detect host (see `${CLAUDE_PLUGIN_ROOT}/reference/host-commands.md`). Ask if unclear.
2. Ask which pieces (multi-select): `labels`, `templates`, `merged-comment`, `labeler`, `stale`.
3. For each chosen piece, check the target exists first. Never overwrite a file without showing the diff and asking.
4. Copy per the table, then review the files with the user.

| Piece | GitHub | GitLab |
|---|---|---|
| labels | `scripts/create-labels.sh github` | `scripts/create-labels.sh gitlab` (scoped `::` names) |
| templates | `.github/ISSUE_TEMPLATE/*`, `.github/pull_request_template.md` | `.gitlab/issue_templates/*`, `.gitlab/merge_request_templates/*` |
| merged-comment | `.github/workflows/pr-merged-issue-comment.yml` | `.gitlab-ci.yml` job from `templates/gitlab/merged-comment.gitlab-ci.yml` |
| labeler | `.github/workflows/labeler.yml` + `.github/labeler.yml` | `.gitlab-ci.yml` job from `templates/gitlab/labeler.gitlab-ci.yml` (path-to-label map in `LABEL_MAP`) |
| stale | `.github/workflows/close-stale-issues.yml` | GitLab policies or a scheduled pipeline |

5. Adapt `labeler.yml` globs (GitLab: `LABEL_MAP`) to the repo layout; do not ship placeholder globs.
6. GitLab needs a CI variable `GITLAB_API_TOKEN` (api scope) for the merged-comment and labeler jobs. Tell the user; never write a token to a file.
7. Run the label script only after the user confirms; it creates labels on the remote.
