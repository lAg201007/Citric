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

The locale mitigation is implemented in `scripts/run-studio.sh` and covered by
`tests/test_run_studio_locale.py`. It has not yet been confirmed by opening
Play through the updated launcher.

Deployment `citric-plugin-bit32-20261012` is paused after identifying a likely
plugin crash source: plugin `16708835782` requests bare `bit`, matching the
fatal `require path must start with a valid prefix` log. The launcher-side
override, tests, and documentation are present in the worktree, but the
override has not been installed into the user's live prefix and no post-fix
Studio launch has been validated. Resume by running the full tests, then
launching through `scripts/run-studio.sh` and checking the generated metadata
and crash result. Keep the plugin enabled; disabling it is only a diagnostic
comparison, not the intended fix.

Migration verification is documented in docs/validation.md. Several checks were
run against the source tree before migration and must be rechecked in Citric
before treating the copy as fully validated.
