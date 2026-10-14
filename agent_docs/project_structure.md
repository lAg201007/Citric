# Project structure

- crates/appkit: NSView, window, event, input, display-link, controls, font,
  file-panel, and AppKit diagnostic behavior.
- crates/appkit/src/event.rs: key event normalization for text clients and
  regression coverage for printable text, editing keys, and shortcuts.
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
  chooser and navigation, filtering, and rendering tests.
- crates/corefoundation: collection singletons, run-loop and timer lifetime.
- crates/objc: Objective-C messaging and autorelease-pool safety.
- crates/metal_translate: Metal/SPIR-V translation support.
- scripts/run-studio.sh: local launcher and diagnostic log wrapper.
- scripts/citric: GTK launcher entry point and CLI wrapper.
- citric_launcher/: GTK 4 UI, configuration, desktop-entry integration, and
  launch diagnostics.
- citric_launcher/studio_bundle.py: pinned Studio archive downloader,
  checksum/app validation, safe ZIP extraction, atomic installation, and the
  bounded published-version check.
- citric_launcher/app.py and citric_launcher/core.py: asynchronous Studio
  update availability check, update button label, and guarded pinned-installer
  behavior.
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
- patches/: pinned base commit, canonical Citric runtime patch, and historical
  snapshots.
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

The clipboard compatibility change is owned by the AppKit pasteboard/text
modules and the WebKit view bridge. The canonical patch remains the source of
truth; `bin/rosemary` is an ignored installed build artifact.
The follow-up clipboard layer also owns read-only NSTextField selection-only
field-editor behavior in `crates/appkit/src/text.rs`, WebKit pre-read clipboard
synchronization in `crates/webkit/src/web_view.rs`, and focused-responder
ancestor traversal for key equivalents. Diagnostics are environment-gated in
the existing AppKit and WebKit input paths.
