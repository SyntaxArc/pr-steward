---
name: new-issue
description: >-
  Create one or many labeled GitHub/GitLab issues with a checklist for a bug, improvement, refactor, or finding. Use for "file an issue", "track this", "create issues for these findings".
---

# New Issue

Create the issue **before** fixing anything. One issue per finding.

## Steps

1. Detect host: `git remote get-url origin` (github.com -> `gh`, otherwise `glab`).
2. Read the project policy first: `AGENTS.md`, `CONTRIBUTING.md`, `.cursor/rules/contributing.mdc` if present. Project label names and templates win over the defaults below.
3. List labels (`gh label list` / `glab label list`). Pick one **type** (`bug`, `enhancement`, `refactor`, `documentation`, `security`), one or more **area** labels, and one **priority** (`priority:high|medium|low`). Create missing labels only after asking.
4. Body: problem, evidence (file:line, logs), proposed fix, then a checklist, one item per PR-sized chunk:

   ```markdown
   ## Checklist
   - [ ] chunk 1: <small, reviewable>
   - [ ] chunk 2: <next>
   - [ ] docs / tests updated
   ```

5. Create: `gh issue create --title ... --body-file ... --label a,b,c` (GitLab: `glab issue create`).
6. Several unrelated findings -> several issues, never one catch-all.

## Do not

- Fix before the issue exists.
- Put unrelated findings in one issue.
- Mention AI tools in the issue text.
