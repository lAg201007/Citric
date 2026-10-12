# Project structure

- crates/appkit: NSView, window, event, input, display-link, controls, font,
  and AppKit diagnostic behavior.
- crates/corefoundation: collection singletons, run-loop and timer lifetime.
- crates/objc: Objective-C messaging and autorelease-pool safety.
- crates/metal_translate: Metal/SPIR-V translation support.
- scripts/run-studio.sh: local launcher and diagnostic log wrapper.
- scripts/citric: GTK launcher entry point and CLI wrapper.
- citric_launcher/: GTK 4 UI, configuration, desktop-entry integration, and
  launch diagnostics.
- scripts/build-studio.sh: fetches the pinned Rosemary base, applies the patch
  series in a temporary checkout, and performs a locked release build.
- scripts/patch-color-dialog.py: idempotent Qt Cocoa QColorDialog patching.
- scripts/patch_plugin_compatibility.py: reversible, signature-based RBXM
  compatibility rules scanned across installed plugin IDs and versions.
- app/full/RobloxStudio.app: ignored local Studio bundle.
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
