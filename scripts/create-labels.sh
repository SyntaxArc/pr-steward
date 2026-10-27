#!/usr/bin/env bash
# Create the type/area/priority labels. Usage: create-labels.sh [github|gitlab]
set -euo pipefail
host="${1:-github}"
mk() { # name color description
  local name="$1"
  [ "$host" = gitlab ] && name="${name/:/::}"
  if [ "$host" = github ]; then gh label create "$name" --color "$2" --description "$3" --force
  else glab label create --name "$name" --color "#$2" --description "$3" || true; fi
}
mk bug d73a4a "Something is broken"
mk enhancement a2eeef "New feature or request"
mk refactor c5def5 "Code change with no behavior change"
mk documentation 0075ca "Docs only"
mk security ee0701 "Security-related"
mk breaking-change b60205 "Changes public behavior; needs deprecation path"
mk priority:high b60205 "Needs attention soon"
mk priority:medium fbca04 "Normal priority"
mk priority:low 0e8a16 "Nice to have"
mk area:ci 5319e7 "CI, workflows, release tooling"
mk area:testing 5319e7 "Tests"
