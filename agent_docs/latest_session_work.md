# Latest session work

Deployment: `clipboard_upstream_20261014`

State: complete; both upstream-ready branches are pushed to the user's fork
and are included in official Rosemary PR #42, which is open.

Outcome: clipboard compatibility was separated into two stacked Rosemary
v0.2.3 branches. `citric/pasteboard-bridge` contains Carbon/Cocoa named
pasteboard aliasing, legacy `NSStringPboardType` handling, external clipboard
synchronization, promised flavor materialization, and the 32-bit Carbon item
count/item ID ABI. `citric/clipboard-text-actions` adds native AppKit and
WebKit Control/Command copy, cut, paste, and select-all behavior on top of the
bridge. The branches are available in
`lAg201007/rosemary-citric-fixes`.

Verification: both branches have clean commit boundaries and are based on the
pinned Rosemary v0.2.3 checkout. Existing focused clipboard coverage and the
Citric Release validation are the supporting automated evidence. Manual
validation is still required for the full Studio and external-Linux-app
clipboard matrix; the latest recorded validation confirms several transfers
but still reports failures in some paste and shortcut paths.

Blockers: no source blocker. Manual Studio and external-Linux-app clipboard
validation remains incomplete while the official PR is open.

Exact next entry point: test both branches in a rebuilt Rosemary runtime and
report the results on PR #42; add a focused follow-up commit only if validation
finds a source issue.

Deployment token report: `clipboard_upstream_20261014` (unavailable; the
deployment-token-report skill and matching session record were not available).

Deployment: `open_portal_fork_20261014`

State: complete; both fork branches are included in official Rosemary PR #40,
which is open.

Outcome: the upstreamable file-panel work was separated into two stacked
Rosemary v0.2.3 branches. `citric/sdl-file-picker` contains the shared SDL
fallback and file-picker QoL behavior. `citric/xdg-file-chooser` builds on it
and adds XDG Desktop Portal Open/Save routing, filter mapping, cancellation,
fallback eligibility, and diagnostics. Both branches are available in
`lAg201007/rosemary-citric-fixes`.

Verification: the SDL branch passed its isolated locked offline AppKit and
Chrome tests, formatting, and diff checks. The integrated Citric patch passed
the pinned-base application, AppKit/Chrome tests, formatting, diff checks, and
the locked offline Rosemary v0.2.3 Release build. The current portal branch
was pushed after these checks. No session D-Bus or Studio GUI was available,
so portal appearance, Open/Save interaction, cancellation, and fallback
behavior still require manual validation.

Blockers: no source blocker. The session bus was unavailable during automated
validation, so manual portal and Studio testing remains pending while PR #40
is open.

Exact next entry point: test `citric/sdl-file-picker` and the XDG portal branch
in a desktop session with a working portal. Confirm Open, Save, filters,
cancellation, and SDL fallback, then report the results on PR #40.

Deployment token report: `open_portal_fork_20261014` (unavailable; no session
record matched this deployment ID).

Deployment: `xdg_open_portal_qt_filter_accessory_20261014`

State: complete in source and installed binary; manual Open from File portal
validation remains pending.

Outcome: Qt Cocoa's filter-only accessory view is now recognized when it has
exactly one popup button and one label. Its filter titles, globs, and selected
filter are mapped to XDG FileChooser filters. Arbitrary or unsupported
accessories and selection modes retain the shared SDL/Chrome fallback, and
fallback reasons are logged. This fixes the previously observed silent
fallback for Open from File.

Verification: 331 AppKit unit tests plus the theme integration test and seven
focused portal tests passed; `cargo fmt --all -- --check`, patched-source
`git diff --check`, `./scripts/build-studio.sh --check-only`, and the locked
offline Release build/install passed. Installed `bin/rosemary` reports v0.2.3,
SHA-256 `9021b8d129adc78a755a6fbff25fdbec3a152f51ab41b5ab3bee857f914ec3c6`,
ELF build ID `a99a35bb9f8857b26eaa5f7d0a09de79b25b5b42`.

