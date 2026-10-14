from __future__ import annotations

import json
import os
import shlex
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
LOGS_DIR = ROOT / "logs"
STUDIO_BUNDLE_VERSION = "0.742.0.7421053"


@dataclass(frozen=True)
class LaunchSpec:
    argv: tuple[str, ...]
    env: dict[str, str]


def _home(environment: Mapping[str, str]) -> Path:
    return Path(environment.get("HOME", str(Path.home()))).expanduser()


def config_path(environment: Mapping[str, str] | None = None) -> Path:
    environment = os.environ if environment is None else environment
    config_home = Path(environment.get("XDG_CONFIG_HOME", _home(environment) / ".config"))
    return config_home / "citric" / "launcher.json"


def data_home(environment: Mapping[str, str] | None = None) -> Path:
    environment = os.environ if environment is None else environment
    return Path(environment.get("XDG_DATA_HOME", _home(environment) / ".local" / "share"))


def default_config(environment: Mapping[str, str] | None = None) -> dict[str, str]:
    environment = os.environ if environment is None else environment
    return {
        "prefix": str(_home(environment) / "rosemary-studio-prefix"),
        "sdl_driver": "wayland",
        "rosemary_bin": "",
        "studio_app": "",
    }


def normalize_config(values: Mapping[str, object], environment: Mapping[str, str] | None = None) -> dict[str, str]:
    environment = os.environ if environment is None else environment
    config = default_config(environment)
    for key in config:
        value = values.get(key, config[key])
        if not isinstance(value, str):
            raise ValueError(f"Invalid configuration for {key}")
        config[key] = value.strip()
    if not config["prefix"]:
        raise ValueError("The Rosemary prefix cannot be empty")
    if config["sdl_driver"] not in {"x11", "wayland"}:
        raise ValueError("The SDL driver must be x11 or wayland")
    return config


def load_config(path: Path | None = None, environment: Mapping[str, str] | None = None) -> dict[str, str]:
    path = path or config_path(environment)
    if not path.exists():
        return default_config(environment)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read {path}: {error}") from error
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid configuration in {path}")
    return normalize_config(raw, environment)


