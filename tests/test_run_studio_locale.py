from __future__ import annotations

import os
import plistlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RunStudioLocaleTests(unittest.TestCase):
    def test_studio_uses_c_numeric_locale_even_when_launched_with_locale_all(self) -> None:
        with tempfile.TemporaryDirectory(prefix="citric-locale-") as temporary:
            root = Path(temporary)
            scripts = root / "scripts"
            scripts.mkdir()
            shutil.copy2(ROOT / "scripts" / "run-studio.sh", scripts / "run-studio.sh")
            shutil.copy2(ROOT / "scripts" / "patch-color-dialog.py", scripts / "patch-color-dialog.py")
            shutil.copy2(ROOT / "scripts" / "patch_plugin_compatibility.py", scripts / "patch_plugin_compatibility.py")

            studio = root / "RobloxStudio.app"
            contents = studio / "Contents"
            executable = contents / "MacOS" / "RobloxStudio"
            executable.parent.mkdir(parents=True)
            executable.touch()
            with (contents / "Info.plist").open("wb") as plist_file:
                plistlib.dump({"CFBundleExecutable": "RobloxStudio"}, plist_file)

            plugin = contents / "Plugins" / "Qt5" / "platforms" / "libqcocoa.dylib"
            plugin.parent.mkdir(parents=True)
            plugin.write_bytes(
                bytes.fromhex("55 48 89 e5 83 fe 03 0f 92 c0 5d c3 0f 1f 40 00")
                + b"\x00" * 16
                + bytes.fromhex("83 fe 02 74 37 83 fe 01 74 1b 85 f6 75 45")
            )

            rosemary = root / "rosemary"
            rosemary.write_text(
                "#!/bin/sh\n"
                "printf 'LC_ALL=%s\\n' \"${LC_ALL-<unset>}\"\n"
                "printf 'LC_NUMERIC=%s\\n' \"${LC_NUMERIC-<unset>}\"\n",
                encoding="utf-8",
            )
            rosemary.chmod(0o755)

            environment = os.environ.copy()
            environment.update(
                {
                    "HOME": str(root),
                    "LC_ALL": "pt_BR.UTF-8",
                    "LC_NUMERIC": "pt_BR.UTF-8",
                    "ROSEMARY_BIN": str(rosemary),
                    "ROSEMARY_PREFIX": str(root / "prefix"),
                    "ROSEMARY_ROOTFS_CACHE": str(root / "cache"),
                    "STUDIO_APP": str(studio),
                    "STUDIO_LOG_NAME": "locale-test",
                }
            )
            result = subprocess.run(
                [str(scripts / "run-studio.sh")],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            session_log = (root / "logs" / "locale-test.log").read_text(encoding="utf-8")
            metadata = (root / "logs" / "locale-test.meta").read_text(encoding="utf-8")
            self.assertIn("LC_ALL=<unset>\n", session_log)
            self.assertIn("LC_NUMERIC=C\n", session_log)
            self.assertIn("locale_source_lc_all=pt_BR.UTF-8\n", metadata)
            self.assertIn("locale_source_lc_numeric=pt_BR.UTF-8\n", metadata)
            self.assertIn("locale_lc_all=<unset>\n", metadata)
            self.assertIn("locale_lc_numeric=C\n", metadata)
            self.assertIn("plugin_compatibility_patch=Plugin compatibility: no installed plugin models found; skipped\n", metadata)
            self.assertIn("post_exit_plugin_patch_exit=0\n", metadata)
            self.assertIn("post_exit_plugin_patch_result=Plugin compatibility: no installed plugin models found; skipped\n", metadata)


if __name__ == "__main__":
    unittest.main()
