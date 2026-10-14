# Project core technology

Rosemary is a Rust 2024 workspace that loads macOS Mach-O applications through
native or Microlift-backed execution and supplies Darwin, Objective-C,
CoreFoundation, AppKit, Metal, and SDL compatibility layers.

Citric targets the Linux execution path. scripts/run-studio.sh selects the
local release binary, validates and patches the Studio app when required, uses
the local Darwin cache, and defaults SDL to X11/XWayland because that avoided a
reappearing non-modal plugin-loading window during the recorded tests.

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
fetches a pinned Roblox CDN ZIP, checks its SHA-256, validates the bundle
identifier/version/executable and Intel Mach-O slice, and installs it under the
ignored `app/full/RobloxStudio.app` path with a replacement confirmation.

`citric_launcher/studio_bundle.py --check-update` queries
`clientsettings.roblox.com/v2/client-version/MacStudio`, validates the returned
version and build identifier, and compares numeric version components. The GTK
launcher runs this check asynchronously and updates its button label when a
newer release exists. The check is advisory because the downloader has a
recorded checksum and compatibility validation only for the pinned build;
unknown releases are never installed automatically.

The launcher clears inherited `LC_ALL` and forces `LC_NUMERIC=C` for Studio.
Launch metadata records both the incoming and effective numeric locale values
so decimal-literal failures can be diagnosed.

In `crates/appkit/src/event.rs`, printable key-down characters are removed from
the event delivered to an active text input client when SDL will also deliver a
layout-resolved text commit. The original characters remain available to key
equivalent processing; controls, shortcuts, key-up events, and non-text
responders retain their existing behavior.

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

AppKit `NSOpenPanel` and `NSSavePanel` use the shared `chrome::FilePicker` on
the SDL window backend. It handles navigation, filtering, selection, save-name
entry, and guest/host path conversion without depending on a desktop portal.
`Theme::panel_input_background` keeps dark-mode file names readable against the
chooser fields and list.

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
