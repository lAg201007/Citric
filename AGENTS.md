# Citric Agent Instructions

This repository is an experimental continuation of Rosemary compatibility work for investigating how to run the macOS version of Roblox Studio on Linux. It is not the CaseSolved game repository.

## Language

Write all documentation and code changes in English. This includes new or modified documentation, source code, code comments, identifiers, and user-facing text.

## Before Changing Code

- Read `docs/current-state.md`, `docs/compatibility.md`, `docs/crashes.md`, and `docs/validation.md`.
- Preserve the current diff against the base commit recorded in `README.md` and `docs/current-state.md`.
- Do not treat a user's visual report as equivalent to an automated test.
- Keep raw logs, cookies, tokens, authenticated prefixes, places, and account screenshots out of Git.
- `app/full/RobloxStudio.app`, `bin/rosemary`, and `downloads/darwin-cache` are ignored local artifacts. Do not force-add them.
- Do not configure remotes or push changes to GitHub without a subsequent explicit request.
- For tests requiring complex mouse movement, ask the user to perform the interaction through a question; do not move the pointer on their behalf.
- Track implemented fixes, fixes confirmed by the user, and unresolved issues separately.

The local Roblox Studio copy is proprietary software. It is available for testing but excluded from Git. Before any publication, check `git status` and the manifest documented in `docs/bundle.md`.
