from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import re
import shutil
import stat
import struct
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.742.0.7421053"
BUILD = "version-6b80d5eacfba48e5"
ARCHIVE_SHA256 = "04bab64d3b463519874e09887e1ca75777e6b39285f4cb78720449477404da2d"
MAX_ARCHIVE_SIZE = 2 * 1024**3
MAX_UNPACKED_SIZE = 4 * 1024**3
USER_AGENT = "Citric-Studio-Bundle-Installer/1.0"
VERSION_ENDPOINT = "https://clientsettings.roblox.com/v2/client-version/MacStudio"
VERSION_PATTERN = re.compile(r"\d{1,10}(?:\.\d{1,10}){2,3}\Z")
BUILD_PATTERN = re.compile(r"version-[a-f0-9]{16,64}\Z")


@dataclass(frozen=True)
class StudioRelease:
    version: str
    build: str

    @property
    def archive_url(self) -> str:
        return f"https://setup.rbxcdn.com/mac/{self.build}-RobloxStudioApp.zip"


PINNED_RELEASE = StudioRelease(VERSION, BUILD)


class DownloadError(Exception):
    pass


def _download_archive(destination: Path, release: StudioRelease) -> None:
    request = urllib.request.Request(release.archive_url, headers={"User-Agent": USER_AGENT})
    digest = hashlib.sha256()
    downloaded = 0
    try:
        with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as output:
            final_url = urlsplit(response.geturl())
            expected_path = f"/mac/{release.build}-RobloxStudioApp.zip"
            if (
                final_url.scheme != "https"
                or final_url.hostname != "setup.rbxcdn.com"
                or final_url.path != expected_path
            ):
                raise DownloadError("The Roblox CDN redirected the download to an unexpected host.")
            content_length = response.headers.get("Content-Length")
            if content_length:
                try:
                    expected_size = int(content_length)
                except ValueError as error:
                    raise DownloadError("The Roblox CDN returned an invalid file size.") from error
                if expected_size <= 0 or expected_size > MAX_ARCHIVE_SIZE:
                    raise DownloadError("The Studio archive size is outside the accepted limit.")
            else:
                expected_size = None
            while chunk := response.read(1024 * 1024):
                downloaded += len(chunk)
                if downloaded > MAX_ARCHIVE_SIZE:
                    raise DownloadError("The Studio archive is larger than the accepted 2 GiB limit.")
                digest.update(chunk)
                output.write(chunk)
    except urllib.error.HTTPError as error:
        raise DownloadError(f"The Roblox CDN returned HTTP {error.code} while downloading Studio.") from error
    except urllib.error.URLError as error:
        raise DownloadError(f"Could not reach the Roblox CDN: {error.reason}") from error
    except TimeoutError as error:
        raise DownloadError("The Studio download timed out.") from error

    if downloaded == 0 or (expected_size is not None and downloaded != expected_size):
        raise DownloadError("The Studio download ended before the complete archive arrived.")
    if release == PINNED_RELEASE and digest.hexdigest() != ARCHIVE_SHA256:
        raise DownloadError("The downloaded pinned Studio archive did not match its SHA-256 checksum.")


