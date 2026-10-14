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

The launcher applies a narrow, plugin-ID-agnostic compatibility rule to
cached plugin models that contain the known legacy `bit` fallback declaration.
It changes only that exact signature to use Roblox's built-in `bit32`, with a
verified local backup. The user confirmed that the Baseplate which previously
failed now opens. Other unknown module imports remain untouched.

The diagnostic workflow supports `ROSEMARY_PERF_TRACE`. When enabled by the
launcher, it records main-loop gaps, script/event/backing pumps,
CoreFoundation callbacks, and AppKit/CoreVideo display-link scheduling and
callback times. This helps investigate periodic Play stalls without assuming
that the cause is a fixed timer.

The AppKit file-panel compatibility layer now uses Rosemary's shared SDL-backed
`chrome` file chooser for Import and Open from File. The latest manual retest
reached the chooser and navigated with Up; readable entries, selection, and
cancellation still need confirmation after the theme contrast fix.
