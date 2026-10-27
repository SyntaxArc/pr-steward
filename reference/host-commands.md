# Host commands

Detect the host with `git remote get-url origin`: `github.com` -> `gh`, otherwise `glab`. Ask when unclear.
Self-hosted GitLab: `glab` reads the host from the remote; `GITLAB_HOST` overrides it.

| Task | GitHub (`gh`) | GitLab (`glab`) |
|---|---|---|
| list labels | `gh label list` | `glab label list` |
| create label | `gh label create N --color RRGGBB --description D` | `glab label create --name N --color "#RRGGBB" --description D` |
| create issue | `gh issue create --title T --body-file F --label a,b` | `glab issue create --title T --description "$(cat F)" --label a,b` |
| view issue body | `gh issue view N --json body -q .body` | `glab issue view N -F json \| jq -r .description` |
| edit issue body | `gh issue edit N --body-file F` | `glab issue update N --description "$(cat F)"` |
| comment on issue | `gh issue comment N --body T` | `glab issue note N -m T` |
| reopen issue | `gh issue reopen N` | `glab issue reopen N` |
| list PR/MR by branch | `gh pr list --head BRANCH --state all` | `glab mr list --source-branch BRANCH --all` |
| find PR/MR by issue | `gh pr list --search "#N" --state all` | `glab mr list --search "#N" --all` |
| edit PR/MR | `gh pr edit N --add-label a --add-assignee @me --body-file F` | `glab mr update N --label a --assignee USER --description "$(cat F)"` |
| create PR/MR | `gh pr create --title T --body-file F --label a,b` | `glab mr create --title T --description "$(cat F)" --label a,b --target-branch BASE --remove-source-branch --yes` |
| assign / review on create | `gh pr create ... --assignee @me --reviewer LOGIN` | `glab mr create ... --assignee USER --reviewer USER` (`glab api user \| jq -r .username` for the current user) |
| watch checks | `gh pr checks N --watch` | `glab ci status --live` |
| read mergeability | `gh pr view N --json mergeStateStatus,mergeable` (`DIRTY`/`CONFLICTING` = conflict, `BEHIND` = needs rebase, `CLEAN` = ok) | `glab mr view N -F json \| jq -r .detailed_merge_status` (`conflict`/`need_rebase` = stop, `mergeable` = ok) |
| push rebased branch | `git push --force-with-lease` | `git push --force-with-lease` |
| merge | `gh pr merge N --merge` (or `--squash`) | `glab mr merge N --yes` (add `--squash`; `--when-pipeline-succeeds` waits for the pipeline) |
| tag | `git tag -a vX.Y.Z -m X.Y.Z && git push origin vX.Y.Z` | same |
| create release | `gh release create vX.Y.Z --title X.Y.Z --notes-file F` | `glab release create vX.Y.Z --name X.Y.Z --notes-file F` |

## Differences

- GitLab calls PRs merge requests (MRs).
- Label scopes: GitHub uses `area:ci`, GitLab scoped labels use `area::ci`. Match what the repo already has (`glab label list`); `scripts/create-labels.sh gitlab` creates the `::` form. One scoped label per scope is allowed on an item, which fits one type/priority.
- Closing keywords `Closes #N`, `Fixes #N`, `Resolves #N` work on both hosts. `Part of #N` is only a convention: neither host links it, so the post-merge comment job and `tick-checklist` carry that reference.
- GitLab has no required-status default: use `--when-pipeline-succeeds` or watch the pipeline before merging.
