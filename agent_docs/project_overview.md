# Project overview

Studio 0.743.0.7431133 exposed a missing `+[NSGraphicsContext graphicsContextWithCGContext:flipped:]` selector during startup. The AppKit compatibility layer now creates a retained Core Graphics-backed wrapper, exposes `CGContext` and `graphicsPort`, preserves the initial flipped state, and releases the context with the wrapper. Automated coverage and a release build pass; the headless smoke launch advanced beyond the selector but could not create a window without a display.

Citric is the local continuation of the Rosemary compatibility work for running
the macOS Roblox Studio client on Linux. Its current branch stores the
compatibility patches, launcher, scripts, and diagnostic record; Rosemary source
is materialized only in a temporary build checkout.

The AppKit overlay also registers `-[NSButtonCell drawBezelWithFrame:inView:]`
with the correct CGRect/object ABI and renders the requested bezel frame using
the supplied control view. Automated coverage and pinned-base application pass;
graphical Studio confirmation remains pending.

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

The current import deployment adds `patches/0003-upstream-pr77-80.patch` to
the series while keeping the Rosemary v0.2.3 base pinned. It reconciles
upstream runtime, autorelease-pool, drawable-lifetime, input/locale, and Qt
compatibility work with Citric's existing chooser and diagnostic changes.
Automated validation is recorded in docs/upstream-imports.md; the rebuilt
runtime awaits a bounded Studio Play/Stop memory test.

The launcher normalizes Studio's numeric locale to `C` and records the
before/after values. This addresses the observed Play failure where valid
decimal literals were reported as `Malformed number`; fresh manual Play
confirmation is still required.

The launcher also exposes a managed download action for the pinned official
Roblox Studio macOS x86_64 archive. The downloader verifies the recorded
checksum and app metadata before atomically installing the ignored bundle;
replacement of a different existing bundle requires an explicit GTK
confirmation.

At startup, the launcher makes an advisory request to Roblox's MacStudio
version endpoint when a compatible installed bundle is available. A newer
published version changes the action label to `UPDATE STUDIO NEW VERSION
<version>`. Selecting it refreshes the metadata, downloads the matching
official build, validates it, and asks before replacing Studio. The pinned
0.742.0.7421053 archive keeps its recorded SHA-256 check; newer releases are
validated by the official HTTPS source and bundle identity, version, build,
executable, and architecture. Citric does not claim runtime compatibility
testing for every newly published release.

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

The launcher also supports a one-shot memory investigation. When
`logs/.memory-trace-once` is armed, `scripts/run-studio.sh` starts the
privacy-conscious `scripts/trace-studio-memory.py` sampler before Studio and
stops it when the launch exits. The ignored JSONL trace samples the Studio
process tree and available host memory, swap, pressure, cgroup, and zram
metrics without recording command lines, environments, file paths, memory
contents, clipboard contents, or Studio log contents. The next normal Studio
session is the reproduction window; analysis remains pending until the user
returns its generated trace.

The memory investigation now recognizes only fixed `PlaySoloManager` start and
stop events from the session log. It emits privacy-safe boundary snapshots and
follow-up snapshots 60 and 120 seconds after Stop, including aggregate
`smaps` mapping categories, private/shared totals, and fixed VMA-size buckets
without addresses, labels, individual sizes, or paths. Boundary and periodic
30-second samples use the same privacy-preserving aggregation. A diagnostic
launch requests mimalloc shutdown statistics through `MIMALLOC_SHOW_STATS=1`;
the parser recognizes fixed footer rows and records only presence and numeric
summary fields. The bounded capture showed roughly 7.4 GiB retained after two
idle minutes, dominated by anonymous mappings and swap. A clean exit returned
status 0 and reduced host swap, but the 86.3 MiB mimalloc committed total does
not reconcile with process RSS, so allocation ownership remains unknown.

The next memory diagnostic supports an ignored
`logs/.memory-trace-detailed-once` marker. It records per-VMA identity and
addresses, permissions, labels/paths, mapping sizes, RSS/PSS, swap, and
private/shared counters in the local mode-0600 JSONL trace at the normal
cadence and Play/Stop checkpoints. The same run enables Rosemary's
`ROSEMARY_TRACE_VM=1` request logging for guest `mmap` and `mprotect`; the
summary helper keeps only fixed call counts. The default capture remains
redacted, and this mode still attributes mappings rather than allocation
call stacks.