Blocker: no source blocker. The current environment's session bus is
unreachable, so no Studio or portal UI test was possible.

Exact next entry point: fully restart Studio through Citric, open Open from
File with a working portal, verify the portal and filter selection, then verify
cancellation. Test an unavailable-portal case to confirm the SDL fallback.

Deployment token report: `xdg_open_portal_qt_filter_accessory_20261014`
(unavailable; no session record matched this deployment ID).

Deployment: `xdg_file_chooser_portal_20261014`

State: complete in source and installed binary; manual portal and Studio
validation remains pending.

Outcome: Linux `NSOpenPanel` and `NSSavePanel` now prefer the XDG Desktop
Portal FileChooser through the Rust `ashpd`/`zbus` client. Titles, prompts,
initial folders, save names, extension filters, and expressible selection
options are mapped to `OpenFile` and `SaveFile`. Portal cancellation remains
cancellation. Missing portals, D-Bus errors, non-local URIs, and unsupported
options use the existing shared SDL/Chrome chooser. No GTK or `libportal`
link dependency was added.

Verification: 329 AppKit unit tests plus the theme integration test and 55
Chrome tests passed; `cargo fmt --all -- --check`, source `git diff --check`,
clean application to pinned Rosemary v0.2.3, and the locked offline Release
build passed. Installed `bin/rosemary` reports v0.2.3, SHA-256
`234aa881598a2a522433b0e1110bac78af2904d947daac1fe4c0e8a2b975aebf`, ELF
build ID `a38787081ce80a766a5da89757fce32aea120b1a`.

The root diff check reports only lines containing one leading space in blank
context rows of the generated unified patch; this is required patch syntax.
The applied Rosemary source diff is clean.

Blockers: no source blocker. No session D-Bus portal interaction or Studio
launch was available, so portal appearance, Open, Save, cancellation, and
fallback behavior are unverified manually.

Exact next entry point: launch Studio through Citric with a working desktop
portal, test Open from File and Save to File, cancel both, then exercise a
fallback case with the portal unavailable or an unsupported panel option.

Deployment token report: `xdg_file_chooser_portal_20261014` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

Deployment: `rosemary_v023_base_migration_20261014`

State: complete in source and installed binary; manual Studio validation
remains pending.

Outcome: the canonical Citric patch was regenerated on Rosemary v0.2.3 at
commit `91e2de231604237ed5faa81513ba441d7b0a79bb`. Upstream's merged
implementations of `systemFontSizeForControlSize:`, `NSButtonCell` background
style, and Num Lock/keypad behavior were removed from the overlay. Citric's
Linux Control-to-Command mapping, file-picker improvements, Save panel fix,
and remaining compatibility work were retained.

Verification: the exact pinned base applied cleanly; 322 AppKit tests plus the
theme integration test and 55 Chrome tests passed; `cargo fmt -p appkit --
--check`, `git diff --check`, and the locked offline Release build passed.
Installed `bin/rosemary` has SHA-256
`af59637d4aef2490498d0b3efb47a206f32ef222321044351201dd984dcbad9e` and ELF
build ID `d8d7f314b6f2136a2738dbe90e165b8b0c99ae56`.

Blockers: no source blocker. The installed v0.2.3 binary has not yet been
launched into Studio. User validation remains pending for Linux Control
shortcuts, Open from File, and Save to File.

Exact next entry point: launch Studio through Citric using the installed
binary, test Ctrl-based Studio commands, then retest the file panels.

Deployment token report: `rosemary_v023_base_migration_20261014` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

Deployment: `shortcut_mapping_linux_20261014`

State: complete in source and installed binary; manual Studio shortcut
validation remains pending.

Outcome: Linux Control chords now act as aliases for macOS Command shortcuts
before AppKit dispatch. The mapping covers every non-modifier key, preserves
Shift and left Alt, passes right Alt/AltGr through for alternate characters,
and can be disabled with `ROSEMARY_MENU_CTRL=0`. Menu-equivalent handling and
text-input filtering share the same modifier policy.

