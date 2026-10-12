# Latest session work

Deployment: citric-launcher-20261012

State: complete. The Citric checkout preserves the full Rosemary source tree,
adds the canonical runtime patch series, and has local `upstream` configured as
`https://github.com/microlift/rosemary.git`. GitHub still treats Citric as an
independent repository; the local upstream remote is the update path.

The GTK 4 launcher was added under `citric_launcher/` with `scripts/citric`,
XDG configuration, place selection, diagnostics, and desktop-menu integration.
The launcher delegates to `scripts/run-studio.sh`; it does not package or
download the proprietary Studio bundle.

Material changes include 18 modified Rust source files, the canonical patch,
GTK launcher sources and tests, launcher/upstream-layout documentation, and
the existing bundle and cache inventory. The source diff is 1,646 insertions
and 120 deletions. The copied app is Studio 0.742.0.7421053; hashes are in
docs/bundle.md and the manifest.

Verification evidence: launcher unit/CLI checks, desktop-entry validation, the
canonical patch `git apply --check` worktree validation, and the existing source
view, backing, run-loop, display-link, Objective-C, camera-focused tests and
release build were recorded as passing. The GTK GUI smoke test could not be
fully validated in the available display session. Manual Studio work ended
with an unresolved crash opening the large place and unresolved camera/docking
edge cases.

Exact continuation point: run scripts/run-studio.sh with a fresh STUDIO_LOG_NAME
and reproduce the place-opening crash normally. Preserve the raw log outside
Git, then isolate the require path failure before changing camera behavior.

Token report: the deployment-token parser returned `unavailable` because no
session record matched deployment `citric-launcher-20261012`.
