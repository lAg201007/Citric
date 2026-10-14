# Citric

Citric is a Linux launcher for the macOS version of Roblox Studio. It uses the [Rosemary](https://github.com/microlift/rosemary) runtime, built with Citric's compatibility patches, to run a local Roblox Studio app bundle. The launcher provides a GTK 4 interface and a command-line option for opening Studio or a place file.

The proprietary Roblox Studio app bundle is not included in Git. Use the launcher's **Download and install Roblox Studio** button to retrieve the pinned official macOS x86_64 bundle; Citric verifies its SHA-256 checksum and stores it under `app/full/RobloxStudio.app`. At startup, the launcher checks Roblox's published Mac Studio version and changes the button to **UPDATE STUDIO NEW VERSION _version_** when it finds a release newer than the selected installed bundle. Citric never updates Studio automatically. The button installs the pinned, validated build when that is the available update; if Roblox has published a version newer than Citric's validated build, it displays the version but leaves the installed bundle unchanged. You can also provide a compatible bundle under `app/` or select it in the launcher. Citric stores its built [Rosemary](https://github.com/microlift/rosemary) runtime and user configuration locally; it does not include an authenticated Studio prefix.

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
