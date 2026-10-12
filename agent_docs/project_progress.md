# Project progress

No active deployment remains. Deployment citric-history-trim-20261012
completed the local Citric repository history cleanup after the patch-overlay
migration.

The launcher milestone is complete: `scripts/citric` and the `citric_launcher/`
GTK 4 package provide GUI/CLI launch, XDG configuration, diagnostics, and an
optional desktop-menu entry. The current branch contains no Rosemary source;
the canonical patch series and pinned base drive each build.

The next milestone is a normal-launch reproduction of the latest place-opening
crash, with a fresh log and exit code, followed by isolation of the invalid
require path. Camera sensitivity, nonlinear mouse spikes, Device Emulator
interference, and docking remain open; see docs/current-state.md.

Migration verification is documented in docs/validation.md. Several checks were
run against the source tree before migration and must be rechecked in Citric
before treating the copy as fully validated.
