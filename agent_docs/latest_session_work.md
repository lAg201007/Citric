# Latest session work

Deployment: citric-generic-plugin-bit32-20261012

State: complete for the generic plugin compatibility change. The user
confirmed that the Baseplate which previously failed opens after the original
plugin fix. A separate Play attempt emitted `Malformed number` for valid
decimal literals in Roblox's bundled PlayerModule, plugins, and place scripts.
That locale issue remains separate and unconfirmed.

Material changes: `scripts/run-studio.sh` now removes inherited `LC_ALL` and
sets `LC_NUMERIC=C` for Studio. It records source and effective locale values
in session metadata. `tests/test_run_studio_locale.py` verifies the contract
under `pt_BR.UTF-8`, and `docs/numeric-locale.md` documents the diagnosis and
required manual check.

Verification: the locale regression test and shell syntax check passed during
its deployment; no fresh Play session was run after the locale change. The
token report is unavailable because no matching session record was found.

Separate pending check: restart Studio through `scripts/run-studio.sh`, open
the affected place, and try Play. Inspect new `.log` and `.meta` files. If
`Malformed number` remains, investigate the runtime's `strtod` locale path.
Complex mouse tests remain user-driven and are unrelated to this check.

The user asked to replace the plugin-specific override with a general rule.
The initial crash evidence remains specific: `BlenderAnimationsInternal`
loaded immediately before a fatal bare-`bit` require, and its model contains
`requireany("bit", "bit32", "bit.numberlua", nil)`.

The launcher now uses `scripts/patch_plugin_compatibility.py`, which scans all
`InstalledPlugins/<plugin-id>/<version>/Plugin.rbxm` models in the Rosemary
prefix, independent of plugin ID. It patches only the exact legacy source
signature, preserves unrelated RBXM chunks, and creates a verified
content-addressed backup. Unknown or ambiguous models and unrelated `require`
patterns remain unchanged. The launcher, locale test, generic plugin tests,
project notes, and user-facing plugin documentation use the generic helper.

Verification completed: all 17 Citric tests pass, `bash -n scripts/run-studio.sh`
and `git diff --check` pass. The live prefix scan reported 18 models scanned,
0 newly patched, 1 already patched, 17 unchanged, and 0 unsupported. The user
confirmed the formerly failing Baseplate opens with the plugin enabled.

Exact continuation point: none for this deployment. Camera behavior and the
separate numeric-locale Play validation remain open. Do not broaden the rule
to arbitrary `require` names without evidence and a safe compatibility mapping.

Token report: `unavailable`; no matching session record was available for
`citric-generic-plugin-bit32-20261012`.

Historical deployment record: the Citric branch snapshot is patch-only: Rosemary source was
removed from the current tree, while `patches/base-commit`, `patches/series`,
and `patches/upstream-url` define the reproducible overlay. The original
Rosemary ancestry was removed from the branch history while the four Citric
commits were preserved. The first preserved Citric commit records the initial
workspace snapshot; the current tree contains no Rosemary source. GitHub still
treats Citric as an independent repository.

The GTK 4 launcher was added under `citric_launcher/` with `scripts/citric`,
XDG configuration, place selection, diagnostics, and desktop-menu integration.
The launcher delegates to `scripts/run-studio.sh`; it does not package or
download the proprietary Studio bundle.

Material changes include removal of the Rosemary source from the current
snapshot, the canonical patch overlay build path, GTK launcher sources and
tests, and updated migration documentation. The copied app is Studio
0.742.0.7421053; hashes are in docs/bundle.md and the manifest.

Verification evidence: `scripts/build-studio.sh --check-only`, a full offline
`--build-only` in a dedicated cache using the pinned commit, six launcher tests,
shell syntax checks, and `git diff --check` passed. The validation cache was
removed; the ignored bundle, binary, downloads cache, prefix, and logs were
preserved. The GTK GUI smoke test could not be fully validated in the available
display session. Manual Studio work ended with an unresolved crash opening the
large place and unresolved camera/docking edge cases.

Exact continuation point: run scripts/run-studio.sh with a fresh STUDIO_LOG_NAME
and reproduce the place-opening crash normally. Preserve the raw log outside
Git, then isolate the require path failure before changing camera behavior.

Token report: `unavailable`; no matching session record was available for this
deployment.
