# Project progress

Latest completed deployment: `xdg_open_portal_qt_filter_accessory_20261014`.
The portal path now accepts Qt Cocoa's filter-only accessory view, maps its
name filters and selected filter to XDG filters, and logs unsupported
accessory/selection fallback reasons. The installed Rosemary v0.2.3 binary is
updated and automated validation passed. No session D-Bus or Studio GUI was
available, so Open from File still requires a full manual restart through
Citric. There is no active deployment.

Latest completed deployment: `rosemary_v023_base_migration_20261014`. Citric
is now pinned to Rosemary v0.2.3 at commit
`91e2de231604237ed5faa81513ba441d7b0a79bb`. The canonical overlay was
regenerated against that base, and changes already merged upstream for
`systemFontSizeForControlSize:`, `NSButtonCell` background style, and Num Lock
were removed from the overlay. The v0.2.3 Release binary is installed and
automated validation passed. Manual Studio validation remains pending. There
is no active deployment.

Latest completed deployment: `shortcut_mapping_linux_20261014`. The canonical
patch and installed Release binary map Linux Control chords to macOS Command
shortcuts for all non-modifier keys, preserve Shift and left Alt, pass AltGr
through, and support the `ROSEMARY_MENU_CTRL=0` opt-out. Automated validation
is complete; manual Studio shortcut validation remains pending. There is no
active deployment.

Latest completed deployment: `picker_ui_applied_20261014`. The canonical
file-picker patch and installed Release binary now contain visible search and
hidden-file controls, modifier-aware shortcuts, filtered navigation, and
generic icons. Automated validation is complete; manual Studio retesting after
restart remains pending. There is no active deployment.

Latest source follow-up: `save_panel_hidden_extension_20261014`. The missing
NSSavePanel `canSelectHiddenExtension` getter/setter is implemented and tested,
and the Release binary is installed. Save to File manual validation remains
pending; there is no active deployment.

Latest completed deployment: `xdg_file_chooser_portal_20261014`. Linux AppKit
Open and Save panels prefer the XDG Desktop Portal FileChooser through
`ashpd`/`zbus`, preserving cancellation and falling back to the shared SDL
chooser for unavailable portals, errors, non-local URIs, or unsupported panel
options. Automated validation and the v0.2.3 Release build passed; no session
D-Bus or Studio GUI was available, so portal behavior remains pending manual
validation. There is no active deployment.

Latest completed deployment: file_picker_qol_20261013. Its patch and focused
automated checks are complete; no GUI visual test was run. There is no active
deployment.

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

The file-picker QoL deployment is complete. The canonical patch extends the
shared chooser with case-insensitive live name search, Ctrl/Command+F search
focus, Ctrl/Command+H dotfile visibility, Ctrl/Command+R refresh, filtered
Home/End/PageUp/PageDown navigation, and generic extension-based icons. The
AppKit panel exposes and preserves the hidden-file preference. A clean pinned
base accepted the patch; formatting, seven focused chrome tests, and eight
focused AppKit panel tests passed. No GUI visual test was run. Future manual
work can verify the controls in Import/Open/Save and assess icon contrast in
both themes.

The 2026-10-13 duplicate-text deployment is complete. The canonical patch now
prevents printable key-down and SDL text commits from inserting the same
character twice in active Studio text fields. The focused regression passed,
the release build was installed, and the user confirmed Toolbox and Explorer
search behavior. The full AppKit suite had two unrelated dark-theme named-color
failures; this does not block the validated fix. The next milestone is a new
user-selected compatibility issue.

The current deployment is `citric_clipboard_promises_20261013`. Its source
patch and release build are complete, but the manual retest still fails in
several paths. The Carbon bridge now resolves promised flavors, eagerly
materializes promised text for SDL, replaces stale external formats, avoids
local-write resynchronization, and uses the correct 32-bit item-count and
item-ID ABI. Studio-to-search paste works in the latest report, while cut,
search-to-other-control paste, and all transfers involving external Linux
applications still fail.
The canonical patch now synchronizes non-empty SDL clipboard text despite a
false availability result, preserves local state when the backend is
unavailable, clears stale plain text and HTML on confirmed empty external
clipboard state, and makes identical observations idempotent. Native AppKit
text responders and the WebKit editor accept Control and Command clipboard
shortcuts; plain copy/cut clears stale HTML.

Verification completed: 15 focused pasteboard tests, locked offline Release
build, rustfmt, source diff checks, and clean application of the generated
patch to the pinned Rosemary base. The installed `bin/rosemary` is ignored;
its current hash is `280140f9a9a8324ccef9564953832234c8f6a9c144ce979fcce9df342b67daa3`.
The first debug-profile attempt ran out of temporary disk space; the
low-disk release-profile verification passed. Exact continuation point:
launch with `ROSEMARY_TRACE_CLIPBOARD=1` and `ROSEMARY_INPUT_TRACE=1`, then
reproduce external-to-Studio and search-to-other-control paths. Do not treat
clipboard input as fixed until those manual paths pass.

The `launcher_studio_bundle_20261013` deployment is implementation-complete.
The GTK launcher now offers download and install of the pinned Roblox Studio
0.742.0.7421053 macOS x86_64 archive. The downloader validates the pinned
SHA-256 and bundle metadata, extracts through a safe staging directory, and
replaces a different local bundle only after launcher confirmation. `py_compile`,
the downloader help path, and a scoped whitespace check passed. End-to-end
network download and installation remain unverified because DNS resolution was
unavailable in this environment. No active deployment remains after this
handoff; the next milestone is user validation of the button with network
access.

The `studio_update_label_20261013` deployment is complete. On launcher startup,
Citric checks Roblox's published Mac Studio version asynchronously against the
selected installed bundle. When a newer version is published, the button is
renamed to `UPDATE STUDIO NEW VERSION <version>`. Citric does not auto-install
that release: the pinned 0.742.0.7421053 build is the only validated installer,
and selecting the button for a newer unvalidated release leaves the installed
bundle unchanged while explaining the limitation.

Verification completed with Python compilation, six launcher unit tests,
version-comparison smoke checks, and a scoped whitespace check. The live
endpoint/network and GTK GUI behavior were not exercised in this environment.
There is no active deployment; the next entry point is a manual launcher run
with network access to verify the label and guarded click behavior.
