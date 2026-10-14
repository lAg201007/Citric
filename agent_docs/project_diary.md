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
