# Project overview

Citric is the local continuation of the Rosemary compatibility work for running
the macOS Roblox Studio client on Linux. Its current branch stores the
compatibility patches, launcher, scripts, and diagnostic record; Rosemary source
is materialized only in a temporary build checkout.

The GitHub repository is a standalone Citric repository. Locally, `origin`
points to Citric and `upstream` points to Rosemary, so updates can be fetched
without pretending that GitHub has a formal fork relationship. Its branch
history keeps the four Citric commits and omits the prior Rosemary ancestry;
the proprietary
Studio bundle, runtime binary, and Darwin cache are physically available but
ignored by Git; their versions and hashes are documented in docs/bundle.md.
The authenticated user prefix and raw logs remain outside this repository.

The repository contains a GTK 4 launcher in `citric_launcher/` and a canonical
runtime patch series in `patches/`. `scripts/build-studio.sh` fetches the pinned
Rosemary commit, applies `patches/series`, builds in a temporary cache, and can
install the resulting ignored `bin/rosemary` executable. Earlier Git commits
retain the removed Rosemary source, so history and reproducibility are kept.

The patch-overlay migration is complete. Future work resumes from
docs/current-state.md and should preserve the separation between source changes,
local runtime assets, and user account state.

The launcher normalizes Studio's numeric locale to `C` and records the
before/after values. This addresses the observed Play failure where valid
decimal literals were reported as `Malformed number`; fresh manual Play
confirmation is still required.

The launcher also contains a narrow compatibility override for installed
Blender Animations plugin builds that request the unavailable bare `bit`
module. The override is content-addressed, idempotent, and creates a local
backup before changing the plugin artifact. Live installation and Studio
reproduction are still pending.