Verification: 13 focused AppKit event tests, `cargo fmt -p appkit -- --check`,
`git diff --check`, and clean application to pinned Rosemary commit
`04dce85b63154d6451adf74e3f7bacf40add08bd` passed. Installed `bin/rosemary`
has SHA-256 `0cb1b632002760ee8aaa59a63e3abbfdcdef22cbc98102060fe56b149599ae55`
and ELF build ID `27914446907553df5e3b08a3ed2ac3257bb45c74`.

Blockers: no source blocker. Studio has not been retested for this deployment;
verify Ctrl+S, Ctrl+O, Ctrl+F, Ctrl+Z, and Ctrl+Shift+Z through Citric, plus
an AltGr character and the opt-out environment variable.

Exact next entry point: restart Studio through Citric with the installed
binary, exercise the listed Windows-style chords in Studio, then repeat one
test with `ROSEMARY_MENU_CTRL=0` and an AltGr layout.

Deployment token report: `shortcut_mapping_linux_20261014` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

Deployment: `save_panel_hidden_extension_20261014`

State: complete in source and installed binary; manual Save to File validation
remains pending.

Outcome: logs showed Qt Cocoa configuring `NSSavePanel` with the unimplemented
`setCanSelectHiddenExtension:` selector and aborting with exit 134. The
canonical patch now implements the `canSelectHiddenExtension` BOOL getter and
setter, with default false, and adds the round-trip regression test
`can_select_hidden_extension_preference_round_trips_on_save_panel`.

Verification: logs `logs/run-20261014T001508-166369.log:3658` and
`logs/run-20261014T000101-152331.log:3533` record the original abort. The
generated patch applies cleanly to pinned Rosemary commit
`04dce85b63154d6451adf74e3f7bacf40add08bd`; all 10 focused AppKit panel tests,
formatting, and the locked offline Release build passed. Installed
`bin/rosemary` has SHA-256
`2beeff9974531646b40c4730953fe432647f3418c98f008b10f038f5a0ab81c0` and ELF
build ID `1b24ede78a3a114e86a7ad252474f0ddaa87da5d`. Temporary `.savepanel-build/`
was removed.

Blockers: no source blocker. No Studio was launched, so Save to File behavior
and the absence of the abort are not manually confirmed. Preserve the
pre-existing untracked `scripts/run-mcp.sh`; do not stage, commit, push, or
configure remotes.

Exact next entry point: launch the installed binary through Citric, open Save
to File, confirm the panel opens, and exercise the hidden-extension preference.

Deployment token report: `save_panel_hidden_extension_20261014` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

---

Deployment: `picker_ui_applied_20261014`

State: complete in source and installed binary; manual GUI validation remains
pending.

Outcome: the canonical Rosemary patch was corrected after the prior installed
binary did not contain the described chooser changes. The shared picker now
renders a search field and hidden-file toggle, filters names case-insensitively,
maps SDL Ctrl/Command+F/H/R shortcuts, navigates the filtered list with
keyboard paging/home/end controls, and draws generic extension-based icons.
The AppKit panel now stores and returns `showsHiddenFiles` and filters dotfiles
at enumeration time. The implementation stays in shared `chrome` and AppKit
layers for future upstreaming.

Verification: the patch applies cleanly to pinned Rosemary commit
`04dce85b63154d6451adf74e3f7bacf40add08bd`; `cargo fmt --check -p chrome -p
appkit`, seven Chrome file-picker tests, nine AppKit panel tests including
filesystem dotfile enumeration and shortcut mapping, `git diff --check`, and a
Release build/install passed. Installed `bin/rosemary` reports 0.2.2 and has
SHA-256 `56b88570318096493dd99661ac031c3a0c93d5cfaf1d913036bf14fc2aa22ea4`
with ELF build ID `3b988a18fb8bf4f29fd06ed397ad6e5077234c0c`. Binary strings
confirm the search and hidden-file labels. No GUI interaction or visual check
was run; restart Studio through Citric and manually test Import, Open from
File, and Save panels, including Ctrl/Command+H.

