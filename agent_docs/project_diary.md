# Project diary

- The destination was made as a local clone of Rosemary source at base commit
  c14275b, then the complete working diff was applied. CaseSolved content was
  deliberately excluded.
- The Studio app, ready binary, and Darwin cache were copied for continuity but
  kept out of Git to avoid publishing proprietary or account-related data.
- X11/XWayland became the launcher default after Wayland reproduced the plugin
  loading window. This is a runtime workaround, not proof of a full modal
  lifecycle fix.
- The View Selector was repaired rather than disabled: an invisible overlay had
  consumed a broad top viewport strip. The user later confirmed Edit and Play
  clicks worked.
- Docking was left pending after repeated crashes and unreliable guides because
  the user prioritized general stability.
- Camera scaling was reduced repeatedly, ultimately to 0.003 for captured/right
  drag input, but manual validation still found excessive speed and abrupt
  rotations. This remains an investigation item.
- After comparing the Vinegar and Kombucha layout, Citric was converted to a
  patch-only branch snapshot. `scripts/build-studio.sh` fetches the pinned
  upstream commit, applies the canonical series in a temporary directory, and
  builds without copying Rosemary source into the checkout. The old source
  remains recoverable in Git history.
- A GTK 4 launcher was added around `scripts/run-studio.sh`, with XDG
  configuration, place selection, diagnostics, and an optional application-menu
  entry. The launcher was verified through its CLI and non-Studio checks; a
  full GUI smoke test is limited by the available display session.

- The patch-overlay migration was validated with `--check-only`, a full
  offline `--build-only` in a dedicated cache, launcher tests, shell syntax,
  and `git diff --check`. The temporary validation cache was removed and local
  runtime assets were preserved.
- The branch history was then trimmed to the four Citric commits. The old
  Rosemary ancestry is no longer reachable from `main`, while the preserved
  first Citric commit remains the historical workspace snapshot and the current
  branch tree remains patch-only.

Reusable lesson: keep raw account-bearing logs outside the repository and use
the normal launcher for crash reproduction; direct GDB startup produced a
different early selector failure.

- A new Play session on 2026-10-12 produced `Malformed number` for valid
  decimal literals in bundled PlayerModule code, plugins, and place scripts.
  Integer literals and string conversion worked, implicating the active
  numeric locale rather than the new place's code.
- The launcher now removes inherited `LC_ALL`, sets `LC_NUMERIC=C`, and records
  source and effective locale values. A regression test covers an inherited
  `pt_BR.UTF-8` environment. Manual Play confirmation remains pending.
- A later place-opening crash matched plugin `16708835782` loading
  `BlenderAnimationsInternal` immediately before a fatal bare-`bit` require.
  This plugin was the trigger, not the rule's scope: the launcher scans every
  installed plugin ID for the exact legacy `requireany("bit", "bit32", ...)`
  declaration and changes only that signature. It preserves the original RBXM
  by hash and leaves unknown module imports untouched. The user confirmed the
  formerly failing Baseplate opens with the plugin enabled.

- On 2026-10-12 the user reported a periodic Play stutter at approximately
  0.5-second intervals and confirmed the same behavior in an empty Baseplate,
  which makes place scripts an insufficient explanation. A source audit found
  no fixed 500 ms timer in AppKit, CoreFoundation, or SDL. The launcher now
  enables `ROSEMARY_PERF_TRACE` and records main-loop, script/event/backing
  pump, CoreFoundation callback, and AppKit/CoreVideo display-link timing so a
  fresh reproduction can identify the stalled layer. This is diagnostic work;
  no behavior fix has been established yet.
- The follow-up per-view trace isolated image-content copying: the aggregate
  operation consumed about 110 ms of each 500 ms composition, with a 7.16 ms
  median per view. The fast path is restricted to exact-size, opaque BGRA
  contents; transparency, scaling, and RGBA keep the existing behavior. The
  release build is installed and awaits a manual Baseplate retest.
