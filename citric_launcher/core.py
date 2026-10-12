from __future__ import annotations

import json
import os
import shlex
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
LOGS_DIR = ROOT / "logs"


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
        "sdl_driver": "x11",
        "rosemary_bin": "",
        "studio_app": "",
    }


def normalize_config(values: Mapping[str, object], environment: Mapping[str, str] | None = None) -> dict[str, str]:
    environment = os.environ if environment is None else environment
    config = default_config(environment)
    for key in config:
        value = values.get(key, config[key])
        if not isinstance(value, str):
            raise ValueError(f"Configuração inválida para {key}")
        config[key] = value.strip()
    if not config["prefix"]:
        raise ValueError("O prefixo do Rosemary não pode ficar vazio")
    if config["sdl_driver"] not in {"x11", "wayland"}:
        raise ValueError("O driver SDL deve ser x11 ou wayland")
    return config


def load_config(path: Path | None = None, environment: Mapping[str, str] | None = None) -> dict[str, str]:
    path = path or config_path(environment)
    if not path.exists():
        return default_config(environment)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Não consegui ler {path}: {error}") from error
    if not isinstance(raw, dict):
        raise ValueError(f"Configuração inválida em {path}")
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
        raise FileNotFoundError(f"Script de inicialização não encontrado: {script}")
    argv = [str(script)]
    if place is not None:
        place_path = Path(place).expanduser()
        if not place_path.is_file():
            raise FileNotFoundError(f"Place não encontrada: {place_path}")
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
        "display_server": environment.get("STUDIO_SDL_DRIVER", config["sdl_driver"]),
        "logs_directory": str(root / "logs"),
        "config_file": str(config_path(environment)),
        "config_error": config_error,
    }
    checks["ready"] = bool(checks["launcher_script"] and rosemary and studio and checks["patch_script"] and not config_error)
    return checks