Blockers: no source blocker. Manual interaction is the remaining validation.
The pre-existing untracked `scripts/run-mcp.sh` is preserved. No commit, push,
remote, or unrelated change was made by the deployment.

Exact next entry point: launch the newly installed binary through Citric,
open a file panel, confirm the controls are visible, press Ctrl/Command+H,
and verify dotfiles appear and disappear. Then test search and refresh.

Deployment token report: `picker_ui_applied_20261014` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

---

Deployment: citric-generic-plugin-bit32-20261012

State: complete for the generic plugin compatibility change. The user
confirmed that the Baseplate which previously failed opens after the original
plugin fix. A separate Play attempt emitted `Malformed number` for valid
decimal literals in Roblox's bundled PlayerModule, plugins, and place scripts.
That locale issue remains separate and unconfirmed.

Material changes: `scripts/run-studio.sh` now removes inherited `LC_ALL` and
sets `LC_NUMERIC=C` for Studio. It records source and effective locale values
in session metadata. `tests/test_run_studio_locale.py` verifies the contract
under `pt_BR.UTF-8`, and `docs/numeric-locale.md` documents the diagnosis and
required manual check.

Verification: the locale regression test and shell syntax check passed during
its deployment; no fresh Play session was run after the locale change. The
token report is unavailable because no matching session record was found.

Separate pending check: restart Studio through `scripts/run-studio.sh`, open
the affected place, and try Play. Inspect new `.log` and `.meta` files. If
`Malformed number` remains, investigate the runtime's `strtod` locale path.
Complex mouse tests remain user-driven and are unrelated to this check.

The user asked to replace the plugin-specific override with a general rule.
The initial crash evidence remains specific: `BlenderAnimationsInternal`
loaded immediately before a fatal bare-`bit` require, and its model contains
`requireany("bit", "bit32", "bit.numberlua", nil)`.

The launcher now uses `scripts/patch_plugin_compatibility.py`, which scans all
`InstalledPlugins/<plugin-id>/<version>/Plugin.rbxm` models in the Rosemary
prefix, independent of plugin ID. It patches only the exact legacy source
signature, preserves unrelated RBXM chunks, and creates a verified
content-addressed backup. Unknown or ambiguous models and unrelated `require`
patterns remain unchanged. The launcher, locale test, generic plugin tests,
project notes, and user-facing plugin documentation use the generic helper.

Verification completed: all 17 Citric tests pass, `bash -n scripts/run-studio.sh`
and `git diff --check` pass. The live prefix scan reported 18 models scanned,
0 newly patched, 1 already patched, 17 unchanged, and 0 unsupported. The user
confirmed the formerly failing Baseplate opens with the plugin enabled.

Exact continuation point: none for this deployment. Camera behavior and the
separate numeric-locale Play validation remain open. Do not broaden the rule
to arbitrary `require` names without evidence and a safe compatibility mapping.

Token report: `unavailable`; no matching session record was available for
`citric-generic-plugin-bit32-20261012`.

---

Deployment: citric-play-periodic-stutter-20261012

State: the user-visible stutter is resolved in the latest tested build. On
2026-10-12, the user restarted through Citric, ran an empty Baseplate in Play
for about 10 seconds, and reported that the stutter disappeared.

The user confirmed the stutter persists with per-view profiling. The trace
measured 110.71 ms median slow window composition every 499.69 ms, with
109.78 ms in `compose_render_background_total`. Across 3,658 slow view records,
`contents_ms` had a 7.16 ms median and 25,773.7 ms cumulative time; presentation
and fill were negligible. Every slow view had contents and no background.

