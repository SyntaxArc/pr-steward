#!/usr/bin/env bash
# SessionStart hook: point the session at the pr-steward skills. Silent outside a git repo.
set -euo pipefail

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

echo "Use the pr-steward skills (new-issue, split-issue, open-pr, tick-checklist, merge-pr, review-pr, status, release) for issues, branches, PRs and merges; do not run raw gh pr create, gh pr merge, glab mr create or glab mr merge."
