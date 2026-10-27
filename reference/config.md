# Config: `.pr-steward.json`

Optional file at the repo root. Skills read it before asking the user.

```json
{
  "workingBranch": "master",
  "defaultReviewer": "octocat",
  "mergeStrategy": "squash"
}
```

| Key | Value | Used by |
| --- | --- | --- |
| `workingBranch` | branch PRs target (`development`, `main`, `master`, ...) | `open-pr`, `merge-pr`, `release` |
| `defaultReviewer` | GitHub login or GitLab username | `open-pr` |
| `mergeStrategy` | `merge`, `squash` or `rebase` | `merge-pr` |

## Rules

- All keys optional. File missing or invalid JSON: treat every key as missing.
- Precedence: project policy files (`AGENTS.md`, `CONTRIBUTING.md`) > this config > asking the user.
- Use a key's value without asking. Ask only when the key is missing and no policy file answers it.
- An explicit user instruction in the conversation overrides the config for that run.
- Never write the file unless the user asks.