- The user tested the fast-path telemetry build and reported the stutter
  remains. All 95 slow-view records selected the exact-size BGRA path, while
  82 images had only one fully opaque row. This showed that mixed rows still
  blended opaque pixels and visited fully transparent zeros. The follow-up
  optimization copies opaque pixels, skips exactly transparent pixels, and
  blends only remaining pixels. The user reported the cadence remains but the
  stutter is much lighter; the measured median composition fell to 28.73 ms.
  The latest build also skips completely transparent rows and keeps the
  original Core Animation setter call site when reporting window damage.
- The user restarted that latest build through Citric and ran an empty
  Baseplate in Play for about 10 seconds. On 2026-10-12 they reported that the
  visible stutter disappeared. The latest run log still records full-window
  damage at roughly 500 ms intervals, so only the visual symptom is confirmed
  resolved; the recurring invalidation remains observable but is not blocking.

- On 2026-10-13, Import and Open from File progressed through missing AppKit
  and Foundation compatibility selectors. The final crash was
  `NSWorkspace -isFilePackageAtPath:`; the implementation now translates guest
  paths and reuses the chooser's package classifier.
- The next retest stopped crashing and confirmed that Up navigated. Dark mode
  used white list and field surfaces with white text, making entries appear
  blank. The theme-aware surface fix and regression test are installed. The user
  confirmed readable Import names, file selection returning without a crash, and
  cancellation working. Open from File remains unverified separately.

- On 2026-10-13, Studio Toolbox and Explorer search duplicated printable
  characters because the same key reached AppKit `keyDown:` and SDL
  `TEXT_INPUT`. The patch keeps the latter as the insertion path for active
  text clients and sanitizes only printable key-down characters in the former.
  Backspace, shortcuts, key equivalents, and IME/layout resolution remain
  intact. The focused regression passed and the user confirmed both fields now
  insert one character per key.

- On 2026-10-13, clipboard diagnosis separated write and read failures. Text
  copied from Toolbox and Explorer reached external Linux applications, while
  text copied externally could not be pasted back into Studio fields. The
  availability gate around SDL clipboard reads was unreliable for this runtime.
  The bridge now queries the text value regardless of that flag, tracks the
  last observed/exported system value, preserves local state when the backend
  is unavailable, and clears stale plain/rich data only on a confirmed external
  empty clipboard. Native AppKit and WebKit editors also gained Control-key
  clipboard shortcuts, and plain copy/cut no longer leaves stale HTML. Release
  build and focused pasteboard/text tests passed; manual UI retest is pending.

- On 2026-10-13, the clipboard follow-up added selection-only field editors
  for selectable read-only NSTextField controls, rejected paste and host/IME
  commits in those fields, synchronized SDL clipboard state before WebKit
  reads it, and searched focused responder ancestors for key equivalents.
  Privacy-safe clipboard and input traces were added. Automated validation
  passed, but the latest manual evidence leaves paste and other controls
  unresolved.

- On 2026-10-13 the launcher gained a managed Studio download action. The
  implementation pins the known compatible x86_64 archive and checksum rather
  than silently following an update channel, validates the app before install,
  stages extraction under an ignored temporary directory, and asks before
  replacing a different existing bundle. The archive download could not be
  exercised because this environment had no DNS resolution; retain the pending
  manual check and refresh the bundle manifest if a different local build is
  installed.

- On 2026-10-13 the launcher gained a bounded Studio update notice. It checks
  Roblox's MacStudio version endpoint at startup and labels the action
  `UPDATE STUDIO NEW VERSION <version>` when the published version is newer
  than the selected bundle. Automatic replacement was deliberately rejected:
  only 0.742.0.7421053 has a recorded checksum and compatibility validation,
  so a newer release is displayed but the current bundle remains untouched.
  The endpoint and GUI were not exercised in this environment; manual
  validation with network access remains the next step.

