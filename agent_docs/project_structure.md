# Project structure

Explorer/input compatibility is owned by the AppKit table, pasteboard, drag
and event modules in the Rosemary overlay. `patches/0008-rosemary-v0.3.0-overlay.patch`
is the authoritative source representation; `bin/rosemary` is only an
installed artifact and currently reflects the older 0.2.3 build. Future work
should inspect the v0.3.0 temporary build checkout rather than treating the
old installed binary or historical source snapshots as the final interface.

- crates/appkit: NSView, window, event, input, display-link, controls, font,
  file-panel, and AppKit diagnostic behavior.
- crates/appkit/src/controls.rs: AppKit control drawing and
  `NSButtonCell` bezel-only frame dispatch, with Objective-C registration and
  rendering regression coverage.
- crates/appkit/src/event.rs: key event normalization for text clients,
  Linux Control-to-Command shortcut mapping, and regression coverage for
  printable text, editing keys, modifiers, and shortcuts.
- crates/appkit/src/backing.rs: Core Graphics-backed `NSGraphicsContext`
  creation, flipped-state behavior, lifetime management, and regression tests.
- crates/appkit/src/pasteboard.rs: SDL system-clipboard synchronization,
  plain/rich text ownership, and external clipboard state tracking.
- crates/appkit/src/pasteboard_manager.rs: Carbon pasteboard ABI, promised
  flavor registration and resolution, PromiseKeeper callbacks, and item
  identifier/count compatibility.
- crates/appkit/src/text.rs: native AppKit text selection, copy/cut actions,
  and Control/Command editing shortcuts.
- crates/webkit/src/web_view.rs: WebKit editor clipboard and keyboard shortcut
  forwarding for Control and Command modifiers.
- crates/chrome/src/file_picker.rs: shared SDL-rendered Import/Open/Save
  chooser, visible search and hidden-file filtering, SDL shortcut handling,
  filtered keyboard navigation, generic file-type icons, and rendering tests.
- crates/appkit/src/panel/portal.rs: Linux XDG Desktop Portal FileChooser
  requests, panel option mapping including Qt's filter accessory, local URI
  conversion, cancellation, fallback eligibility, and diagnostic logging.
- crates/corefoundation: collection singletons, run-loop and timer lifetime.
- crates/foundation/src/runtime.rs: NSObject instance/class description and
  debugDescription compatibility, including autorelease and override tests.
- crates/objc: Objective-C messaging and autorelease-pool safety.
- crates/metal_translate: Metal/SPIR-V translation support.
- scripts/run-studio.sh: local launcher and diagnostic log wrapper.
- scripts/trace-studio-memory.py: one-shot privacy-conscious `/proc` memory,
  swap, process, pressure, cgroup, zram, Play boundary, and aggregate
  mapping sampler. It never persists Studio log lines or mapping labels.
- scripts/citric: GTK launcher entry point and CLI wrapper.
- citric_launcher/: GTK 4 UI, configuration, desktop-entry integration, and
  launch diagnostics.
- citric_launcher/studio_bundle.py: pinned and latest Studio archive
  downloader, checksum/app validation, safe ZIP extraction, atomic
  installation, and published-version checking.
- citric_launcher/app.py and citric_launcher/core.py: asynchronous Studio
  update availability check, update button label, and guarded replacement
  behavior for the selected release.
- scripts/build-studio.sh: fetches the pinned Rosemary base, applies the patch
  series in a temporary checkout, and performs a locked release build.
- scripts/patch-color-dialog.py: idempotent Qt Cocoa QColorDialog patching.
- scripts/patch_plugin_compatibility.py: reversible, signature-based RBXM
  compatibility rules scanned across installed plugin IDs and versions.
- app/full/RobloxStudio.app: ignored local Studio bundle.
- app/full/.citric-studio-*/: ignored temporary download/extraction staging.
- bin/rosemary: ignored ready-to-run Rosemary binary.
- downloads/darwin-cache: ignored local runtime cache.
- docs/: migration, compatibility, crash, bundle, patch, and validation notes.
- docs/nsobject-description.md: isolated upstream preparation and validation
  record for NSObject textual descriptions.
- patches/: pinned Rosemary v0.3.0 base commit, canonical reconciled overlay,
  historical v0.2.x snapshots, and diagnostic patches retained for provenance.