The AppKit file-panel compatibility layer now uses Rosemary's shared SDL-backed
`chrome` file chooser for Import and Open from File. The latest manual retest
reached the chooser and navigated with Up; readable entries, selection, and
cancellation still need confirmation after the theme contrast fix.

The file-panel work is prepared as two stacked branches in the Rosemary fork
`lAg201007/rosemary-citric-fixes`: the SDL-backed chooser branch
`citric/sdl-file-picker`, followed by the XDG Desktop Portal branch
`citric/xdg-file-chooser`. Both commits are included in open Rosemary PR #40.
The SDL branch keeps the shared fallback independently usable; the portal
branch adds portal preference and fallback routing on top of it. Manual
Studio/portal validation is still pending.

The shared file chooser now includes a visible case-insensitive live name
search, hidden dotfile visibility toggled with Ctrl/Command+H, refresh with
Ctrl/Command+R, filtered keyboard navigation, and generic canvas-drawn icons
for common file types. Ctrl/Command+F focuses search. The AppKit panel
preserves the hidden-file preference through `showsHiddenFiles`, while SDL
modifier flags drive shortcut handling and the reusable chooser remains
independent of desktop-specific icon APIs. Automated verification is complete;
manual GUI retesting after the installed binary update remains pending.

The Save panel implements the `canSelectHiddenExtension` preference with a
false default and a real getter/setter, preventing Qt Cocoa's Save to File
configuration from aborting on the missing selector. Automated coverage is
complete; manual Save to File validation remains pending.

On Linux, AppKit file panels first try the XDG Desktop Portal FileChooser via
the Rust `ashpd`/`zbus` client. Expressible Open and Save options are mapped to
the portal, including Qt Cocoa's filter-only accessory view (one popup and one
label), while cancellation stays cancelled. Portal absence, errors, non-local
URIs, or unsupported options use the existing shared SDL/Chrome chooser. The
implementation has no GTK or `libportal` link dependency. Manual portal and
Studio validation remains pending.

On Linux, the AppKit event bridge maps Control chords to their macOS Command
shortcut equivalents for non-modifier keys, so Windows-style Studio shortcuts
such as Ctrl+S, Ctrl+O, Ctrl+F, and Ctrl+Z work through the same dispatch path.
Shift and left Alt are retained, right Alt/AltGr is passed through, and
`ROSEMARY_MENU_CTRL=0` disables the compatibility alias. Automated coverage is
complete; manual Studio shortcut validation remains pending.

Printable text input is routed through SDL's resolved text/IME commit for active
text clients. The duplicate AppKit key-down character is retained only for key
equivalent handling, preventing doubled characters in Studio search fields
while preserving Backspace and shortcuts.

Clipboard support covers both directions of the Linux/Studio boundary. Native
AppKit and WebKit text controls handle Control and Command copy, cut, paste,
and select-all paths. The SDL pasteboard bridge reads non-empty external text
even when the availability flag is unreliable, preserves local state when the
backend is unavailable, clears stale formats when an external clipboard is
confirmed empty, and avoids repeated change notifications for identical reads.
Carbon promised flavors are tracked separately from empty data; the
PromiseKeeper is registered and invoked, promised text is materialized eagerly
for SDL's eager UTF-8 API, other promised flavors resolve on demand, stale
external flavors are replaced, and Carbon item-count/item-ID outputs use the
required 32-bit ABI. Privacy-safe diagnostics are gated by
ROSEMARY_TRACE_CLIPBOARD and ROSEMARY_INPUT_TRACE. Manual validation remains
incomplete: Studio-to-search paste works, while cut, search-to-other-control
paste, and transfers involving external Linux applications still fail.

The reusable clipboard work is prepared for upstream review as two independent,
one-commit Rosemary branches in `lAg201007/rosemary-citric-fixes`:
`citric/pasteboard-carbon-bridge` contains the Carbon/Cocoa bridge and
`citric/native-clipboard-actions` adds native AppKit and WebKit text actions.
Both branches target current Rosemary main and are pushed to the fork; PR #42 remains open and
untouched for the user to close manually before opening replacement PRs. Full
manual Studio and external-application validation is still pending.

The PR 77–80 import is now the validated memory-stability candidate. The
launcher hides memory diagnostics during normal use; set
`STUDIO_MEMORY_TRACE=1` for aggregate capture or `STUDIO_MEMORY_TRACE=detailed`
for per-VMA and guest VM tracing when needed. In the latest bounded two-cycle
test, memory stopped growing linearly and stayed stable for two minutes after
the second Stop, with approximately 244 MiB above the settled baseline.
Longer sessions remain unverified.