def _latest_release() -> StudioRelease:
    request = urllib.request.Request(VERSION_ENDPOINT, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            final_url = urlsplit(response.geturl())
            if (
                final_url.scheme != "https"
                or final_url.hostname != "clientsettings.roblox.com"
                or final_url.path != "/v2/client-version/MacStudio"
            ):
                raise DownloadError("Roblox's version endpoint redirected to an unexpected host.")
            payload = response.read(64 * 1024 + 1)
    except urllib.error.HTTPError as error:
        raise DownloadError(f"Roblox's version endpoint returned HTTP {error.code}.") from error
    except urllib.error.URLError as error:
        raise DownloadError(f"Could not check Roblox Studio's version: {error.reason}") from error
    except TimeoutError as error:
        raise DownloadError("Roblox Studio's version check timed out.") from error
    if len(payload) > 64 * 1024:
        raise DownloadError("Roblox's version response exceeded the accepted size.")
    try:
        data = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DownloadError("Roblox's version endpoint returned invalid JSON.") from error
    if not isinstance(data, dict):
        raise DownloadError("Roblox's version response has an invalid structure.")
    version = data.get("version")
    build = data.get("clientVersionUpload")
    if not isinstance(version, str) or not VERSION_PATTERN.fullmatch(version):
        raise DownloadError("Roblox's version response did not contain a valid Studio version.")
    if not isinstance(build, str) or not BUILD_PATTERN.fullmatch(build):
        raise DownloadError("Roblox's version response did not contain a valid Studio build ID.")
    if build == BUILD and version != VERSION:
        raise DownloadError("Roblox's version response paired the pinned build with an unexpected version.")
    return StudioRelease(version, build)


def check_update(installed_version: str) -> dict[str, object]:
    if not VERSION_PATTERN.fullmatch(installed_version):
        raise DownloadError("The installed Studio version could not be identified.")
    latest_release = _latest_release()
    installed_parts = tuple(int(part) for part in installed_version.split("."))
    latest_parts = tuple(int(part) for part in latest_release.version.split("."))
    width = max(len(installed_parts), len(latest_parts))
    installed_parts += (0,) * (width - len(installed_parts))
    latest_parts += (0,) * (width - len(latest_parts))
    return {
        "installed_version": installed_version,
        "latest_version": latest_release.version,
        "latest_build": latest_release.build,
        "update_available": latest_parts > installed_parts,
    }


def _archive_path(info: zipfile.ZipInfo) -> tuple[str, ...] | None:
    name = info.filename
    if "\\" in name:
        raise DownloadError("The Studio archive contains a path with an invalid separator.")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part == ".." for part in path.parts):
        raise DownloadError("The Studio archive contains an unsafe path.")
    parts = tuple(part for part in path.parts if part not in {"", "."})
    if not parts or parts[0] == "__MACOSX":
        return None
    if parts[0] != "RobloxStudio.app":
        raise DownloadError("The Studio archive does not have the expected RobloxStudio.app layout.")
    return parts


def _extract_bundle(archive_path: Path, extraction_root: Path) -> Path:
    app_root = extraction_root / "RobloxStudio.app"
    app_root.mkdir(parents=True)
    directories: list[tuple[Path, int]] = []
    regular_files: list[tuple[zipfile.ZipInfo, Path, int]] = []
    symbolic_links: list[tuple[zipfile.ZipInfo, Path]] = []
    total_size = 0
    seen: set[tuple[str, ...]] = set()

    try:
        with zipfile.ZipFile(archive_path) as archive:
            for info in archive.infolist():
                parts = _archive_path(info)
                if parts is None:
                    continue
                if parts in seen:
                    raise DownloadError("The Studio archive contains a duplicate path.")
                seen.add(parts)
                target = extraction_root.joinpath(*parts)
                mode = (info.external_attr >> 16) & 0xFFFF
                if info.is_dir() or stat.S_ISDIR(mode):
                    directories.append((target, mode & 0o777 or 0o755))
                elif stat.S_ISLNK(mode):
                    symbolic_links.append((info, target))
                elif stat.S_IFMT(mode) in {0, stat.S_IFREG}:
                    total_size += info.file_size
                    if total_size > MAX_UNPACKED_SIZE:
                        raise DownloadError("The extracted Studio bundle would exceed the accepted 4 GiB limit.")
                    regular_files.append((info, target, mode & 0o777 or 0o644))
                else:
                    raise DownloadError("The Studio archive contains an unsupported special file.")

            for directory, _mode in sorted(directories, key=lambda item: len(item[0].parts)):
                directory.mkdir(parents=True, exist_ok=True)
            for info, target, mode in regular_files:
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output, length=1024 * 1024)
                target.chmod(mode)
            for info, target in symbolic_links:
                target_text = archive.read(info).decode("utf-8")
                link_target = PurePosixPath(target_text)
                if not target_text or link_target.is_absolute() or "\\" in target_text:
                    raise DownloadError("The Studio archive contains an unsafe symbolic link.")
                resolved_parts = list(target.relative_to(app_root).parent.parts)
                for part in link_target.parts:
                    if part in {"", "."}:
                        continue
                    if part == "..":
                        if not resolved_parts:
                            raise DownloadError("The Studio archive contains a symbolic link outside the app bundle.")
                        resolved_parts.pop()
                    else:
                        resolved_parts.append(part)
                if target.parent.is_symlink():
                    raise DownloadError("The Studio archive contains a symbolic link through another link.")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(target_text)
    except zipfile.BadZipFile as error:
        raise DownloadError("The downloaded Studio file is not a valid ZIP archive.") from error
    except (OSError, RuntimeError, UnicodeDecodeError) as error:
        raise DownloadError(f"Could not safely extract the Studio archive: {error}") from error

    for directory, mode in sorted(directories, key=lambda item: len(item[0].parts), reverse=True):
        if directory.exists() and not directory.is_symlink():
            directory.chmod(mode)
    if not app_root.is_dir():
        raise DownloadError("The Studio archive did not contain RobloxStudio.app.")
    return app_root


