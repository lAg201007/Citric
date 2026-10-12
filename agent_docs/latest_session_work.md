# Latest session work

Deployment: citric-history-trim-20261012

State: complete. The Citric branch snapshot is patch-only: Rosemary source was
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
