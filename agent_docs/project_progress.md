# Project progress

Active deployment: `software_cursor_source_trace_20261015`. The user has
already reproduced the symptom visually: only Studio's software cursor inside
the Play viewport freezes after RMB camera movement is released, while the OS
cursor and scene remain responsive. The frame analyzer was discarded because
it would measure the symptom without identifying its source. Static Qt Cocoa
inspection confirms the AppKit event reaches `handleMouseEvent:` and the
imported `QWindowSystemInterface::handleMouseEvent<DefaultDelivery>` path;
the Studio renderer remains a stripped proprietary boundary. The untracked
`scripts/trace-studio-viewport-cursor.sh` is prepared to trace those exact Qt
handoff calls and `QCoreApplication::sendEvent`; syntax, whitespace, and
import-symbol checks passed, but it has not been run. Next milestone: use that
focused probe once, then inspect Qt receiver delivery and the Studio
`MouseService`/software-cursor render boundary. No root cause or fix is known.

No active deployment. The completed `explorer_input_diagnosis_20261015`
deployment found three related user-facing failures: Explorer Cut/Paste does
not work from the Edit menu or shortcuts, Explorer instance dragging produces
no preview or move, and Edit workspace shortcuts such as F and 1–5 do not
respond. The current installed binary is still Rosemary 0.2.3 while the
source pin is v0.3.0 and has not been rebuilt. Old source inspection shows
incomplete NSTableView selection and native drag/drop forwarding; shortcut
mapping exists but its delivery path is unverified. Next milestone: compare
the v0.3.0 overlay, implement only confirmed gaps, and validate with focused
tests before another manual session.

No active deployment. The completed `rosemary_v030_base_20261015` deployment
updated `patches/base-commit` to official Rosemary v0.3.0 commit
`91314d454fdb86e265228c0e43b53152fc5762ce` and reduced the active series to
`patches/0008-rosemary-v0.3.0-overlay.patch`. The aggregate overlay applies
cleanly to a fresh checkout of that commit and preserves Citric-specific
compatibility and diagnostic changes. No v0.3.0 Rust test suite, binary build,
or Studio run was performed; the next milestone is a clean offline build
followed by bounded Studio validation. See `docs/upstream-imports.md` for
reconciliation decisions and evidence.

No active deployment. The latest completed deployment is
`studio_software_cursor_trace_20261015`: the native Qt/QNSView cursor probe
was rejected as the wrong diagnostic boundary after the user clarified that
the OS cursor moves normally and only the cursor graphic drawn inside the Play
viewport freezes. The latest short capture recorded native
`cursorUpdate:` and `setCursor:` dispatch on QNSView, but no correlated Qt
input.mouse records or exact RMB action markers. This proves native cursor
callbacks were observed, while QWidget delivery and the rendered viewport
cursor remain unresolved. The cursor investigation
`hover_after_camera_20261015` remains unresolved. Only the Play cursor graphic
freezes after RMB camera movement is released; the scene continues rendering,
and SDL/mapped coordinates plus native tracking callbacks continue. This
predates the PR77–80 import. Local binary inspection found candidate Studio
software-cursor symbols/state (`RBX::MouseService::CursorCache`, `MouseIcon`,
cursor textures, and `RobloxViewStudio::updateNativeMouseIconVisibility`), but
no direct render-state trace has been implemented. The two startup gaps exposed by Qt logging
(`NSObject` description and NSString composed-character range) have been
implemented; the latest user run exited normally and reproduced the visual
freeze. Patch 0007 and `scripts/trace-studio-cursor.sh` remain diagnostic-only
and are insufficient for the software cursor. The next milestone is a direct
trace of the viewport cursor/cache or render-state boundary, followed by one
short user capture.

The earlier completed deployment is
`memory_stability_release_20261015`: the reconciled PR 77–80 import is present as
`patches/0003-upstream-pr77-80.patch` after the existing two overlays, with the
Rosemary v0.2.3 base still pinned. The imported runtime and compatibility
checks are documented in docs/upstream-imports.md; one pre-existing Metal
heap-fit test remains failing and is unchanged by the import. The rebuilt
runtime is validated by a bounded two-cycle Play/Stop capture with stable memory
after the second Stop. Diagnostics are now opt-in through
`STUDIO_MEMORY_TRACE=1` or `detailed`; longer-session confirmation remains
future work.

