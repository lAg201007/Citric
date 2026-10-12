# Citric

Citric is a Linux launcher for the macOS version of Roblox Studio. It uses the [Rosemary](https://github.com/microlift/rosemary) runtime, built with Citric's compatibility patches, to run a local Roblox Studio app bundle. The launcher provides a GTK 4 interface and a command-line option for opening Studio or a place file.

The proprietary Roblox Studio app bundle is not included. Provide a compatible bundle under `app/` or select it in the launcher. Citric stores its built [Rosemary](https://github.com/microlift/rosemary) runtime and user configuration locally; it does not include an authenticated Studio prefix.

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

On first launch, choose the Studio bundle if Citric cannot find it automatically. The launcher lets you configure the [Rosemary](https://github.com/microlift/rosemary) prefix and SDL driver, save settings, build [Rosemary](https://github.com/microlift/rosemary), and open session logs.

## Acknowledgements

Citric's launcher is based on [Nutmeg](https://github.com/frolleks/nutmeg). Its compatibility patch workflow is based on the approach used by [Vinegar](https://github.com/vinegarhq/vinegar) and its companion project [Kombucha](https://github.com/vinegarhq/kombucha).
