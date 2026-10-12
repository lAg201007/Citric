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
- scripts/build-studio.sh: locked release build for Rosemary.
- scripts/patch-color-dialog.py: idempotent Qt Cocoa QColorDialog patching.
- app/full/RobloxStudio.app: ignored local Studio bundle.
- bin/rosemary: ignored ready-to-run Rosemary binary.
- downloads/darwin-cache: ignored local runtime cache.
- docs/: migration, compatibility, crash, bundle, patch, and validation notes.
- patches/: pinned base commit, canonical Citric runtime patch, and historical
  snapshots.
- tests/test_citric_launcher.py: launcher configuration, argument, and desktop
  entry tests.
- agent_docs/: durable deployment state for future agent handoffs.

The source repository is the owner of Rust behavior. The scripts own local
launch composition. docs/ owns the user-facing record; agent_docs/ owns the
workflow handoff state.
