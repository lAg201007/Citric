# Project overview

Citric is the local continuation of the Rosemary compatibility work for running
the macOS Roblox Studio client on Linux. Its current branch stores the
compatibility patches, launcher, scripts, and diagnostic record; Rosemary source
is materialized only in a temporary build checkout.

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
<version>`. Selecting it never silently replaces Studio: the validated
0.742.0.7421053 archive remains the only installable build, and a newer
unvalidated release is reported while the current bundle stays intact.

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

The AppKit file-panel compatibility layer now uses Rosemary's shared SDL-backed
`chrome` file chooser for Import and Open from File. The latest manual retest
reached the chooser and navigated with Up; readable entries, selection, and
cancellation still need confirmation after the theme contrast fix.

The shared file chooser now includes a case-insensitive live name search,
hidden dotfile visibility toggled with Ctrl/Command+H, refresh with
Ctrl/Command+R, filtered keyboard navigation, and generic canvas-drawn icons
for common file types. The AppKit panel preserves the hidden-file preference
through `showsHiddenFiles` while the reusable chooser remains independent of
desktop-specific icon APIs.

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
