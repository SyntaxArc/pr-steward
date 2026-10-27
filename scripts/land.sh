#!/usr/bin/env bash
# Land PRs in order: rebase on the base, union-resolve append-only conflicts,
# run project gates, push, wait for checks, merge, verify MERGED, delete the head branch.
# Usage: land.sh PR [PR...]   (run from inside the repo; GitHub only for now)
set -euo pipefail

die() {
  printf 'STOP: %s\n' "$*" >&2
  exit "${2:-1}"
}

[ "$#" -ge 1 ] || die "usage: land.sh PR [PR...]" 64
for pr in "$@"; do
  case "$pr" in
    '' | *[!0-9]*) die "not a PR number: $pr" 64 ;;
  esac
done

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(git rev-parse --show-toplevel)"
origin_url="$(git -C "$repo" remote get-url origin)"
case "$origin_url" in
  *github.com*) ;;
  *) die "land.sh supports GitHub only for now (origin is $origin_url); on GitLab merge each MR by hand with merge-pr" 64 ;;
esac
command -v gh > /dev/null || die "gh CLI not found" 64

tmp="$(mktemp -d)"
cleanup() {
  local status=$?
  local dir
  for dir in "$tmp"/pr*; do
    [ -d "$dir" ] || continue
    git -C "$repo" worktree remove --force "$dir" > /dev/null 2>&1 || true
  done
  git -C "$repo" worktree prune > /dev/null 2>&1 || true
  rm -rf "$tmp"
  exit "$status"
}
trap cleanup EXIT

# Merge strategy: .pr-steward.json mergeStrategy, else merge.
strategy=merge
if [ -f "$repo/.pr-steward.json" ]; then
  configured="$(python3 -c 'import json,sys
try:
    print(json.load(open(sys.argv[1])).get("mergeStrategy", ""))
except (OSError, ValueError, AttributeError):
    pass' "$repo/.pr-steward.json")"
  case "$configured" in
    merge | squash | rebase) strategy="$configured" ;;
    '') ;;
    *) die "invalid mergeStrategy in .pr-steward.json: $configured" 64 ;;
  esac
fi

# Rebase the checked-out PR branch on origin/BASE, union-resolving append-only conflicts.
rebase_on_base() {
  local pr="$1" base="$2" git_dir unmerged file
  local -a files
  git rebase "origin/$base" > /dev/null 2>&1 && return 0
  git_dir="$(git rev-parse --git-dir)"
  while [ -d "$git_dir/rebase-merge" ] || [ -d "$git_dir/rebase-apply" ]; do
    unmerged="$(git diff --name-only --diff-filter=U)"
    [ -n "$unmerged" ] || die "PR $pr: rebase stopped without conflicting files; resolve by hand" 2
    files=()
    while IFS= read -r file; do
      case "$file" in
        *.md) files+=("$file") ;;
        *)
          git rebase --abort > /dev/null 2>&1 || true
          die "PR $pr: conflict in $file is not an append-only markdown file; resolve by hand" 2
          ;;
      esac
    done <<< "$unmerged"
    if ! python3 "$script_dir/union_resolve.py" "${files[@]}"; then
      git rebase --abort > /dev/null 2>&1 || true
      die "PR $pr: conflict is not append-only (see above); resolve by hand" 2
    fi
    git add -- "${files[@]}"
    GIT_EDITOR=true git rebase --continue > /dev/null 2>&1 || true
  done
}

run_gates() {
  local pr="$1"
  if [ -f scripts/check_catalog.py ]; then
    python3 scripts/check_catalog.py || die "PR $pr: scripts/check_catalog.py failed" 4
    if [ -d tests ]; then
      python3 -m unittest discover -s tests > /dev/null 2>&1 || die "PR $pr: unit tests failed" 4
    fi
  elif [ -f Makefile ]; then
    echo "PR $pr: Makefile found but no known gate; skipping local gates"
  else
    echo "PR $pr: no project gates found; skipping"
  fi
}

wait_for_checks() {
  local pr="$1" try=0 buckets
  # Checks may not be registered right after the push.
  until gh pr checks "$pr" > /dev/null 2>&1 || [ "$try" -ge 6 ]; do
    try=$((try + 1))
    sleep 5
  done
  gh pr checks "$pr" --watch > /dev/null 2>&1 || true
  buckets="$(gh pr checks "$pr" --json bucket --jq '.[].bucket' 2> /dev/null || true)"
  case "$buckets" in
    *fail* | *cancel*) die "PR $pr: a check failed; not merging" 5 ;;
    *pending*) die "PR $pr: checks still pending; not merging" 5 ;;
  esac
}

for pr in "$@"; do
  echo "== PR $pr =="
  info="$(gh pr view "$pr" --json state,headRefName,baseRefName,isCrossRepository \
    --jq '[.state, .headRefName, .baseRefName, (.isCrossRepository | tostring)] | join("\t")')"
  IFS=$'\t' read -r state head base cross <<< "$info"
  [ "$state" = OPEN ] || die "PR $pr is $state, not OPEN" 3
  [ "$cross" = false ] || die "PR $pr is from a fork; land it by hand" 3

  git -C "$repo" fetch --quiet origin
  wt="$tmp/pr$pr"
  git -C "$repo" worktree add --quiet -B "land-pr$pr" "$wt" "origin/$head" > /dev/null
  lease="$(git -C "$repo" rev-parse "origin/$head")"

  (
    cd "$wt"
    rebase_on_base "$pr" "$base"
    if grep -rlE '^(<<<<<<<|>>>>>>>) ' --exclude-dir=.git . > /dev/null 2>&1; then
      die "PR $pr: conflict markers left in the tree" 3
    fi
    run_gates "$pr"
    git push --quiet --force-with-lease="$head:$lease" origin "HEAD:refs/heads/$head"
  )

  wait_for_checks "$pr"

  merge_state="$(gh pr view "$pr" --json mergeStateStatus --jq .mergeStateStatus)"
  case "$merge_state" in
    DIRTY | BEHIND | BLOCKED | UNKNOWN) die "PR $pr: merge state is $merge_state; not merging" 3 ;;
  esac
  gh pr merge "$pr" "--$strategy" > /dev/null 2>&1 || echo "PR $pr: gh pr merge reported an error; reading state to check"

  final=""
  for _ in 1 2 3 4 5 6; do
    final="$(gh pr view "$pr" --json state --jq .state)"
    [ "$final" = MERGED ] && break
    sleep 3
  done
  [ "$final" = MERGED ] || die "PR $pr: state is $final after merge attempt" 6

  if git -C "$repo" ls-remote --exit-code --heads origin "$head" > /dev/null 2>&1; then
    git -C "$repo" push --quiet origin --delete "$head" || echo "PR $pr: could not delete remote branch $head"
  fi
  git -C "$repo" worktree remove --force "$wt" > /dev/null 2>&1 || true
  git -C "$repo" branch -D "land-pr$pr" > /dev/null 2>&1 || true
  echo "PR $pr: MERGED ($strategy), branch $head deleted"
done