The previous latest completed deployment was
`appkit_button_cell_bezel_20261015`: the canonical patch now implements and
registers `-[NSButtonCell drawBezelWithFrame:inView:]` for the pinned Rosemary
v0.2.3 base. It draws only the bezel in the supplied frame using the supplied
control view, with a regression test for dispatch, ABI encoding, and rendered
frame dimensions. The patch applies cleanly, formatting passes, and the full
offline AppKit suite passed 337 unit tests plus one theme integration test.
The user launched Studio and confirmed that it opened normally after the fix.
Citric commit `30757c2` is pushed. The standalone Rosemary branch
`citric/nsbuttoncell-draw-bezel` is based on current main `01a5301`, passes 288
AppKit unit tests plus the theme integration test, and is pushed to the user's
fork; no official PR was opened.

The previous latest completed deployment was
`memory_attribution_20261015`: a detailed one-shot capture is prepared and
armed through the ignored `logs/.memory-trace-detailed-once` marker. It records
per-VMA addresses, permissions, labels/paths, sizes, RSS/PSS/swap, and
private/shared counters at periodic and Play/Stop snapshots, and enables
Rosemary `mmap`/`mprotect` request tracing. The default capture remains
redacted and the detailed JSONL is mode 0600 under ignored `logs/`.

Verification: `python3 -m unittest discover -s tests` passed 36 tests;
`bash -n scripts/run-studio.sh`, Python compilation, and `git diff --check`
passed. The next milestone is one short user-run Play/Stop cycle followed by
analysis; this mapping capture still cannot attribute allocator call stacks.

Latest completed deployment: `rosemary_set_current_context_pr_20261015`. The
AppKit current-context implementation is prepared as the single commit
`2004fef36d09c2dbd4ab5005777b7fad64caf54f` on the fork branch
`citric/nsgraphicscontext-current-context`, based directly on Rosemary
`main` at `01a5301a7955155d3b6d9872991bdfae9f9fcffc`. It adds retained
per-thread `NSGraphicsContext` state, replacement and nil clearing, teardown
cleanup, and regression coverage. The branch is clean and pushed to the
user's fork; opening the official PR remains a manual user action. The
companion factory implementation remains independently available on
`citric/nsgraphicscontext-cgcontext`.

The 2026-10-15 diagnostic audit closed a launch-environment gap: the
guest Studio process now receives `MIMALLOC_SHOW_STATS=1` through
`ROSEMARY_ENVIRON`, and the same one-shot run enables
`ROSEMARY_TRACE_INTERPOSE=1`. This makes the next bounded capture more useful
for allocator attribution while preserving normal-launch behavior. The
sampler still does not provide allocation call stacks, so the retaining
subsystem remains unresolved. The next milestone is one short Play/Stop
capture after host memory pressure recovers, followed by targeted Rosemary
cache counters or stack sampling if allocator output remains aggregate-only.

The source and automated preparation for the bounded memory capture are
complete, and the capture has been collected. `scripts/trace-studio-memory.py` recognizes sanitized
PlaySoloManager start/stop markers, emits immediate process/host snapshots at
those boundaries, and schedules 60-second and 120-second post-stop snapshots.
Boundary snapshots include a no-path/no-address `/proc/<pid>/smaps` aggregate
grouped by mapping kind and private/shared status. `scripts/run-studio.sh`
passes the session log to the tracer and requests `MIMALLOC_SHOW_STATS=1` only
for the diagnostic launch. The marker remains armed until Rosemary is observed
so an early startup failure does not consume it.

Verification is current: the full Python suite passed 30/30 before the final
shell formatting change; the focused memory and launcher suite passed 6/6
afterward; `bash -n`, Python compilation, and `git diff --check` passed. A
private parse of the ignored prior session found four Play starts and four
stops. The ignored trace `logs/run-20261015T010138-120845.memory.jsonl` records
one cycle: RSS plus swap grew 7.44 GiB from Play start to Stop and retained
7.37 GiB after 120 seconds. Anonymous mappings dominated the retained bytes
(about 3.05 GiB RSS and 7.61 GiB swap, plus named anonymous mappings), while
file mappings were negligible. Host swap peaked at 28.96 GiB, MemAvailable
reached 1.29 GiB, and OOM counters stayed at zero. The user closed Studio with
the window X; the trace recorded its final signal record and the launcher exit
code sidecar is `0`, confirming that capture shutdown completed. The next
milestone is allocation attribution with stack traces; this aggregate capture
already establishes abnormal Play-correlated retention but cannot identify its
owner.