The first optimization uses clipped row copies for exact-size, opaque BGRA
contents. The user retested and confirmed the stutter remained. In the next
trace, all 95 slow-view records selected `exact_copy`; images had matching
source and placed dimensions, no channel swap, and full layer opacity. However,
82 records had only one fully opaque row. Mixed rows still ran the four-channel
blend for every pixel, including fully opaque pixels, and did not skip fully
transparent zero pixels. The current implementation copies opaque pixels
directly, leaves exactly transparent pixels unchanged, and source-over blends
only remaining pixels. It records opaque rows/pixels and transparent/blended
pixel counts. Scaled images and RGBA surfaces remain on the generic path.

The user tested that build and reported the same 0.5-second stutter, but much
lighter. Its trace measured 28.73 ms median composition, 64.08 ms at p95, and
499.91 ms median between compositions across 712 samples. The remaining
composition still redraws the full 1920x1052 window. The current build adds a
transparent-row skip and propagates `#[track_caller]` through Core Animation
damage. The latest run log still records full-window damage for a 1920x1052
region at a median interval of about 499.9 ms, while the visible stutter
disappeared in the user's retest. Treat the visible symptom as resolved; the
remaining periodic invalidation is a separate diagnostic detail and does not
currently block use.

Verification: the canonical patch applies to the pinned base; `cargo fmt
--all -- --check`, source `git diff --check`, all 11 focused Core Animation
tests, and the Release build/install pass. The full AppKit suite previously
passed 281/283 tests; the same two named-color assertions expected black
`textColor` but received white, an unrelated issue. The installed binary
SHA-256 is `1c81b0f81f3483c4eb6ccbfe15437f5634b275fc574e380d4f7b7e0f710a2513`;
ELF build ID is `df984a5c36cf72f68b3704b10ee7c8b5a5ad7cb0`.

Exact continuation point: no further stutter retest is needed unless the user
reports it returning. If it does, inspect transparent-row counts and the
damage setter call sites in a fresh trace. Keep raw logs outside Git.

Token report: `citric-play-periodic-stutter-20261012` is unavailable; no
matching session record was found.

Historical deployment record: the Citric branch snapshot is patch-only: Rosemary source was
removed from the current tree, while `patches/base-commit`, `patches/series`,
and `patches/upstream-url` define the reproducible overlay. The original
Rosemary ancestry was removed from the branch history while the four Citric
commits were preserved. The first preserved Citric commit records the initial
workspace snapshot; the current tree contains no Rosemary source. GitHub still
treats Citric as an independent repository.

The GTK 4 launcher was added under `citric_launcher/` with `scripts/citric`,
XDG configuration, place selection, diagnostics, and desktop-menu integration.
The launcher delegates to `scripts/run-studio.sh`; it does not package or
download the proprietary Studio bundle.

Material changes include removal of the Rosemary source from the current
snapshot, the canonical patch overlay build path, GTK launcher sources and
tests, and updated migration documentation. The copied app is Studio
0.742.0.7421053; hashes are in docs/bundle.md and the manifest.

Verification evidence: `scripts/build-studio.sh --check-only`, a full offline
`--build-only` in a dedicated cache using the pinned commit, six launcher tests,
shell syntax checks, and `git diff --check` passed. The validation cache was
removed; the ignored bundle, binary, downloads cache, prefix, and logs were
preserved. The GTK GUI smoke test could not be fully validated in the available
display session. Manual Studio work ended with an unresolved crash opening the
large place and unresolved camera/docking edge cases.

Exact continuation point: run scripts/run-studio.sh with a fresh STUDIO_LOG_NAME
and reproduce the place-opening crash normally. Preserve the raw log outside
Git, then isolate the require path failure before changing camera behavior.

---

Deployment: citric_dark_picker_20261013

State: code and automated verification complete; Import manual validation passed.

Outcome: the Import/Open chooser no longer crashed after Rosemary implemented
the missing AppKit and Foundation compatibility calls. The user confirmed that
the chooser opens and that Up navigates. The entries then appeared white with
invisible names in dark appearance. The patch changed the chooser's list,
location, and save-name surfaces to use the theme-specific input background.