- On 2026-10-13, the clipboard follow-up exposed a Carbon promise boundary:
  Qt registered promised flavors, while the bridge stored them as empty data
  and never invoked the provider. The fix keeps promised data distinct from
  genuine empty data, invokes PromiseKeeper callbacks, resolves text eagerly
  for SDL's eager clipboard API, resolves other formats on demand, removes
  stale external flavors, avoids local-write resync, and corrects Carbon
  item-count/item-ID output widths to UInt32. The release build and 15 focused
  pasteboard tests passed. Manual validation still reports failures across
  cut, search-to-other-control paste, and Linux application boundaries. The
  durable lesson is to implement the promise contract rather than treating
  NULL promised data as an empty string.

- On 2026-10-13, the shared Rosemary file chooser was extended from basic
  navigation and selection with a case-insensitive live name filter, a
  Ctrl/Command+H dotfile toggle, refresh and search shortcuts, filtered
  keyboard navigation, and generic canvas-drawn icons. Wine's native chooser
  was used as inspiration for filter controls and navigation; Ctrl/Command+H
  is a Rosemary addition rather than a behavior attributed to Wine. The
  implementation stays in the shared `chrome` chooser and AppKit preference
  bridge so it can be proposed upstream without desktop-specific APIs.

- On 2026-10-14, the first file-picker QoL report could not be reproduced from
  the installed binary: the earlier response described changes that were not
  present in that binary, and its key handler ignored modifiers. The canonical
  patch was then updated and rebuilt. The chooser now visibly paints the search
  and hidden-file controls, maps SDL Ctrl/Command modifiers for Ctrl/Command+
  F/H/R, preserves `showsHiddenFiles`, and tests filesystem dotfile
  enumeration and filtered navigation. The lesson is to verify the installed
  binary and visible strings after patch generation, not only the patch source.
  Manual Studio retesting after restarting Citric remains open.

- On 2026-10-14, Save to File reached Qt Cocoa's next panel configuration
  selector and aborted on `setCanSelectHiddenExtension:`. The AppKit panel now
  stores this BOOL preference with a false default and exposes its getter and
  setter. Ten focused panel tests, a clean pinned-base patch application, and
  the Release build passed. No Studio session was launched, so Save to File
  confirmation remains user-driven.

- On 2026-10-14, Linux shortcut compatibility was generalized from clipboard
  editing chords to all non-modifier key events: Control is offered as a
  Command alias before AppKit dispatch, while Shift and left Alt remain
  available and right Alt/AltGr is preserved for alternate characters. The
  `ROSEMARY_MENU_CTRL=0` opt-out keeps host Control semantics. Thirteen focused
  event tests and a clean pinned-base application passed; Studio validation is
  still user-driven. The reusable lesson is to map the modifier at the event
  boundary rather than maintain a per-command list.

- On 2026-10-14, Linux AppKit file panels gained an XDG Desktop Portal
  integration. The implementation maps expressible Open and Save options with
  `ashpd`/`zbus`, converts only local `file://` URIs, and treats cancellation
  separately from portal failure. Missing services, errors, and unsupported
  panel options use the existing shared SDL/Chrome chooser. This keeps the
  patch free of GTK/libportal linkage and preserves the upstreamable fallback
  path. Automated tests and the Release build passed, but no session D-Bus or
  Studio GUI was available; portal appearance and fallback behavior still need
  manual validation.

- On 2026-10-14, the user reported that Open from File still opened the SDL
  chooser. Inspection of the bundled Qt Cocoa plugin showed that Qt attaches a
  filter popup and label as an accessory view when multiple name filters are
  configured. The portal eligibility check previously rejected every accessory
  view, so it selected the fallback. The patch now recognizes exactly that
  filter-only shape, maps filter titles/globs and the current selection to XDG
  filters, and retains fallback with diagnostic reasons for arbitrary or
  unsupported accessories. Automated tests and the v0.2.3 build passed; the
  user still needs to restart Studio and test Open from File with a working
  session portal.
