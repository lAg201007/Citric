# Project core technology

Rosemary is a Rust 2024 workspace that loads macOS Mach-O applications through
native or Microlift-backed execution and supplies Darwin, Objective-C,
CoreFoundation, AppKit, Metal, and SDL compatibility layers.

The AppKit compatibility layer now has an upstream-ready implementation of
`+[NSGraphicsContext setCurrentContext:]` in the fork branch
`citric/nsgraphicscontext-current-context`. It stores an explicitly selected
context per thread, retains it until replacement or clearing, and releases it
when the thread-local state is destroyed. An explicit nil value suppresses the
focused-view fallback, matching AppKit's current-context semantics.

Citric targets the Linux execution path. scripts/run-studio.sh selects the
local release binary, validates and patches the Studio app when required, uses
the local Darwin cache, and defaults SDL to X11/XWayland because that avoided a
reappearing non-modal plugin-loading window during the recorded tests.

In `crates/appkit/src/backing.rs`, `NSGraphicsContext` wraps a retained
`CGContextRef` for `graphicsContextWithCGContext:flipped:`. The wrapper stores
the initial flipped flag until a focused view supplies the live value, returns
the Core Graphics handle through both AppKit accessors, and releases the
handle during deallocation. This is required by Studio 0.743 startup and is
implemented without a host-specific workaround.

`NSButtonCell` registers `drawBezelWithFrame:inView:` with the full CGRect and
object-argument ABI used by AppKit. Its implementation renders only the bezel
inside the supplied frame and takes control state from the supplied view; the
existing combined bezel-and-title path remains separate. This avoids the
startup selector abort while keeping the method suitable for upstream
Rosemary. A focused regression covers registration, encoding, frame dimensions,
and Objective-C dispatch.

The compatibility diff includes AppKit window/view/input behavior,
CoreFoundation lifetime handling, Objective-C autorelease safety, keyboard/font
compatibility, and diagnostic logging. `patches/0001-citric-runtime-compat.patch`
is now the authoritative source representation; Rosemary is fetched into a
temporary checkout only for applying and building it.

The current canonical patch is `patches/0001-citric-runtime-compat.patch`,
applied to the pinned base in `patches/base-commit` and ordered by
`patches/series`. The older patch files remain historical snapshots. Citric's
GTK 4 Python launcher delegates execution to `scripts/run-studio.sh`; it does
not include the proprietary Studio bundle in Git. Its optional downloader
fetches a pinned Roblox CDN ZIP or the build named by the latest release
metadata, checks the pinned SHA-256 when available, validates the bundle
identifier/version/build, executable, and Intel Mach-O slice, and installs it
under the ignored `app/full/RobloxStudio.app` path with a replacement
confirmation.

`patches/0003-upstream-pr77-80.patch` is the reconciled import layer for the
upstream Rosemary PR 77–80 snapshots. It adds sharded runtime references and
caches, per-turn autorelease pools, drawable/layer retirement, input and
locale behavior, and selected Qt/AppKit/Foundation APIs while retaining
Citric's portal/fallback chooser and diagnostics. Its source revisions,
conflicts, and test evidence are recorded in docs/upstream-imports.md.

`citric_launcher/studio_bundle.py --check-update` queries
`clientsettings.roblox.com/v2/client-version/MacStudio`, validates the returned
version and build identifier, and compares numeric version components. The GTK
launcher runs this check asynchronously and updates its button label when a
newer release exists. Clicking the update action refreshes the metadata and
downloads that release; it never replaces Studio without confirmation. Dynamic
releases have no recorded per-release checksum, so archive limits, safe paths,
official host/path checks, and bundle metadata validation are used instead.

The launcher clears inherited `LC_ALL` and forces `LC_NUMERIC=C` for Studio.
Launch metadata records both the incoming and effective numeric locale values
so decimal-literal failures can be diagnosed.

In `crates/appkit/src/event.rs`, printable key-down characters are removed from
the event delivered to an active text input client when SDL will also deliver a
layout-resolved text commit. The original characters remain available to key
equivalent processing; controls, shortcuts, key-up events, and non-text
responders retain their existing behavior.

