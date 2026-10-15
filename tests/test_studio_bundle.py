from __future__ import annotations

import hashlib
import io
import json
import plistlib
import stat
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from citric_launcher import studio_bundle


class _Response(io.BytesIO):
    def __init__(self, payload: bytes, url: str) -> None:
        super().__init__(payload)
        self.headers = {"Content-Length": str(len(payload))}
        self._url = url

    def geturl(self) -> str:
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        self.close()


class StudioBundleTests(unittest.TestCase):
    def test_latest_release_reads_validated_official_version_metadata(self) -> None:
        payload = b'{"version":"0.743.0.7431133","clientVersionUpload":"version-0123456789abcdef"}'
        response = _Response(payload, studio_bundle.VERSION_ENDPOINT)

        with patch.object(studio_bundle.urllib.request, "urlopen", return_value=response) as urlopen:
            release = studio_bundle._latest_release()

        self.assertEqual(release, studio_bundle.StudioRelease("0.743.0.7431133", "version-0123456789abcdef"))
        self.assertEqual(release.archive_url, "https://setup.rbxcdn.com/mac/version-0123456789abcdef-RobloxStudioApp.zip")
        self.assertEqual(urlopen.call_args.args[0].full_url, studio_bundle.VERSION_ENDPOINT)

    def test_latest_release_rejects_mismatched_pinned_build_metadata(self) -> None:
        payload = json.dumps(
            {"version": "0.743.0.7431133", "clientVersionUpload": studio_bundle.BUILD}
        ).encode()
        response = _Response(payload, studio_bundle.VERSION_ENDPOINT)

        with patch.object(studio_bundle.urllib.request, "urlopen", return_value=response):
            with self.assertRaises(studio_bundle.DownloadError):
                studio_bundle._latest_release()

    def test_update_check_compares_numeric_version_components(self) -> None:
        release = studio_bundle.StudioRelease("0.743.0.7431133", "version-0123456789abcdef")

        with patch.object(studio_bundle, "_latest_release", return_value=release):
            result = studio_bundle.check_update("0.742.0.7421053")

        self.assertTrue(result["update_available"])
        self.assertEqual(result["latest_build"], release.build)

    def test_latest_install_downloads_and_validates_the_reported_release(self) -> None:
        release = studio_bundle.StudioRelease("0.743.0.7431133", "version-0123456789abcdef")
        payload = _studio_archive(release.version)
        response = _Response(payload, release.archive_url)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "app" / "full" / "RobloxStudio.app"
            destination.mkdir(parents=True)
            (destination / "previous-install").write_text("keep until swap", encoding="utf-8")
            with (
                patch.object(studio_bundle, "ROOT", root),
                patch.object(studio_bundle, "_latest_release", return_value=release),
                patch.object(studio_bundle.urllib.request, "urlopen", return_value=response) as urlopen,
            ):
                result = studio_bundle.install(replace=True, latest=True)

            installed = plistlib.loads((destination / "Contents" / "Info.plist").read_bytes())

        self.assertIn(release.version, result)
        self.assertEqual(installed["CFBundleShortVersionString"], release.version)
        self.assertFalse((destination / "previous-install").exists())
        self.assertEqual(urlopen.call_args.args[0].full_url, release.archive_url)

    def test_invalid_latest_bundle_preserves_existing_install(self) -> None:
        release = studio_bundle.StudioRelease("0.743.0.7431133", "version-0123456789abcdef")
        payload = _studio_archive("0.742.0.7421053")
        response = _Response(payload, release.archive_url)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "app" / "full" / "RobloxStudio.app"
            destination.mkdir(parents=True)
            marker = destination / "previous-install"
            marker.write_text("must survive", encoding="utf-8")
            with (
                patch.object(studio_bundle, "ROOT", root),
                patch.object(studio_bundle, "_latest_release", return_value=release),
                patch.object(studio_bundle.urllib.request, "urlopen", return_value=response),
            ):
                with self.assertRaises(studio_bundle.DownloadError):
                    studio_bundle.install(replace=True, latest=True)

            self.assertEqual(marker.read_text(encoding="utf-8"), "must survive")
            self.assertEqual(list(destination.parent.glob(".citric-studio-backup-*")), [])

    def test_latest_install_requires_replacement_confirmation_before_download(self) -> None:
        release = studio_bundle.StudioRelease("0.743.0.7431133", "version-0123456789abcdef")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "app" / "full" / "RobloxStudio.app"
            destination.mkdir(parents=True)
            marker = destination / "previous-install"
            marker.write_text("must survive", encoding="utf-8")
            with (
                patch.object(studio_bundle, "ROOT", root),
                patch.object(studio_bundle, "_latest_release", return_value=release),
                patch.object(studio_bundle.urllib.request, "urlopen") as urlopen,
            ):
                with self.assertRaises(studio_bundle.DownloadError):
                    studio_bundle.install(latest=True)

            urlopen.assert_not_called()
            self.assertEqual(marker.read_text(encoding="utf-8"), "must survive")

    def test_pinned_archive_still_uses_its_recorded_checksum(self) -> None:
        payload = b"pinned archive test payload"
        response = _Response(payload, studio_bundle.PINNED_RELEASE.archive_url)
        digest = hashlib.sha256(payload).hexdigest()

        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / "studio.zip"
            with (
                patch.object(studio_bundle, "ARCHIVE_SHA256", digest),
                patch.object(studio_bundle.urllib.request, "urlopen", return_value=response),
            ):
                studio_bundle._download_archive(archive_path, studio_bundle.PINNED_RELEASE)
            self.assertEqual(archive_path.read_bytes(), payload)


def _studio_archive(version: str) -> bytes:
    version_parts = version.split(".")
    info = {
        "CFBundleIdentifier": "com.Roblox.RobloxStudio",
        "CFBundleShortVersionString": version,
        "CFBundleVersion": version_parts[-1],
        "CFBundleExecutable": "RobloxStudio",
    }
    executable = b"\xcf\xfa\xed\xfe" + struct.pack("<I", 0x01000007) + b"\0" * 64
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("RobloxStudio.app/Contents/Info.plist", plistlib.dumps(info))
        executable_info = zipfile.ZipInfo("RobloxStudio.app/Contents/MacOS/RobloxStudio")
        executable_info.create_system = 3
        executable_info.external_attr = (stat.S_IFREG | 0o755) << 16
        archive.writestr(executable_info, executable)
    return payload.getvalue()


if __name__ == "__main__":
    unittest.main()
