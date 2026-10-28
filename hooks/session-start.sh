#!/usr/bin/env bash
# SessionStart hook: point the session at the pr-steward skills. Silent outside a git repo.
set -euo pipefail

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

# List the skills from the skills/ directory next to this script so new skills appear automatically.
skills_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/skills"
names=""
if [ -d "$skills_dir" ]; then
  for dir in "$skills_dir"/*/; do
    [ -f "${dir}SKILL.md" ] || continue
    name="$(basename "$dir")"
    names="${names:+$names, }$name"
  done
fi
# Fallback when the directory is missing or empty.
[ -n "$names" ] || names="new-issue, split-issue, open-pr, tick-checklist, merge-pr, review-pr, status, release"

echo "Use the pr-steward skills ($names) for issues, branches, PRs and merges; do not run raw gh pr create, gh pr merge, glab mr create or glab mr merge."