The same AppKit event boundary maps Linux Control chords to macOS Command
shortcuts for every non-modifier key when `ROSEMARY_MENU_CTRL` is enabled.
Shift and left Alt are preserved, while right Alt/AltGr passes through so
keyboard layouts can produce alternate characters. The mapping is opt-out via
`ROSEMARY_MENU_CTRL=0` and is implemented generically rather than as a list of
Studio commands.

Before Studio starts, `scripts/patch_plugin_compatibility.py` scans cached
`Plugin.rbxm` models across every plugin ID and version in InstalledPlugins.
It replaces only the exact legacy `requireany("bit", "bit32", ...)`
declaration with the built-in `bit32` module. The helper rewrites the matching
LZ4 chunk, preserves unrelated chunks, performs an atomic replacement, and
keeps a verified hash-named backup. Unsupported or ambiguous models are left
unchanged; the post-exit pass catches plugins installed or updated during a
run.

Do not copy the authenticated prefix or raw logs into Git. Do not publish the
proprietary app bundle without an explicit later decision.

For the current Studio memory-leak investigation, `scripts/trace-studio-memory.py`
is a low-overhead Linux `/proc` sampler. It follows the launcher parent and its
descendants, records per-process RSS/PSS/anonymous/swap memory, thread count,
file descriptors, VMA count, page faults, CPU time, and I/O counters, and
periodically records host memory/swap, vmstat, memory PSI, cgroup memory
statistics/events, and zram statistics when available. It emits mode `0600`
JSONL with metadata and an explicit privacy contract. `scripts/run-studio.sh`
enables it only when `STUDIO_MEMORY_TRACE=1` or `STUDIO_MEMORY_TRACE=detailed`
is set for that invocation, uses a five-second default interval, and terminates
it after the launcher exits. It
removes the marker only after a sample sees the Rosemary executable in the
process tree, preserving the capture request through early startup failures.
The sampler tails the session log only to recognize fixed `PlaySoloManager`
start/stop events, then emits immediate boundary snapshots and 60/120-second
post-stop snapshots. Boundary snapshots aggregate `/proc/<pid>/smaps` by
mapping kind and private/shared status, retaining counters but no labels,
paths, addresses, or contents. A diagnostic launch requests
`MIMALLOC_SHOW_STATS=1` in both the host Rosemary environment and the
filtered Studio guest environment through `ROSEMARY_ENVIRON`, and enables
`ROSEMARY_TRACE_INTERPOSE=1` for that run. These may produce shutdown-only
aggregate allocator statistics and binding decisions, but they are not a
per-allocation profiler. Normal launches do not inherit either diagnostic
setting.

For a deeper bounded run, the ignored `logs/.memory-trace-detailed-once`
marker adds per-VMA addresses, permissions, labels/paths, sizes, RSS/PSS,
swap, and private/shared counters to the local mode-0600 trace. It also sets
`--detailed-vmas` for the sampler and `ROSEMARY_TRACE_VM=1` for Rosemary's
guest `mmap`/`mprotect` request logging. The summarizer stores only fixed
counts of those VM calls. This is mapping attribution, not allocation stack
attribution. The local environment has no `perf`, Heaptrack, BPF tracer, or
Valgrind available; `strace` would provide syscall events without allocator
stacks, so a later stack profiler may require a concrete privileged setup.
The normal reproduction must not use `--objc-debug`. The first bounded capture
showed anonymous mappings dominating the retained footprint, while file
mappings were negligible; it did not establish whether the bytes are live
allocations or allocator-retained pages.

