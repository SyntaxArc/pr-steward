---
name: setup-ci
description: >-
  Install issue/PR CI and templates on GitHub or GitLab: labels, issue and PR/MR templates, post-merge issue comment, PR labeler, stale-issue bot, chat notify. Use for "set up CI for issues", "add templates", "bootstrap the repo workflow".
---

# Setup CI

Installs the files in `${CLAUDE_PLUGIN_ROOT}/templates/` into the current repo.

## Steps

1. Detect host (see `${CLAUDE_PLUGIN_ROOT}/reference/host-commands.md`). Ask if unclear.
2. Ask which pieces (multi-select): `labels`, `templates`, `merged-comment`, `labeler`, `stale`, `notify`, `tick-checklist`.
3. For each chosen piece, check the target exists first. Never overwrite a file without showing the diff and asking.
4. Dry run first: list every file to create or change, with its diff (new files in full, existing files as a diff). Write nothing. Ask the user to confirm.
5. After confirmation, copy per the table, then review the files with the user.

| Piece | GitHub | GitLab |
|---|---|---|
| labels | `scripts/create-labels.sh github` | `scripts/create-labels.sh gitlab` (scoped `::` names) |
| templates | `.github/ISSUE_TEMPLATE/*`, `.github/pull_request_template.md` | `.gitlab/issue_templates/*`, `.gitlab/merge_request_templates/*` |
| merged-comment | `.github/workflows/pr-merged-issue-comment.yml` | `.gitlab-ci.yml` job from `templates/gitlab/merged-comment.gitlab-ci.yml` |
| labeler | `.github/workflows/labeler.yml` + `.github/labeler.yml` | `.gitlab-ci.yml` job from `templates/gitlab/labeler.gitlab-ci.yml` (path-to-label map in `LABEL_MAP`) |
| stale | `.github/workflows/close-stale-issues.yml` | GitLab policies or a scheduled pipeline |
| tick-checklist | `.github/workflows/tick-checklist.yml` (ticks `Part of #N (item K)` and `Closes #N` items after a merge; reopens a `Closes #N` issue that still has unticked items) | `.gitlab-ci.yml` job from `templates/gitlab/tick-checklist.gitlab-ci.yml` |
| notify | `.github/workflows/notify.yml` | `.gitlab-ci.yml` job from `templates/gitlab/notify.gitlab-ci.yml` |

6. Adapt `labeler.yml` globs (GitLab: `LABEL_MAP`) to the repo layout; do not ship placeholder globs.
7. GitLab needs a CI variable `GITLAB_API_TOKEN` (api scope) for the merged-comment, labeler and tick-checklist jobs. Tell the user; never write a token to a file.
8. For `notify`, ask the chat kind (`mattermost`, `slack` or `telegram`). Tell the user to create the secret `NOTIFY_WEBHOOK_URL` (GitLab: masked CI variable) and set `NOTIFY_KIND`. Telegram also needs `NOTIFY_TELEGRAM_CHAT_ID`, and the secret is `https://api.telegram.org/bot<TOKEN>/sendMessage`. GitLab also needs `GITLAB_API_TOKEN`. Never ask for or write the webhook URL or a token.
9. Run the label script only after the user confirms; it creates labels on the remote.
