# Project progress

Latest deployment: citric_dark_picker_20261013; code and automated validation
are complete, and the user confirmed the Import chooser manually. Open from File
remains to be tested separately.

The user confirmed that a periodic roughly 0.5 second stutter occurs in Play
even in an empty Baseplate. A per-view trace isolated pixel-content copying
as the dominant cost. The first row-copy optimization only reduced median
composition from about 111 to 102 ms; the user retested and confirmed the
stutter remains. A follow-up build copied opaque pixels directly and skipped
transparent pixels; the user reported the same cadence but a much lighter
stutter. Its trace measured a 28.73 ms median composition every 499.91 ms. The
latest build skips completely transparent rows and records the Core Animation
call site that requests window damage. After restarting through Citric, the
user ran an empty Baseplate in Play for about 10 seconds and reported that the
stutter disappeared. The trace still records full-window damage roughly every
500 ms, but this no longer produces the reported visible stutter in the tested
session.

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

For the current stutter investigation, the latest trace from the pixel-level
optimization measured 712 compositions at a 28.73 ms median and 64.08 ms p95,
with a 499.91 ms median interval. The user reported that the cadence is the
same but the stutter is much lighter. The current build adds a fast path for
fully transparent rows and preserves the original Core Animation setter
location in damage traces. The canonical patch check, formatting, source diff
check, all 11 Core Animation tests, and Release build passed. The installed
binary SHA-256 is
`1c81b0f81f3483c4eb6ccbfe15437f5634b275fc574e380d4f7b7e0f710a2513`; ELF
build ID is `df984a5c36cf72f68b3704b10ee7c8b5a5ad7cb0`. The user manually
confirmed the visible stutter disappeared on this build.

The current deployment repaired dark-mode rendering of the Import/Open chooser.
The preceding retest no longer crashed and showed that Up navigated, but entries
had invisible names because list and fields were white while dark-theme text was
white. The chooser now uses a theme-specific input background. Chrome tests
(52), AppKit tests (295 plus the theme integration test), formatting, patch
application, source diff checks, and the locked offline Release build passed;
the updated binary is installed. The user restarted Studio through Citric and confirmed readable Import entries, file selection returning without a crash, and cancellation working. Separate Open from File validation remains pending. There is no active deployment after this retest.

The 2026-10-13 duplicate-text deployment is complete. The canonical patch now
prevents printable key-down and SDL text commits from inserting the same
character twice in active Studio text fields. The focused regression passed,
the release build was installed, and the user confirmed Toolbox and Explorer
search behavior. The full AppKit suite had two unrelated dark-theme named-color
failures; this does not block the validated fix. The next milestone is a new
user-selected compatibility issue.