def _is_x86_64_macho(executable: Path) -> bool:
    try:
        with executable.open("rb") as stream:
            header = stream.read(4096)
    except OSError:
        return False
    if header[:4] == b"\xcf\xfa\xed\xfe":
        return len(header) >= 8 and struct.unpack_from("<I", header, 4)[0] == 0x01000007
    if header[:4] == b"\xfe\xed\xfa\xcf":
        return len(header) >= 8 and struct.unpack_from(">I", header, 4)[0] == 0x01000007
    if header[:4] in {b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca"} and len(header) >= 8:
        little_endian = header[:4] == b"\xbe\xba\xfe\xca"
        byte_order = "<" if little_endian else ">"
        count = struct.unpack_from(f"{byte_order}I", header, 4)[0]
        if count > 128:
            return False
        entry_size = 20
        for index in range(count):
            offset = 8 + index * entry_size
            if offset + 4 > len(header):
                return False
            cpu_type = struct.unpack_from(f"{byte_order}I", header, offset)[0]
            if cpu_type == 0x01000007:
                return True
    return False


def _validate_bundle(bundle: Path, release: StudioRelease) -> None:
    try:
        info = plistlib.loads((bundle / "Contents" / "Info.plist").read_bytes())
    except (OSError, plistlib.InvalidFileException, ValueError) as error:
        raise DownloadError(f"The downloaded app has no valid Info.plist: {error}") from error
    if not isinstance(info, dict):
        raise DownloadError("The downloaded app's Info.plist has an invalid structure.")
    executable_name = info.get("CFBundleExecutable")
    executable = bundle / "Contents" / "MacOS" / str(executable_name)
    version_parts = release.version.split(".")
    expected_bundle_build = version_parts[-1] if len(version_parts) == 4 else None
    if (
        info.get("CFBundleIdentifier") != "com.Roblox.RobloxStudio"
        or info.get("CFBundleShortVersionString") != release.version
        or (expected_bundle_build is not None and info.get("CFBundleVersion") != expected_bundle_build)
        or executable_name != "RobloxStudio"
        or not executable.is_file()
        or not os.access(executable, os.X_OK)
        or not _is_x86_64_macho(executable)
    ):
        raise DownloadError("The downloaded app did not match the validated Citric Studio bundle (Intel x86_64).")


def _installed_version(bundle: Path) -> str | None:
    if bundle.is_symlink():
        return None
    try:
        info = plistlib.loads((bundle / "Contents" / "Info.plist").read_bytes())
    except (OSError, plistlib.InvalidFileException, ValueError):
        return None
    if not isinstance(info, dict):
        return None
    executable_name = info.get("CFBundleExecutable")
    executable = bundle / "Contents" / "MacOS" / str(executable_name)
    if (
        info.get("CFBundleIdentifier") != "com.Roblox.RobloxStudio"
        or executable_name != "RobloxStudio"
        or not executable.is_file()
        or not os.access(executable, os.X_OK)
        or not _is_x86_64_macho(executable)
    ):
        return None
    version = info.get("CFBundleShortVersionString")
    return version if isinstance(version, str) else None


def install(replace: bool = False, latest: bool = False) -> str:
    release = _latest_release() if latest else PINNED_RELEASE
    destination = ROOT / "app" / "full" / "RobloxStudio.app"
    if (ROOT / "app").is_symlink() or destination.parent.is_symlink():
        raise DownloadError("The app/full install path contains a symbolic link; no files were changed.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if _installed_version(destination) == release.version:
        return f"Roblox Studio {release.version} is already installed at {destination.relative_to(ROOT)}."
    if destination.exists() or destination.is_symlink():
        if not replace:
            raise DownloadError("A different Studio bundle is already installed. Confirm replacement in the launcher first.")
        if destination.is_symlink() or not destination.is_dir():
            raise DownloadError("The existing Studio destination is not a regular app bundle; it was left unchanged.")

    with tempfile.TemporaryDirectory(prefix=".citric-studio-", dir=destination.parent) as temporary_name:
        temporary = Path(temporary_name)
        archive = temporary / "studio.zip"
        extraction_root = temporary / "extracted"
        extraction_root.mkdir()
        print(f"Downloading official Roblox Studio {release.version}…", flush=True)
        _download_archive(archive, release)
        print("Validating the archive and extracting RobloxStudio.app…", flush=True)
        staged_bundle = _extract_bundle(archive, extraction_root)
        _validate_bundle(staged_bundle, release)

        current_version = _installed_version(destination)
        if current_version == release.version:
            return f"Roblox Studio {release.version} is already installed at {destination.relative_to(ROOT)}."
        if destination.exists() or destination.is_symlink():
            if not replace:
                raise DownloadError(
                    "A different Studio bundle appeared during the download; it was left unchanged. "
                    "Confirm replacement in the launcher before trying again."
                )
            if destination.is_symlink() or not destination.is_dir():
                raise DownloadError("The existing Studio destination changed during download; it was left unchanged.")

        backup = destination.parent / f".citric-studio-backup-{os.getpid()}"
        had_previous = destination.exists()
        if had_previous:
            if backup.exists():
                raise DownloadError("A previous Studio replacement backup already exists; it was left untouched.")
            os.replace(destination, backup)
        try:
            os.replace(staged_bundle, destination)
        except BaseException:
            if had_previous and backup.exists():
                try:
                    os.replace(backup, destination)
                except OSError as restore_error:
                    raise DownloadError(
                        f"Installation failed and the previous bundle remains at {backup.relative_to(ROOT)}."
                    ) from restore_error
            raise
        if had_previous:
            try:
                shutil.rmtree(backup)
            except OSError as error:
                return (
                    f"Installed Roblox Studio {release.version}, but the old bundle remains at "
                    f"{backup.relative_to(ROOT)} and could not be removed: {error}"
                )

    return f"Installed Roblox Studio {release.version} at {destination.relative_to(ROOT)}."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download and validate an official Roblox Studio bundle")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--replace", action="store_true", help="replace a different app bundle after confirmation")
    modes.add_argument("--check-update", action="store_true", help="check Roblox's currently published Studio version")
    parser.add_argument("--latest", action="store_true", help="download and validate the currently published release")
    parser.add_argument("--installed-version", help="currently installed Studio version for --check-update")
    args = parser.parse_args(argv)
    try:
        if args.check_update:
            if args.latest:
                parser.error("--check-update cannot be combined with --latest")
            if not args.installed_version:
                parser.error("--check-update requires --installed-version")
            print(json.dumps(check_update(args.installed_version), separators=(",", ":")))
            return 0
        print(install(replace=args.replace, latest=args.latest))
    except (DownloadError, OSError) as error:
        print(f"Studio download failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