Verification: 52 chrome tests, 295 AppKit tests plus the theme integration test,
package-scoped formatting, source diff checks, locked offline Release build,
clean pinned-base patch application, and the focused dark-mode rendering test
passed. The updated binary is installed. The latest evidence is
`logs/run-20261013T213755-38660.log`; raw logs remain outside Git.

Pending: test Open from File separately. The user confirmed that Import shows readable names, selecting a file returns to Studio without a crash, and cancellation works. Arbitrary accessory-view rendering remains unverified. Continue from `docs/current-state.md` and `docs/validation.md` if that scope resumes.

Token report for `citric_dark_picker_20261013`:

Deployment token report: `citric_dark_picker_20261013` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warning: no session record matched this deployment ID.

Token report: `unavailable`; no matching session record was available for this
deployment.

---

Deployment: citric_duplicate_text_input_20261013

State: complete. Studio text fields duplicated printable characters because
AppKit `keyDown:` and SDL `TEXT_INPUT` both inserted them. The canonical patch
now sanitizes printable key-down characters only for active text input clients,
while retaining the original characters for key equivalents and keeping SDL
text/IME commits, Backspace, shortcuts, key-up events, and non-text responders
unchanged.

Verification: the focused AppKit regression passed; the release build was
installed and the user confirmed that Toolbox and Explorer searches insert
each character once and that one Backspace removes one character. The full
AppKit suite ran 296 tests with 294 passing and two unrelated dark-theme
named-color failures. Formatting, source diff, and clean patch application
checks passed. The next entry point is the next user-selected compatibility
issue; do not rerun this test unless duplication returns.

Token report for `citric_duplicate_text_input_20261013`:

Deployment token report: `citric_duplicate_text_input_20261013` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

---

Deployment: citric_clipboard_promises_20261013

State: paused with implementation and automated validation complete; manual
clipboard validation remains incomplete.

Outcome: the Carbon pasteboard bridge now distinguishes promised flavors from
genuinely empty CFData, registers and invokes PromiseKeeper callbacks,
materializes promised text eagerly for SDL's eager UTF-8 clipboard interface,
resolves non-text promises on demand, replaces stale local flavors when the
external clipboard changes, avoids resynchronizing over a local write, and
uses UInt32/u32 for Carbon item-count and pasteboard-item-ID output. Regression
coverage was added for promise callbacks, on-demand non-text resolution,
stale external flavor replacement, and the 32-bit output canary.

Verification: 15 focused pasteboard tests passed with the low-disk test
profile, the locked offline release build passed, formatting and source diff
checks passed, and the generated canonical patch applied cleanly to the pinned
Rosemary base. The installed `bin/rosemary` hash is
`280140f9a9a8324ccef9564953832234c8f6a9c144ce979fcce9df342b67daa3`.
An earlier debug-profile attempt ran out of temporary disk space; that attempt
was superseded by the successful low-disk verification.

Manual evidence: Studio-to-search paste works in the latest user report, but
cut does not; search-to-other-Studio paste remains broken; and clipboard
transfers to or from external Linux applications remain broken.

Exact continuation point: launch a fresh Citric session with
`ROSEMARY_TRACE_CLIPBOARD=1` and `ROSEMARY_INPUT_TRACE=1`, reproduce one
external-to-Studio failure and one search-to-other-control failure, and inspect
metadata-only traces. Do not log clipboard contents. Preserve the existing
user-owned `scripts/run-mcp.sh` and unrelated working-tree changes. No commit
or push was made by this handoff.

Token report for `citric_clipboard_promises_20261013`:

Deployment token report: `citric_clipboard_promises_20261013` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warning: no session record matched this deployment ID.

---

Deployment: citric_clipboard_20261013

State: implementation complete; manual UI retest is pending. The implementation and installed
release binary are complete.

Outcome: the reported clipboard asymmetry was addressed. Toolbox and Explorer
could export copied text to Linux, but text copied in another Linux app could
not be pasted into Studio. The SDL pasteboard bridge now always queries the
system text value, accepts a non-empty value even when SDL reports unavailable,
tracks the last observed or exported system value, preserves local state when
the backend cannot answer, clears stale text and HTML on confirmed empty
external state, and avoids change-count churn for identical observations.
Native AppKit text responders now implement copy/cut and Control/Command
C/X/V/A handling. The WebKit script editor accepts Control shortcuts as well as
Command shortcuts. Plain copy/cut clears stale rich HTML formats.

