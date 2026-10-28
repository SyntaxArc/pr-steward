# Terse text

Issue and PR/MR descriptions are short and written in caveman style: key changes and the hot change only. No long details, no essays.

- Drop articles, filler and pleasantries. Fragments are fine. Technical terms, paths, commands and errors stay exact.
- Issue body: one line problem, one line fix (evidence only as `file:line`), then the checklist.
- PR/MR body: 2-5 lines: what changed, test line, then the reference line.
- Keep reference lines (`Closes #N`, `Part of #N (item K)`, `Backport of #N`) and the checklist syntax exact: CI parses them.
- Commit messages stay normal conventional commits.
