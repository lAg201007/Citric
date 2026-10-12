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
not download or modify the proprietary Studio bundle.

The launcher clears inherited `LC_ALL` and forces `LC_NUMERIC=C` for Studio.
Launch metadata records both the incoming and effective numeric locale values
so decimal-literal failures can be diagnosed.

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