- tests/test_citric_launcher.py: launcher configuration, argument, and desktop
  entry tests.
- tests/test_run_studio_locale.py: numeric-locale launch contract test.
- docs/numeric-locale.md: decimal-literal diagnosis and validation notes.
- docs/plugin-overrides.md: plugin override contract, backup, and restore notes.
- tests/test_plugin_compatibility.py: generic RBXM plugin compatibility tests.
- agent_docs/: durable deployment state for future agent handoffs.

The patch series is the owner of Citric's Rust behavior; the temporary
Rosemary checkout owns upstream source during a build. The scripts own local
launch composition. docs/ owns the user-facing record; agent_docs/ owns the
workflow handoff state.

The periodic-stutter diagnostic path is owned by `scripts/run-studio.sh` and
runtime hooks in the patch. Its output is session metadata and raw logs outside
Git; no standalone diagnostic module was introduced.

The memory-leak investigation is owned by `scripts/run-studio.sh` and
`scripts/trace-studio-memory.py`. Diagnostics are disabled for normal launches
and enabled only by `STUDIO_MEMORY_TRACE=1` or `STUDIO_MEMORY_TRACE=detailed`.
The launcher writes the per-session JSONL trace beside
the normal log, and stops the sampler when the Studio process tree exits. The
tracer recognizes fixed PlaySoloManager boundaries and schedules 60/120-second
post-stop snapshots. The trace is intentionally outside Git and contains no
command lines, environment values, file paths, mapping labels, or memory
contents. The launcher requests mimalloc shutdown statistics only while the
one-shot marker is active. Mapping summaries include fixed region-size buckets
and are emitted at Play boundaries and periodic 30-second samples. The
`scripts/summarize-memory-diagnostics.py` helper recognizes fixed mimalloc
footer rows without retaining raw log text.

The detailed one-shot mode consumes the ignored
`logs/.memory-trace-detailed-once` marker. It adds per-VMA identity, addresses,
permissions, labels/paths, sizes, RSS/PSS/swap, and private/shared counters to
the local trace, and enables Rosemary VM request tracing. The summarizer
reduces `mmap`/`mprotect` output to fixed counts; raw VM request lines remain
local and are not documentation artifacts.

The latest ignored capture is `logs/run-20261015T010138-120845.memory.jsonl`.
It is evidence only and remains outside Git; its missing end record and absent
exit-code sidecar leave clean process shutdown uncertain.

The clipboard compatibility change is owned by the AppKit pasteboard/text
modules and the WebKit view bridge. The canonical patch remains the source of
truth; `bin/rosemary` is an ignored installed build artifact.
The follow-up clipboard layer also owns read-only NSTextField selection-only
field-editor behavior in `crates/appkit/src/text.rs`, WebKit pre-read clipboard
synchronization in `crates/webkit/src/web_view.rs`, and focused-responder
ancestor traversal for key equivalents. Diagnostics are environment-gated in
the existing AppKit and WebKit input paths.

The upstream-ready clipboard branches live in the separate Rosemary checkout:
`citric/pasteboard-carbon-bridge` owns the Carbon/Cocoa bridge, and
`citric/native-clipboard-actions` owns native AppKit and WebKit text actions
independently. They are pushed to the user's fork and are not part of Citric's
current branch history. PR #42 remains open and untouched; the user
will close it and open replacement PRs manually.

The Save panel hidden-extension preference is owned by the AppKit panel bridge
in the canonical patch; its getter and setter are covered by panel tests.

Linux shortcut mapping is owned by `crates/appkit/src/event.rs` and the menu
configuration in `crates/appkit/src/decor.rs`. The event boundary maps Control
to Command for non-modifier chords while preserving AltGr and exposing the
`ROSEMARY_MENU_CTRL` opt-out; focused event tests define the contract.

Foundation's composed-character compatibility is implemented in the string
module and documented in `docs/nsstring-composed-characters.md`; its patch is
kept separate for future upstream review.

- patches/0007-native-mouse-message-diagnostics.patch: opt-in Objective-C
  selector dispatch telemetry used by the native Qt mouse investigation.

- scripts/trace-studio-cursor.sh: narrow opt-in cursor-delivery capture for Qt
  categories and cursor selector dispatch.
