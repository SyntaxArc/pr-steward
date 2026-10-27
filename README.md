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
| `new-issue` | Create labeled issues (type, area, priority) with a PR-sized checklist |
| `split-issue` | Split a big finding into `Part of #N` PRs (via an integration branch) or several issues |
| `open-pr` | Branch, conventional commits, labeled PR/MR assigned to you, asks for a reviewer, with `Closes #N` / `Part of #N` |
| `tick-checklist` | Tick the finished item, add result note and next chunk |
| `merge-pr` | Watch checks, merge, reopen the issue if items remain |
| `setup-ci` | Preview files and diffs (dry run), then install labels, templates, post-merge comment, labeler, stale bot on GitHub or GitLab |
| `release` | Bump versions, date the changelog, release PR, tag, publish release notes |

## Rules the flow follows

- One PR moves one small chunk. Several PRs for one issue: `Part of #N`; only the last uses `Closes #N`.
- An issue stays open until every checklist item is ticked.
- Project policy files (`AGENTS.md`, `CONTRIBUTING.md`) override the defaults here.

## CI templates

`templates/github/` and `templates/gitlab/`; installed by `setup-ci`. GitLab merged-comment and labeler jobs need a masked `GITLAB_API_TOKEN` CI variable with the `api` scope.

## Dependabot auto-merge

`.github/workflows/dependabot-automerge.yml` enables auto-merge on Dependabot patch bumps; minor and major stay manual. It needs the repo setting "Allow auto-merge" and branch protection on `main` that requires the CI checks, otherwise GitHub merges without waiting for them.

## Host CLIs

The skills drive GitHub through [`gh`](https://cli.github.com/manual/) and GitLab through [`glab`](https://docs.gitlab.com/cli/). See `reference/host-commands.md`.
