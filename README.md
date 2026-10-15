# Citric

Citric is a Linux launcher for the macOS version of Roblox Studio. It uses the [Rosemary](https://github.com/microlift/rosemary) runtime, built with Citric's compatibility patches, to run a local Roblox Studio app bundle. The launcher provides a GTK 4 interface and a command-line option for opening Studio or a place file.

The proprietary Roblox Studio app bundle is not included in Git. Use the launcher's **Download and install Roblox Studio** button for the pinned initial macOS x86_64 bundle; Citric verifies its recorded SHA-256 and stores it under `app/full/RobloxStudio.app`. At startup, the launcher checks Roblox's published Mac Studio release and changes the button to **UPDATE STUDIO NEW VERSION _version_** when a newer version is available. Clicking that button refreshes the release metadata and downloads the matching official build. Citric validates the HTTPS source, archive limits and paths, app identifier, advertised version and build number, executable, and x86_64 architecture before replacing the installed bundle. Replacement still requires confirmation, and a failed download or validation leaves the current bundle unchanged. Newer releases do not have a pinned checksum, so Citric validates them against the official release metadata and bundle contents; it does not claim to have run a Rosemary compatibility test for every release. Studio is never updated without a user click. You can also provide a compatible bundle under `app/` or select it in the launcher. Citric stores its built [Rosemary](https://github.com/microlift/rosemary) runtime and user configuration locally; it does not include an authenticated Studio prefix.

## Requirements

- Linux
- Python 3, GTK 4, and PyGObject for the graphical launcher
- Git, Rust, Cargo, and the native build dependencies required by [Rosemary](https://github.com/microlift/rosemary)
- A compatible macOS Roblox Studio app bundle

## Build

Build [Rosemary](https://github.com/microlift/rosemary) and apply Citric's compatibility patches:

```sh
./scripts/citric build
```

The resulting runtime is stored in `bin/rosemary`. To check that the source and patches can be prepared without compiling:

```sh
./scripts/citric build --check-only
```

## Use

Open the graphical launcher:

```sh
./scripts/citric
```

Start Studio from the command line, optionally opening a place file directly:

```sh
./scripts/citric launch
./scripts/citric launch "/path/to/place.rbxl"
```

On first launch, download the pinned Studio bundle or choose an existing one if Citric cannot find it automatically. The launcher lets you configure the [Rosemary](https://github.com/microlift/rosemary) prefix and SDL driver, save settings, build [Rosemary](https://github.com/microlift/rosemary), and open session logs. Known third-party plugin overrides are applied locally before launch; see [plugin compatibility notes](docs/plugin-overrides.md).

## Acknowledgements

Citric's launcher is based on [Nutmeg](https://github.com/frolleks/nutmeg). Its compatibility patch workflow is based on the approach used by [Vinegar](https://github.com/vinegarhq/vinegar) and its companion project [Kombucha](https://github.com/vinegarhq/kombucha).