def save_config(values: Mapping[str, object], path: Path | None = None, environment: Mapping[str, str] | None = None) -> Path:
    path = path or config_path(environment)
    config = normalize_config(values, environment)
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(config, ensure_ascii=False, indent=2) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(prefix=".launcher-", dir=path.parent, text=True)
    temporary_path = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(serialized)
        temporary_path.replace(path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
    return path


def build_rosemary_spec(root: Path = ROOT, check_only: bool = False, build_only: bool = False) -> LaunchSpec:
    script = root / "scripts" / "build-studio.sh"
    if not script.is_file():
        raise FileNotFoundError(f"Build script not found: {script}")
    argv = [str(script)]
    if check_only:
        argv.append("--check-only")
    elif build_only:
        argv.append("--build-only")
    return LaunchSpec(tuple(argv), {})


def download_studio_spec(root: Path = ROOT, replace: bool = False) -> LaunchSpec:
    module = root / "citric_launcher" / "studio_bundle.py"
    if not module.is_file():
        raise FileNotFoundError(f"Studio bundle download module not found: {module}")
    argv = [sys.executable, str(module)]
    if replace:
        argv.append("--replace")
    return LaunchSpec(tuple(argv), {})


def studio_bundle_version(bundle: Path) -> str | None:
    if bundle.is_symlink():
        return None
    try:
        import plistlib

        info = plistlib.loads((bundle / "Contents" / "Info.plist").read_bytes())
        if not isinstance(info, dict):
            return None
        version = info.get("CFBundleShortVersionString")
        executable = info.get("CFBundleExecutable")
        if (
            info.get("CFBundleIdentifier") != "com.Roblox.RobloxStudio"
            or executable != "RobloxStudio"
            or not (bundle / "Contents" / "MacOS" / executable).is_file()
        ):
            return None
        return version if isinstance(version, str) else None
    except (OSError, ValueError):
        return None


def detect_rosemary(root: Path = ROOT, environment: Mapping[str, str] | None = None) -> Path | None:
    environment = environment or os.environ
    candidates = (
        root / "bin" / "rosemary",
        root / "target" / "release" / "rosemary",
        Path(environment.get("HOME", str(Path.home()))) / "rosemary" / "target" / "release" / "rosemary",
    )
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    installed = shutil.which("rosemary", path=environment.get("PATH"))
    return Path(installed) if installed else None


def discover_studio_app(root: Path = ROOT) -> Path | None:
    try:
        import plistlib

        candidates: list[tuple[bool, Path]] = []
        for plist_path in (root / "app").rglob("Contents/Info.plist"):
            try:
                info = plistlib.loads(plist_path.read_bytes())
            except (OSError, ValueError):
                continue
            executable = info.get("CFBundleExecutable", "")
            if executable in {"RobloxStudio", "RobloxStudioInstaller"} and (plist_path.parent / "MacOS" / executable).is_file():
                candidates.append((executable != "RobloxStudio", plist_path.parent.parent))
        return sorted(candidates, key=lambda item: item[0])[0][1] if candidates else None
    except OSError:
        return None


def build_launch_spec(
    config: Mapping[str, object],
    place: str | Path | None = None,
    root: Path = ROOT,
    base_environment: Mapping[str, str] | None = None,
) -> LaunchSpec:
    environment = os.environ if base_environment is None else base_environment
    normalized = normalize_config(config, environment)
    script = root / "scripts" / "run-studio.sh"
    if not script.is_file():
        raise FileNotFoundError(f"Launch script not found: {script}")
    argv = [str(script)]
    if place is not None:
        place_path = Path(place).expanduser()
        if not place_path.is_file():
            raise FileNotFoundError(f"Place not found: {place_path}")
        argv.append(str(place_path.resolve()))
    overrides = {
        "ROSEMARY_PREFIX": str(Path(normalized["prefix"]).expanduser()),
        "STUDIO_SDL_DRIVER": normalized["sdl_driver"],
    }
    if normalized["rosemary_bin"]:
        overrides["ROSEMARY_BIN"] = str(Path(normalized["rosemary_bin"]).expanduser())
    if normalized["studio_app"]:
        overrides["STUDIO_APP"] = str(Path(normalized["studio_app"]).expanduser())
    return LaunchSpec(tuple(argv), overrides)


def format_command(argv: tuple[str, ...] | list[str]) -> str:
    return shlex.join(argv)


def _desktop_escape(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("%", "%%")
    return f'"{escaped}"'


def desktop_entry(root: Path = ROOT) -> str:
    launcher = str((root / "scripts" / "citric").resolve())
    return "\n".join(
        (
            "[Desktop Entry]",
            "Type=Application",
            "Version=1.0",
            "Name=Citric Roblox Studio",
            "Comment=Launch Roblox Studio through Rosemary",
            f"Exec={_desktop_escape(launcher)}",
            f"TryExec={_desktop_escape(launcher)}",
            "Terminal=false",
            "Categories=Development;IDE;",
            "StartupNotify=true",
            "",
        )
    )


def desktop_file_path(environment: Mapping[str, str] | None = None) -> Path:
    return data_home(environment) / "applications" / "citric-launcher.desktop"


def install_desktop_entry(root: Path = ROOT, environment: Mapping[str, str] | None = None) -> Path:
    destination = desktop_file_path(environment)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".desktop.tmp")
    temporary.write_text(desktop_entry(root), encoding="utf-8")
    temporary.chmod(0o644)
    temporary.replace(destination)
    return destination


def uninstall_desktop_entry(environment: Mapping[str, str] | None = None) -> Path:
    destination = desktop_file_path(environment)
    destination.unlink(missing_ok=True)
    return destination


def diagnose(root: Path = ROOT, environment: Mapping[str, str] | None = None) -> dict[str, object]:
    environment = os.environ if environment is None else environment
    config_error = None
    try:
        config = load_config(environment=environment)
    except ValueError as error:
        config = default_config(environment)
        config_error = str(error)
    rosemary_override = environment.get("ROSEMARY_BIN") or config["rosemary_bin"]
    studio_override = environment.get("STUDIO_APP") or config["studio_app"]
    rosemary = Path(rosemary_override).expanduser() if rosemary_override else detect_rosemary(root, environment)
    studio = Path(studio_override).expanduser() if studio_override else discover_studio_app(root)
    if rosemary is not None and (not rosemary.is_file() or not os.access(rosemary, os.X_OK)):
        rosemary = None
    if studio is not None and not studio.is_dir():
        studio = None
    checks = {
        "launcher_script": (root / "scripts" / "run-studio.sh").is_file(),
        "rosemary_executable": str(rosemary) if rosemary else None,
        "studio_bundle": str(studio) if studio else None,
        "patch_script": (root / "scripts" / "patch-color-dialog.py").is_file(),
        "build_script": (root / "scripts" / "build-studio.sh").is_file(),
        "patch_series": (root / "patches" / "series").is_file() and (root / "patches" / "base-commit").is_file() and (root / "patches" / "upstream-url").is_file(),
        "display_server": environment.get("STUDIO_SDL_DRIVER", config["sdl_driver"]),
        "logs_directory": str(root / "logs"),
        "config_file": str(config_path(environment)),
        "config_error": config_error,
    }
    checks["ready"] = bool(
        checks["launcher_script"]
        and checks["build_script"]
        and checks["patch_series"]
        and rosemary
        and studio
        and checks["patch_script"]
        and not config_error
    )
    return checks
