---
name: release
description: >-
  Cut a release: bump plugin versions, date the changelog, open a release PR/MR, tag, and publish a release with the changelog notes. Use for "release X.Y.Z", "cut a release", "tag a new version".
---

# Release

Release only when the user asks. Never bump versions, tag, or publish on your own.

Host commands for `gh` and `glab`: `${CLAUDE_PLUGIN_ROOT}/reference/host-commands.md`. Detect the host from `git remote get-url origin`.

## Steps

1. Get the version `X.Y.Z` (ask if missing). Start from an up-to-date working branch with a clean tree. Stop if `CHANGELOG.md` has no `## [Unreleased]` section with entries.
2. Branch `chore/release-X.Y.Z`.
3. Bump `version` to `X.Y.Z` in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.
4. Rename `## [Unreleased]` to `## [X.Y.Z] - <today, YYYY-MM-DD>`. Do not add a new empty `Unreleased` heading.
5. Commit and open the PR/MR `chore: release X.Y.Z` with type/area/priority labels, assigned to the current user (see `open-pr`).
6. Watch checks. Stop and report any failure.
7. Merge only if the user asked for the release itself; otherwise leave it for the reviewer. Sync the working branch after merge.
8. Tag the merge commit: `git tag -a vX.Y.Z -m "X.Y.Z"`, then `git push origin vX.Y.Z`.
9. Publish the release with the `## [X.Y.Z]` section body as notes (see host commands).
10. Offer to post the release link (Slack, issue, channel). Post only if the user agrees.

## Do not

- Release, tag, or merge without an explicit user request.
- Tag before the release PR shows MERGED.
- Use a lightweight tag.