The first complete Studio memory trace is available at
`logs/run-20261014T235818-107572.memory.jsonl` (ignored by Git). Across 37m50s,
the Studio/Rosemary process reached 26.33 GiB swap with a 6.10 GiB RSS
high-water mark; system swap rose from 13.17 to 43.82 GiB and MemAvailable
dropped to 0.61 GiB. The Studio main thread began reporting a hang around 29
minutes into the run. Kernel and cgroup OOM-kill counters stayed at zero, so
the evidence supports severe system-wide memory pressure but not a kernel OOM
kill. The process is a major source of swap use; the allocating subsystem is
unknown. VMA count, threads, and descriptors stayed comparatively stable and
do not explain the memory growth. The user force-killed the launch, leaving no
end record or exit code.
Four Play/Stop events in the captured log align with process memory increases:
the two longer cycles added 8.6 and 6.4 GiB of RSS+swap, with 7.2 and 6.0 GiB
still retained after one minute idle. This confirms Play-correlated retention,
but not yet a leak versus a persistent cache.
The arm marker remains set for a later bounded capture. Avoid another long,
unbounded reproduction and keep `--objc-debug` disabled.

Latest completed deployment: `split_clipboard_pr42_20261014`. The former
two-commit clipboard proposal was split into two independent one-commit
branches targeting current Rosemary main
`01a5301a7955155d3b6d9872991bdfae9f9fcffc`. `citric/pasteboard-carbon-bridge`
is `2b561ba87d7fcf542073487bbfae992d6500bcae` and
`citric/native-clipboard-actions` is
`b2ca8ba9c4bf41c6b41453995618957ba0038112`. The second contains native
AppKit/WebKit actions without depending on the first branch's test mutex. Both
are pushed to the user's fork. Official PR #42 remains open and
untouched because the user will close it and open replacement PRs manually.
Automated validation passed on both branches; manual Studio and external-Linux
clipboard validation remains pending. There is no active deployment.

Latest completed deployment: `studio_0743_graphics_context_20261014`. Studio
0.743.0.7431133's startup crash on the missing
`NSGraphicsContext graphicsContextWithCGContext:flipped:` selector is fixed in
the canonical patch. The installed Release binary was rebuilt from Rosemary
v0.2.3, and the headless smoke launch passed the former selector before
stopping at window creation because this environment has no display. A real
desktop restart through Citric is the remaining validation step. There is no
active deployment.

Latest completed deployment: `citric_studio_latest_update_20261014`. The
launcher automatically checks the published Mac Studio version and the update
button downloads and validates the matching build after the user clicks it.
Replacement remains confirmed and failure-safe. Automated tests pass; live
network and GUI update validation remain pending. There is no active deployment.

Latest completed deployment: `luau_locale_issue1_20261014`. Issue #1 was
confirmed as a locale-sensitive Luau decimal-literal parsing failure: the
bundled parser uses locale-sensitive `strtod` behavior, while arithmetic
division and `tonumber` follow different paths. Citric already mitigates this
when Studio is launched through `scripts/run-studio.sh` by clearing `LC_ALL`
and forcing `LC_NUMERIC=C`; the dedicated launch-contract test passes with
non-C inherited locales. The parser itself is inside the proprietary Studio
bundle, so no parser source change was made here. A locale-independent parser
fix belongs upstream in Luau. Manual Play confirmation through the latest
Citric launcher remains pending. There is no active deployment.

Latest completed deployment: `open_portal_fork_20261014`. The SDL file-picker
fallback and XDG Desktop Portal integration were split into two upstreamable
branches based on Rosemary v0.2.3 and pushed to the user's Rosemary fork:
`citric/sdl-file-picker` and `citric/xdg-file-chooser`. The second branch is
stacked on the first. Both commits are included in open Rosemary PR #40.
Automated validation passed for the isolated branches and the integrated
Citric patch. Manual portal/UI validation remains pending because no session
D-Bus was available. There is no active deployment.

Latest completed deployment: `clipboard_upstream_20261014`. The useful
clipboard fixes were isolated into two stacked Rosemary v0.2.3 branches and
pushed to `lAg201007/rosemary-citric-fixes`: `citric/pasteboard-bridge` and
`citric/clipboard-text-actions`. The first isolates Carbon/Cocoa pasteboard
aliasing, promised flavors, stale-format handling, and the 32-bit Carbon ABI;
the second adds native AppKit and WebKit copy, cut, paste, and select-all
actions. Both commits are included in open Rosemary PR #42. Manual Studio
validation remains incomplete while the PR is under review.

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
