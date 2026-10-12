# Citric

Citric maintains the compatibility patches and launcher used to run the macOS version of Roblox Studio on Linux with Rosemary. The current tree does not include the full Rosemary source: it pins an upstream commit and applies the diffs versioned under `patches/`.

The GitHub `main` branch no longer descends from Rosemary's upstream history. The first Citric commit still contains the original Rosemary source snapshot, while the current branch snapshot contains only the Citric launcher, patches, and documentation.

## Build Rosemary

Build the patched runtime before its first use:

    ./scripts/citric build

This fetches the commit specified in `patches/base-commit` from the repository in `patches/upstream-url`, applies the files listed in `patches/series` to a temporary checkout, and builds the result with Cargo. The generated binary is stored in `bin/rosemary`, which is ignored by Git.

To verify the fetch and patch application without compiling:

    ./scripts/citric build --check-only

To compile without replacing the local `bin/rosemary` binary:

    ./scripts/citric build --build-only

You can also run the build script directly:

    ./scripts/build-studio.sh

## Launch Studio

    ./scripts/citric
    ./scripts/citric launch
    ./scripts/citric launch "/path/to/place.rbxl"

The launcher uses the local Studio bundle and generated binary. The Roblox Studio bundle, authenticated prefix, Darwin cache, and logs remain outside Git. Read `docs/bundle.md` before preparing any publication.

## Patch series

- Base commit: `patches/base-commit`
- Upstream repository: `patches/upstream-url`
- Application order: `patches/series`
- Canonical patch: `patches/0001-citric-runtime-compat.patch`

Run `./scripts/build-studio.sh --check-only` after changing the series. See `docs/patches/README.md` and `docs/upstream-layout.md` for the workflow and comparison with the Vinegar/Kombucha model.

The history of the work, confirmed fixes, observed crashes, and test limitations is documented in `docs/current-state.md`, `docs/compatibility.md`, `docs/crashes.md`, and `docs/validation.md`. Rosemary is maintained by [Microlift](https://github.com/microlift/rosemary); Citric does not distribute the proprietary Studio bundle.