For periodic Play-stutter diagnosis, `ROSEMARY_PERF_TRACE` is enabled by
default by the launcher and writes trace metadata with session logs. The
instrumentation covers main-loop gaps, script/event/backing pumps,
CoreFoundation callbacks, and AppKit/CoreVideo display-link schedule and
callback timing. It also records aggregate background rendering time, the
top slow background-rendered views, and per-view layer-presentation, fill, and
contents-copy timings. The latest trace isolated image-content copying as the
dominant cost. Exact-size BGRA content uses a clipped fast path: fully opaque
rows are copied, opaque pixels inside mixed rows are copied directly, exactly
transparent pixels are skipped, and partial-alpha pixels retain source-over
blending. Completely transparent rows are skipped as a unit. Scaled images and
RGBA surfaces retain the generic path. The user first confirmed that the
pixel-copy optimization made the same 0.5-second stutter much lighter, then
reported that the visible stutter disappeared after testing the latest build
in Play on an empty Baseplate. The latest run still logs full-window
invalidation about every 500 ms, so the optimization resolved the reported
visual symptom without eliminating the periodic damage event.

On Linux, AppKit `NSOpenPanel` and `NSSavePanel` first use the XDG Desktop
Portal FileChooser through `ashpd`/`zbus` when the panel options are
representable. Titles, prompts, initial folders, save names, extension filters,
and supported selection modes are mapped; local `file://` URIs are converted
back to host paths before guest translation. Cancellation is preserved.
The Qt filter-only accessory view is recognized when it contains exactly one
popup button and one label; its filter titles, globs, and current selection are
mapped to the portal. The shared `chrome::FilePicker` on the SDL window backend
remains the fallback for missing or failing portals, arbitrary accessories, and
unsupported options, and is used directly on other host platforms. No GTK or
`libportal` link dependency was added; fallback reasons are logged.
`Theme::panel_input_background` keeps dark-mode file names readable against the
chooser fields and list.

The chooser's shared implementation provides a visible case-insensitive live
filename filter, Ctrl/Command+F search focus, Ctrl/Command+H dotfile
visibility, and Ctrl/Command+R refresh. Home/End/PageUp/PageDown and arrow
navigation operate on the filtered view. File and package icons are drawn from
stable generic shapes and extension categories so the patch remains suitable
for Rosemary's cross-platform base without host-native icon dependencies.
AppKit stores the preference in `showsHiddenFiles`, and SDL modifier flags are
used for shortcut dispatch. Manual GUI verification of the installed build is
still pending.

`NSSavePanel` stores `canSelectHiddenExtension` as per-panel BOOL state,
defaulting to false. The selector is implemented in the AppKit panel bridge
because Qt Cocoa sends it while configuring Save to File.

Clipboard compatibility spans the SDL/AppKit pasteboard bridge, native AppKit
text responders, and the WebKit-backed script editor. System text is queried
even when SDL reports no clipboard text, while the bridge tracks the last
successfully observed or exported value so unavailable backends do not erase
local state. Confirmed empty external clipboards clear stale plain text and
HTML. Identical observations are idempotent and do not increment the
pasteboard change count or discard rich HTML. Carbon promised flavors are
represented distinctly from empty CFData, promise callbacks are materialized
without holding the board mutex, and promised text is eagerly converted to
SDL's UTF-8 clipboard representation; non-text promises resolve when
requested. Carbon ItemCount and PasteboardItemID output parameters use
UInt32/u32. Native copy and cut export plain text without stale rich formats;
native and WebKit text controls accept both Control and Command C/X/V/A
shortcuts. Clipboard trace logging, when enabled, records availability and
byte counts only, never clipboard contents.
The follow-up patch permits selection-only field editors for selectable
read-only NSTextField instances while rejecting paste, host text commits, and
IME composition in those editors. WebKit synchronizes the system clipboard
before exposing general text and HTML, and key-equivalent dispatch walks the
focused responder's ancestor views. Manual validation remains incomplete:
Toolbox and Explorer copy/cut work, while paste there and clipboard shortcuts
in other controls still fail.

For upstream review, these clipboard changes are isolated into two independent
one-commit Rosemary v0.2.3 branches. `citric/pasteboard-carbon-bridge` changes
only the Carbon/Cocoa pasteboard bridge; `citric/native-clipboard-actions` adds
native AppKit and WebKit editing actions independently, keeping the two
concerns independently reviewable. Both branches target current Rosemary main
and are pushed to the user's fork. Official PR #42 was
left open and untouched for the user to close manually before creating the two
replacement PRs.
