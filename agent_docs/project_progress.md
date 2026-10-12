# Project progress

No active deployment remains. Deployment citric-history-trim-20261012
completed the local Citric repository history cleanup after the patch-overlay
migration.

The launcher milestone is complete: `scripts/citric` and the `citric_launcher/`
GTK 4 package provide GUI/CLI launch, XDG configuration, diagnostics, and an
optional desktop-menu entry. The current branch contains no Rosemary source;
the canonical patch series and pinned base drive each build.

The place-opening `require` crash is mitigated by the plugin compatibility
rule, and the user confirmed the Baseplate opens. The separate Play
`Malformed number` observation still needs a launch through the current
launcher. Camera sensitivity, nonlinear mouse spikes, Device Emulator
interference, and docking remain open; see docs/current-state.md.

The locale mitigation is implemented in `scripts/run-studio.sh` and covered by
`tests/test_run_studio_locale.py`. It has not yet been confirmed by opening
Play through the updated launcher.

The bare-`bit` crash was associated with plugin `16708835782` and its legacy
`requireany("bit", "bit32", ...)` fallback. The launcher now scans all
installed plugin IDs and versions for that exact signature, patches matches
to use built-in `bit32`, and preserves verified backups. The user confirmed
the Baseplate that previously failed now opens with the plugin enabled. The
generic plugin rule is implemented and verified: 17 tests pass, and the live
prefix scan reported 18 models with one already patched. Unrelated module
imports remain untouched.

Migration verification is documented in docs/validation.md. Several checks were
run against the source tree before migration and must be rechecked in Citric
before treating the copy as fully validated.
