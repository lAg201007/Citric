# Latest session work

Deployment: citric-plugin-bit32-20261012

State: paused with implementation prepared and live validation pending. A Play attempt in a new place
kept Studio open but emitted `Malformed number` for valid decimal literals in
Roblox's bundled PlayerModule, several plugins, and place scripts. The same
session accepted integer literals and string-based numeric conversion. This is
recorded as a launcher/runtime locale issue, with the exact parser path still
requiring confirmation.

Material changes: `scripts/run-studio.sh` now removes inherited `LC_ALL` and
sets `LC_NUMERIC=C` for Studio. It records source and effective locale values
in session metadata. `tests/test_run_studio_locale.py` verifies the contract
under `pt_BR.UTF-8`, and `docs/numeric-locale.md` documents the diagnosis and
required manual check.

Verification: the regression test and shell syntax check were run during the
deployment; no fresh Play session was run after the locale change. The token
report is unavailable because no matching session record was found.

Exact continuation point: restart Studio through `scripts/run-studio.sh`, open
the affected place, and try Play. Inspect the new `.log` and `.meta` files. If
`Malformed number` remains, investigate the runtime's `strtod` locale path.
Complex mouse tests remain user-driven and are unrelated to this check.

Current deployment state: the crash investigation found plugin `16708835782`
(`BlenderAnimationsInternal`) requesting `requireany("bit", "bit32", ...)`.
The installed plugin logged immediately before the fatal `require "bit"`
message, so this is a high-confidence compatibility cause, although it is not
yet a proven exclusive cause.

Material changes prepared in the worktree: `scripts/patch_blender_animations.py`
performs an idempotent, exact-signature RBXM rewrite with LZ4 chunk handling,
hash-named backup, atomic replacement, and safe skips for unknown versions.
`scripts/run-studio.sh` invokes it before and after Studio; the launcher README,
plugin notes, and focused tests document the behavior.

Verification completed: staged unit tests passed (five total including the
locale test), the helper compiled, shell syntax passed, and a disposable copy
of the real plugin artifact was patched and then reported idempotent. The live
prefix was not changed, the full Citric test suite was not rerun after the
latest additions, and Studio was not relaunched after the override.

Exact continuation point: run the full test suite and inspect the diff, then
run the launcher once so it applies the backup-preserving override to the live
prefix. Open an empty Baseplate and the affected place, record whether Studio
stays open, and retain the generated `.log`, `.meta`, and exit-code files
outside Git. Do not disable the plugin as the fix.

Token report: `unavailable`; no matching session record was available for
`citric-plugin-bit32-20261012`.

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
