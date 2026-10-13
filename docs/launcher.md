# Citric launcher

The GTK 4 launcher starts Roblox Studio with `scripts/run-studio.sh`. It can also prepare the runtime when the checkout does not yet contain `bin/rosemary`. The launcher interface, CLI help, and launcher-owned status and error messages are in English.

## Open

Run `./scripts/citric` to open the interface, or run `python3 -m citric_launcher` from the repository root.

The window lets you launch Studio or a `.rbxl`/`.rbxlx` place, build Rosemary from the patch series, select the prefix, Rosemary executable, Studio bundle and SDL driver, save XDG preferences, install the menu shortcut, and open the logs folder.

On first installation, click **Download and build Rosemary**. This fetches the pinned base, applies `patches/series`, builds the runtime, and saves it to `bin/rosemary`. The proprietary bundle must also be available under `app/` or selected manually.

## CLI

    ./scripts/citric build
    ./scripts/citric build --check-only
    ./scripts/citric build --build-only
    ./scripts/citric launch
    ./scripts/citric launch "/path/to/place.rbxl"
    ./scripts/citric launch --dry-run
    ./scripts/citric diagnose
    ./scripts/citric install-desktop
    ./scripts/citric uninstall-desktop

`build --check-only` validates the base revision and patches without building. `diagnose` checks local paths without launching Studio. `launch --dry-run` shows the arguments and environment variables that would be passed to the wrapper.

## Preferences and local files

Preferences are stored in `$XDG_CONFIG_HOME/citric/launcher.json`, or `~/.config/citric/launcher.json`. Logs are stored in `logs/` in the checkout. Temporary source and Cargo build output are stored in `$XDG_CACHE_HOME/citric` or `~/.cache/citric`. The generated `bin/rosemary` executable, `app/full/RobloxStudio.app`, and `downloads/darwin-cache` are excluded from Git.

## Dependencies

The interface requires Python 3, PyGObject, and GTK 4. Building Rosemary requires Git, Rust/Cargo, and the upstream dependencies required by the pinned revision. The build script runs Cargo against the prepared source; runtime configuration is kept in `scripts/run-studio.sh`.
