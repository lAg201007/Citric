# Project overview

Citric is the local continuation of the Rosemary compatibility work for running
the macOS Roblox Studio client on Linux. It preserves the source changes made
during the session, a local Studio bundle, a ready Rosemary binary, and the
diagnostic record needed to continue debugging.

The GitHub repository is a standalone Citric repository. Locally, `origin`
points to Citric and `upstream` points to Rosemary, so updates can be fetched
without pretending that GitHub has a formal fork relationship. The proprietary
Studio bundle, runtime binary, and Darwin cache are physically available but
ignored by Git; their versions and hashes are documented in docs/bundle.md.
The authenticated user prefix and raw logs remain outside this repository.

The repository now also contains a GTK 4 launcher in `citric_launcher/` and a
canonical runtime patch series in `patches/`. The full Rosemary checkout stays
as the executable reference; a future patch-only distribution is deferred
until checkout preparation and build verification are automated.

The current deployment is complete as a migration. Future work resumes from
docs/current-state.md and should preserve the separation between source changes,
local runtime assets, and user account state.