Verification: `CARGO_PROFILE_RELEASE_DEBUG=0 CARGO_INCREMENTAL=0 cargo build
--locked --offline --release -p rosemary` passed; focused pasteboard tests
passed 7/7; focused text tests passed 21/21; rustfmt and `git diff --check`
passed; and the generated canonical patch applied cleanly to the pinned
Rosemary base. The installed `bin/rosemary` is ignored. These checks are newer
than the clipboard source changes. Manual Studio retest is not yet available.

Exact continuation point: restart Studio through Citric and test external text
paste into Toolbox and Explorer, native property/editor copy and paste, script
editor Control shortcuts, and an external Linux application. Preserve the
existing user-owned `scripts/run-mcp.sh` and unrelated working-tree changes.

Token report: unavailable; no matching session record was found for
`citric_clipboard_20261013`.

---

Deployment: citric_clipboard_followup_20261013

State: paused with implementation and automated validation complete, but the
user-visible clipboard contract still failing in multiple controls.

Outcome: the follow-up patch added selection-only field editors for selectable
read-only NSTextField controls, blocks paste/host text commits/IME composition
in those editors, synchronizes the SDL system clipboard before WebKit exposes
general text and HTML, walks focused responder ancestors for key-equivalent
handling, and lets WKWebView recognize focused descendants. Privacy-safe
ROSEMARY_TRACE_CLIPBOARD and ROSEMARY_INPUT_TRACE diagnostics record metadata
only. The user confirmed Ctrl+C and Ctrl+X in Toolbox and Explorer, but Ctrl+V
still fails there; all three clipboard shortcuts remain broken elsewhere,
including the script editor and properties.

Verification: locked offline Release build, seven pasteboard tests, 21 text
tests, rustfmt, source git diff checks, and clean application of the generated
patch to the pinned Rosemary base passed. No commit or push was made.

Pending: restart with `ROSEMARY_TRACE_CLIPBOARD=1` and
`ROSEMARY_INPUT_TRACE=1`, reproduce one Toolbox/Explorer paste failure and one
script-editor or property shortcut failure, and inspect the metadata trace.
The next code entry point is AppKit focused-responder/key-equivalent dispatch
and WebKit clipboard offering. Preserve user-owned launcher changes,
`scripts/run-mcp.sh`, and canonical patch additions.

Token report for `citric_clipboard_followup_20261013`:

Deployment token report: `citric_clipboard_followup_20261013` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

---

Deployment: launcher_studio_bundle_20261013

State: implementation complete; end-to-end download remains pending network
access and user validation.

Outcome: the GTK launcher now has a `Download and install Roblox Studio`
button. It invokes `citric_launcher/studio_bundle.py`, which downloads the
pinned official Roblox macOS x86_64 archive, verifies its SHA-256, validates
the bundle identifier/version/executable/architecture, safely extracts it to
ignored staging storage, and installs it at `app/full/RobloxStudio.app`.
When another bundle is already present, the launcher requires an explicit
replacement confirmation; failed validation leaves the destination unchanged.

Material files: `.gitignore`, `README.md`, `citric_launcher/app.py`,
`citric_launcher/core.py`, `citric_launcher/studio_bundle.py`,
`docs/bundle.md`, and `docs/current-state.md`.

Verification: `py_compile`, the downloader `--help` path, and a scoped
whitespace check passed. The real network download was not run because shell
DNS resolution failed with `Temporary failure in name resolution`; therefore
archive retrieval, extraction, and installation are not yet end-to-end
verified. Proprietary bundles, Rosemary binaries, Darwin cache, and logs remain
ignored. Unrelated working-tree changes in `patches/0001-citric-runtime-compat.patch`
and `scripts/run-mcp.sh` were preserved.

