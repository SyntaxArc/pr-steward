# pr-steward

Claude Code plugin for an issue-driven dev flow: **issue with checklist -> small PRs -> tick checklist -> merge -> close**.

## Install

```text
/plugin marketplace add SyntaxArc/pr-steward
/plugin install pr-steward@pr-steward
```

## Skills

| Skill | Purpose |
|---|---|
| `new-issue` | Create labeled issues (type, area, priority) with a PR-sized checklist |
| `split-issue` | Split a big finding into `Part of #N` PRs (via an integration branch) or several issues |
| `open-pr` | Branch, conventional commits, labeled PR/MR with `Closes #N` / `Part of #N` |
| `tick-checklist` | Tick the finished item, add result note and next chunk |
| `merge-pr` | Watch checks, merge, reopen the issue if items remain |
| `setup-ci` | Install labels, templates, post-merge comment, labeler, stale bot on GitHub or GitLab |

## Rules the flow follows

- One PR moves one small chunk. Several PRs for one issue: `Part of #N`; only the last uses `Closes #N`.
- An issue stays open until every checklist item is ticked.
- Project policy files (`AGENTS.md`, `CONTRIBUTING.md`) override the defaults here.

## CI templates

`templates/github/` and `templates/gitlab/`; installed by `setup-ci`. GitLab merged-comment and labeler jobs need a masked `GITLAB_API_TOKEN` CI variable with the `api` scope.
