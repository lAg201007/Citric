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

---

Deployment: citric-play-periodic-stutter-20261012

State: the user-visible stutter is resolved in the latest tested build. On
2026-10-12, the user restarted through Citric, ran an empty Baseplate in Play
for about 10 seconds, and reported that the stutter disappeared.

The user confirmed the stutter persists with per-view profiling. The trace
measured 110.71 ms median slow window composition every 499.69 ms, with
109.78 ms in `compose_render_background_total`. Across 3,658 slow view records,
`contents_ms` had a 7.16 ms median and 25,773.7 ms cumulative time; presentation
and fill were negligible. Every slow view had contents and no background.

The first optimization uses clipped row copies for exact-size, opaque BGRA
contents. The user retested and confirmed the stutter remained. In the next
trace, all 95 slow-view records selected `exact_copy`; images had matching
source and placed dimensions, no channel swap, and full layer opacity. However,
82 records had only one fully opaque row. Mixed rows still ran the four-channel
blend for every pixel, including fully opaque pixels, and did not skip fully
transparent zero pixels. The current implementation copies opaque pixels
directly, leaves exactly transparent pixels unchanged, and source-over blends
only remaining pixels. It records opaque rows/pixels and transparent/blended
pixel counts. Scaled images and RGBA surfaces remain on the generic path.

The user tested that build and reported the same 0.5-second stutter, but much
lighter. Its trace measured 28.73 ms median composition, 64.08 ms at p95, and
499.91 ms median between compositions across 712 samples. The remaining
composition still redraws the full 1920x1052 window. The current build adds a
transparent-row skip and propagates `#[track_caller]` through Core Animation
damage. The latest run log still records full-window damage for a 1920x1052
region at a median interval of about 499.9 ms, while the visible stutter
disappeared in the user's retest. Treat the visible symptom as resolved; the
remaining periodic invalidation is a separate diagnostic detail and does not
currently block use.

Verification: the canonical patch applies to the pinned base; `cargo fmt
--all -- --check`, source `git diff --check`, all 11 focused Core Animation
tests, and the Release build/install pass. The full AppKit suite previously
passed 281/283 tests; the same two named-color assertions expected black
`textColor` but received white, an unrelated issue. The installed binary
SHA-256 is `1c81b0f81f3483c4eb6ccbfe15437f5634b275fc574e380d4f7b7e0f710a2513`;
ELF build ID is `df984a5c36cf72f68b3704b10ee7c8b5a5ad7cb0`.

Exact continuation point: no further stutter retest is needed unless the user
reports it returning. If it does, inspect transparent-row counts and the
damage setter call sites in a fresh trace. Keep raw logs outside Git.

Token report: `citric-play-periodic-stutter-20261012` is unavailable; no
matching session record was found.

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

---

Deployment: citric_dark_picker_20261013

State: code and automated verification complete; manual visual validation is
pending.

Outcome: the Import/Open chooser no longer crashed after Rosemary implemented
the missing AppKit and Foundation compatibility calls. The user confirmed that
the chooser opens and that Up navigates. The entries then appeared white with
invisible names in dark appearance. The patch changed the chooser's list,
location, and save-name surfaces to use the theme-specific input background.

Verification: 52 chrome tests, 295 AppKit tests plus the theme integration test,
package-scoped formatting, source diff checks, locked offline Release build,
clean pinned-base patch application, and the focused dark-mode rendering test
passed. The updated binary is installed. The latest evidence is
`logs/run-20261013T213755-38660.log`; raw logs remain outside Git.

Pending: restart through Citric and verify readable names, selecting a file,
and cancelling in Import and Open from File. Arbitrary accessory-view rendering
remains unverified. Continue from `docs/current-state.md` and the file chooser
sections in `docs/validation.md`.

Token report for `citric_dark_picker_20261013`:

Deployment token report: `citric_dark_picker_20261013` (unavailable)

| Agent | Rollouts | Input tokens | Cached input | Output tokens | Total tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| _none recorded_ | 0 | 0 | 0 | 0 | 0 |

Warning: no session record matched this deployment ID.

Token report: `unavailable`; no matching session record was available for this
deployment.
