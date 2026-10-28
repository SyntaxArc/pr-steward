# Host commands

CLI docs: [`gh`](https://cli.github.com/manual/), [`glab`](https://docs.gitlab.com/cli/).

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
| list PRs/MRs merged since date | `gh pr list --state merged --search "merged:>=DATE" --json number,title,labels,url,closingIssuesReferences` | `glab mr list --merged --updated-after DATE -F json` (labels, `web_url` in output; filter by `merged_at`) |
| list open issues | `gh issue list --state open --json number,title,assignees` | `glab issue list -F json` |
| list open PRs/MRs | `gh pr list --state open --json number,title,headRefName,isDraft,reviewRequests,assignees,statusCheckRollup,mergeStateStatus` | `glab mr list -F json` (`draft`, `detailed_merge_status`, `head_pipeline.status` give draft, mergeability, checks) |
| view PR/MR checks | `gh pr checks N` | `glab mr view N -F json \| jq -r .head_pipeline.status` |
| list unresolved review threads | `gh api graphql -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){pullRequest(number:$n){reviewThreads(first:100){nodes{id isResolved isOutdated path line comments(first:20){nodes{databaseId author{login} body}}}}}}}' -f o=OWNER -f r=REPO -F n=N` (keep `isResolved: false`) | `glab api "projects/:id/merge_requests/N/discussions" \| jq '[.[] \| select(.notes[0].resolvable and (.notes[0].resolved\|not))]'` |
| reply to review thread | `gh api graphql -f query='mutation($t:ID!,$b:String!){addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$t,body:$b}){comment{id}}}' -f t=THREAD_ID -f b=T` | `glab mr note N --reply DISCUSSION_ID -m T` (or `glab api -X POST "projects/:id/merge_requests/N/discussions/DISCUSSION_ID/notes" -f body=T`) |
| resolve review thread | `gh api graphql -f query='mutation($t:ID!){resolveReviewThread(input:{threadId:$t}){thread{isResolved}}}' -f t=THREAD_ID` | `glab api -X PUT "projects/:id/merge_requests/N/discussions/DISCUSSION_ID" -f resolved=true` |
| re-request review | `gh pr edit N --add-reviewer LOGIN` (re-requests a reviewer who already reviewed) | `glab mr update N --reviewer USER` (adds to the current list: pass every reviewer to keep) |
| view CI run / pipeline | `gh run view ID --json name,headSha,conclusion,jobs,url` | `glab ci get -p ID -F json` (pipeline id; `glab ci get` uses the current branch) |
| failed job log | `gh run view ID --log-failed \| tail -n 30` | `glab ci trace JOB_ID \| tail -n 30` (job ids: `glab ci get -p ID -F json`, or `glab api "projects/:id/pipelines/ID/jobs?scope[]=failed"`) |
| view PR/MR merge state and merge commit | `gh pr view N --json state,mergeCommit,title,labels,body` (`state` = `MERGED`; `mergeCommit.oid` is the sha) | `glab mr view N -F json \| jq '{state,merge_commit_sha,squash_commit_sha,title,labels}'` (`state` = `merged`) |
| view PR/MR commits | `gh pr view N --json commits -q '.commits[].oid'` | `glab api "projects/:id/merge_requests/N/commits" \| jq -r '.[].id'` (newest first: reverse before picking) |
| delete remote branch | `git push origin --delete BRANCH` | `git push origin --delete BRANCH` |
| list remote branches merged into the working branch | `git branch -r --merged origin/BASE` | `git branch -r --merged origin/BASE` |
| auto-delete head branches after merge | `gh api -X PATCH repos/OWNER/REPO -f delete_branch_on_merge=true` | `glab mr create --remove-source-branch`; project: `glab api -X PUT projects/:id -f remove_source_branch_after_merge=true` |
| view PR/MR labels, assignees, reviewers, state | `gh pr view N --json labels,assignees,reviewRequests,state,baseRefName` | `glab mr view N -F json \| jq '{labels,assignees,reviewers,state,target_branch}'` |
| view issue labels, assignees | `gh issue view N --json labels,assignees` | `glab issue view N -F json \| jq '{labels,assignees}'` |
| check tag / release exists | `git ls-remote --tags origin vX.Y.Z`; `gh release view vX.Y.Z --json tagName,url` | `git ls-remote --tags origin vX.Y.Z`; `glab release view vX.Y.Z` |

## Differences

- GitLab calls PRs merge requests (MRs).
- Label scopes: GitHub uses `area:ci`, GitLab scoped labels use `area::ci`. Match what the repo already has (`glab label list`); `scripts/create-labels.sh gitlab` creates the `::` form. One scoped label per scope is allowed on an item, which fits one type/priority.
- Closing keywords `Closes #N`, `Fixes #N`, `Resolves #N` work on both hosts. `Part of #N` is only a convention: neither host links it, so the post-merge comment job and `tick-checklist` carry that reference.
- Another repo: `gh ... --repo owner/repo`, `glab ... -R owner/repo`; write cross references as `owner/repo#N`.
- GitLab has no required-status default: use `--when-pipeline-succeeds` or watch the pipeline before merging.
