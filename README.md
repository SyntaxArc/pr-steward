# pr-steward

Claude Code plugin ([source](https://github.com/SyntaxArc/pr-steward), [releases](https://github.com/SyntaxArc/pr-steward/releases)) for an issue-driven dev flow: **issue with checklist -> small PRs -> tick checklist -> merge -> close**.

## Install

```text
/plugin marketplace add SyntaxArc/pr-steward
/plugin install pr-steward@pr-steward
```

## Skills

| Skill | Purpose |
|---|---|
| `new-issue` | Create labeled issues (type, area, priority) with a PR-sized checklist; optionally asks for a Jira, Confluence or docs link; can create issues from review output or TODOs |
| `split-issue` | Split a big finding into `Part of #N` PRs (via an integration branch) or several issues; marks which chunks can run in parallel by file overlap |
| `open-pr` | Branch, conventional commits, labeled PR/MR assigned to you, asks for a reviewer, with `Closes #N` / `Part of #N` |
| `tick-checklist` | Tick the finished item, add result note and next chunk |
| `merge-pr` | Watch checks, merge, reopen the issue if items remain |
| `setup-ci` | Preview files and diffs (dry run), then install labels, templates, post-merge comment, labeler, stale bot, notify and tick-checklist on GitHub or GitLab |
| `release` | Bump versions, date the changelog (optionally drafted from merged PRs), release PR, tag, publish release notes |
| `review-pr` | Address review threads: fix, reply, resolve, re-request review |
| `status` | Read-only digest of open issues, PRs, checks and who each waits on |

## Rules the flow follows

- One PR moves one small chunk. Several PRs for one issue: `Part of #N`; only the last uses `Closes #N`.
- An issue stays open until every checklist item is ticked.
- Project policy files (`AGENTS.md`, `CONTRIBUTING.md`) override the defaults here.

## Config

Optional `.pr-steward.json` sets `workingBranch`, `defaultReviewer` and `mergeStrategy`, so `open-pr`, `merge-pr` and `release` ask less. See `reference/config.md`.

## CI templates

`templates/github/` and `templates/gitlab/`; installed by `setup-ci`. The issue templates carry an optional reference link field. GitLab merged-comment and labeler jobs need a masked `GITLAB_API_TOKEN` CI variable with the `api` scope. The optional `notify` piece posts merged PRs/MRs (and GitHub releases) to Mattermost, Slack or Telegram; it needs a `NOTIFY_WEBHOOK_URL` secret and a `NOTIFY_KIND` variable.

## Dependabot auto-merge

`.github/workflows/dependabot-automerge.yml` enables auto-merge on Dependabot patch bumps; minor and major stay manual. It needs the repo setting "Allow auto-merge" and branch protection on `main` that requires the CI checks, otherwise GitHub merges without waiting for them.

## Host CLIs

The skills drive GitHub through [`gh`](https://cli.github.com/manual/) and GitLab through [`glab`](https://docs.gitlab.com/cli/). See `reference/host-commands.md`.