Exact next entry point: run the launcher with network access, click the download
button, confirm the installed bundle is detected, and refresh `docs/bundle.md`
if the installed manifest differs from the recorded local snapshot.

Token report: `unavailable`; no matching session record was available for
`launcher_studio_bundle_20261013`.

---

Deployment: studio_update_label_20261013

State: complete; the launcher implementation and local automated checks are
finished. Live endpoint/network access and GTK GUI behavior remain unverified
in this environment.

Outcome: the GTK launcher now checks Roblox's published Mac Studio version at
startup when it can identify the selected installed bundle. If the published
version is newer, it changes the action label to `UPDATE STUDIO NEW VERSION
<version>`. Citric does not install that release automatically. Clicking the
action for a release newer than the validated pin explains that only
0.742.0.7421053 can currently be installed and leaves the existing bundle
unchanged; the pinned installer still handles its verified archive normally.

Material changes are in `citric_launcher/app.py`, `citric_launcher/core.py`,
`citric_launcher/studio_bundle.py`, `README.md`, `docs/bundle.md`, and
`docs/current-state.md`. The checker validates the endpoint host, response
size, JSON shape, version, and build identifier before comparing numeric
version components. The existing pinned checksum and compatibility boundary
were preserved.

Verification: Python compilation, six launcher unit tests, version-comparison
smoke checks, and a scoped `git diff --check` passed. The live Roblox endpoint,
network retrieval, and GTK click behavior were not exercised here. Existing
unrelated changes, including `patches/0001-citric-runtime-compat.patch` and
the untracked `scripts/run-mcp.sh`, remain preserved.

Exact next entry point: run the launcher with network access and a compatible
installed bundle, verify that the label follows the published version, and
click it once for a newer unvalidated release to confirm the explanatory status
and unchanged bundle.

Token report for `studio_update_label_20261013`:

Deployment token report: `studio_update_label_20261013` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID

---

Deployment: file_picker_qol_20261013

State: complete for the shared file-picker QoL patch. The implementation is
ready for later upstream review; no commit, push, or Rosemary pull request was
created by this handoff.

Outcome: the shared `chrome::FilePicker` now has a case-insensitive live name
search, Ctrl/Command+F focus, Ctrl/Command+H hidden dotfile visibility,
Ctrl/Command+R refresh, filtered Home/End/PageUp/PageDown and arrow navigation,
and generic canvas-drawn icons for folders, packages, images, video, audio,
archives, code, text, and documents. AppKit `NSOpenPanel` and `NSSavePanel`
expose and preserve `showsHiddenFiles`; the reusable chooser does not depend on
desktop-native icon APIs. Wine research informed the existing filter and
navigation concepts, while the dotfile shortcut is recorded as Rosemary
behavior rather than attributed to Wine.

Material change: only `patches/0001-citric-runtime-compat.patch` contains the
production implementation. The preexisting untracked `scripts/run-mcp.sh` was
preserved untouched.

Verification: a clean checkout of pinned Rosemary base
`04dce85b63154d6451adf74e3f7bacf40add08bd` accepted the patch with
`git apply --check`; `cargo fmt --check -p chrome -p appkit` passed;
`CARGO_INCREMENTAL=0 CARGO_BUILD_JOBS=2 CARGO_PROFILE_DEV_DEBUG=0
CARGO_PROFILE_TEST_DEBUG=0 cargo test --locked --offline -p chrome
file_picker::tests` passed 7 tests; corresponding focused AppKit panel tests
passed 8 tests. No GUI visual test was run, so icon contrast and shortcut
behavior still need manual validation in Studio.

Exact next entry point: build or install the patched Rosemary runtime, open
Import/Open/Save in Studio, and manually verify search, dotfile visibility,
refresh, filtered keyboard navigation, and icon readability in both themes.

Token report for `file_picker_qol_20261013`:

Deployment token report: `file_picker_qol_20261013` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warnings:
- no session record matched this deployment ID
