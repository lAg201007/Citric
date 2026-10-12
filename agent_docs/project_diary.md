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
  The chosen remedy is a launcher-managed compatibility patch that changes
  only the exact known declaration, preserves the original RBXM by hash, and
  skips unknown plugin versions. Disabling installed plugins was rejected as
  the product fix because the plugins must remain usable.
