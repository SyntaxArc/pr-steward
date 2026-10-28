# Config: `.pr-steward.json`

Optional file at the repo root. Skills read it before asking the user.

```json
{
  "workingBranch": "master",
  "defaultReviewer": "octocat",
  "mergeStrategy": "squash",
  "deleteBranchOnMerge": true,
  "repos": ["owner/api", "owner/web"]
}
```

| Key | Value | Used by |
| --- | --- | --- |
| `workingBranch` | branch PRs target (`development`, `main`, `master`, ...) | `open-pr`, `merge-pr`, `release` |
| `defaultReviewer` | GitHub login or GitLab username | `open-pr` |
| `mergeStrategy` | `merge`, `squash` or `rebase` | `merge-pr` |
| `deleteBranchOnMerge` | boolean, default `true`; `false` turns off deleting the source branch after merge | `open-pr`, `merge-pr` |
| `maxFiles` | integer, default `15`; PR size warning above this many changed files | `open-pr`, `merge-pr` |
| `maxLines` | integer, default `500`; PR size warning above this many changed lines | `open-pr`, `merge-pr` |
| `announce` | object `{"kind": "mattermost"\|"slack"\|"telegram", "channel": "..."}`; where `release` offers to post the link | `release` |
| `repos` | array of `owner/repo` strings; repos of one multi-repo feature | `split-issue`, `status` |

## Rules

- All keys optional. File missing or invalid JSON: treat every key as missing.
- Precedence: project policy files (`AGENTS.md`, `CONTRIBUTING.md`) > this config > asking the user.
- Use a key's value without asking. Ask only when the key is missing and no policy file answers it.
- An explicit user instruction in the conversation overrides the config for that run.
- `repos`: entries are `owner/repo` (GitLab: `group/project`). Missing or empty: current repo only. Skills pass each entry to `--repo` (gh) or `-R` (glab).
- `announce`: `release` offers to post the link to `channel` via `kind` and posts only after the user agrees.
- Never write the file unless the user asks.
