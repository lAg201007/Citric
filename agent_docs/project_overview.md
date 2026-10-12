# Project overview

Citric is the local continuation of the Rosemary compatibility work for running
the macOS Roblox Studio client on Linux. It preserves the source changes made
during the session, a local Studio bundle, a ready Rosemary binary, and the
diagnostic record needed to continue debugging.

The repository is intentionally local and has no Git remote. The proprietary
Studio bundle, runtime binary, and Darwin cache are physically available but
ignored by Git; their versions and hashes are documented in docs/bundle.md.
The authenticated user prefix and raw logs remain outside this repository.

The current deployment is complete as a migration. Future work resumes from
docs/current-state.md and should preserve the separation between source changes,
local runtime assets, and user account state.
