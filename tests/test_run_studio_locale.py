from __future__ import annotations

import json
import os
import plistlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RunStudioLocaleTests(unittest.TestCase):
    def _create_launch_fixture(self, root: Path) -> tuple[Path, Path, Path]:
        scripts = root / "scripts"
        scripts.mkdir()
        for name in (
            "run-studio.sh",
            "patch-color-dialog.py",
            "patch_plugin_compatibility.py",
            "summarize-memory-diagnostics.py",
            "trace-studio-memory.py",
        ):
            shutil.copy2(ROOT / "scripts" / name, scripts / name)

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
            "printf 'LC_NUMERIC=%s\\n' \"${LC_NUMERIC-<unset>}\"\n"
            "printf 'MIMALLOC_SHOW_STATS=%s\\n' \"${MIMALLOC_SHOW_STATS-<unset>}\"\n"
            "printf 'ROSEMARY_TRACE_INTERPOSE=%s\\n' \"${ROSEMARY_TRACE_INTERPOSE-<unset>}\"\n"
            "printf 'ROSEMARY_TRACE_VM=%s\\n' \"${ROSEMARY_TRACE_VM-<unset>}\"\n"
            "printf 'ROSEMARY_ENVIRON=%s\\n' \"${ROSEMARY_ENVIRON-<unset>}\"\n",
            encoding="utf-8",
        )
        with rosemary.open("a", encoding="utf-8") as rosemary_file:
            rosemary_file.write(
                "if [ \"$ROSEMARY_TRACE_INTERPOSE\" = 1 ]; then\n"
                "  printf 'DFLog::Mimalloc mi_option_show_stats=1\\n'\n"
                "  printf 'heap stats\\n'\n"
                "  printf 'rosemary: interpose: malloc in QtCore -> 0x1\\n'\n"
                "fi\n"
            )
        rosemary.chmod(0o755)
        return scripts, studio, rosemary

    def _launch_environment(
        self, root: Path, studio: Path, rosemary: Path, log_name: str
    ) -> dict[str, str]:
        environment = os.environ.copy()
        environment.pop("STUDIO_MEMORY_TRACE", None)
        environment.update(
            {
                "HOME": str(root),
                "ROSEMARY_BIN": str(rosemary),
                "ROSEMARY_PREFIX": str(root / "prefix"),
                "ROSEMARY_ROOTFS_CACHE": str(root / "cache"),
                "STUDIO_APP": str(studio),
                "STUDIO_LOG_NAME": log_name,
            }
        )
        return environment

    def test_studio_uses_c_numeric_locale_even_when_launched_with_locale_all(self) -> None:
        with tempfile.TemporaryDirectory(prefix="citric-locale-") as temporary:
            root = Path(temporary)
            scripts, studio, rosemary = self._create_launch_fixture(root)
            logs = root / "logs"
            logs.mkdir()
            for marker in (".memory-trace-once", ".memory-trace-detailed-once", ".memory-trace-detailed-enabled"):
                (logs / marker).touch()
            environment = self._launch_environment(root, studio, rosemary, "locale-test")
            environment.update(
                {
                    "LC_ALL": "pt_BR.UTF-8",
                    "LC_NUMERIC": "pt_BR.UTF-8",
                    "MIMALLOC_SHOW_STATS": "inherited-value",
                    "ROSEMARY_ENVIRON": "CUSTOM_GUEST_VALUE=keep",
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
            self.assertFalse((logs / "locale-test.memory.jsonl").exists())
            self.assertNotIn("Memory trace:", result.stdout)
            self.assertIn("memory_trace=false\n", metadata)
            self.assertIn("LC_ALL=<unset>\n", session_log)
            self.assertIn("LC_NUMERIC=C\n", session_log)
            self.assertIn("MIMALLOC_SHOW_STATS=inherited-value\n", session_log)
            self.assertIn("ROSEMARY_TRACE_INTERPOSE=<unset>\n", session_log)
            self.assertIn("ROSEMARY_TRACE_VM=<unset>\n", session_log)
            self.assertIn("ROSEMARY_ENVIRON=CUSTOM_GUEST_VALUE=keep\n", session_log)
            self.assertIn("locale_source_lc_all=pt_BR.UTF-8\n", metadata)
            self.assertIn("locale_source_lc_numeric=pt_BR.UTF-8\n", metadata)
            self.assertIn("locale_lc_all=<unset>\n", metadata)
            self.assertIn("locale_lc_numeric=C\n", metadata)
            self.assertIn("plugin_compatibility_patch=Plugin compatibility: no installed plugin models found; skipped\n", metadata)
            self.assertIn("post_exit_plugin_patch_exit=0\n", metadata)
            self.assertIn("post_exit_plugin_patch_result=Plugin compatibility: no installed plugin models found; skipped\n", metadata)

    def test_memory_trace_requests_mimalloc_stats_only_for_diagnostic_launch(self) -> None:
        with tempfile.TemporaryDirectory(prefix="citric-memory-launch-") as temporary:
            root = Path(temporary)
            scripts, studio, rosemary = self._create_launch_fixture(root)
            logs = root / "logs"
            logs.mkdir()
            arm_file = logs / ".memory-trace-once"
            arm_file.touch(mode=0o600)
            environment = self._launch_environment(root, studio, rosemary, "trace-test")
            environment["STUDIO_MEMORY_TRACE_INTERVAL"] = "1"
            environment["STUDIO_MEMORY_TRACE"] = "1"
            environment.pop("MIMALLOC_SHOW_STATS", None)
            environment["ROSEMARY_ENVIRON"] = "KEEP_GUEST_SETTING=enabled"

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
            trace_path = logs / "trace-test.memory.jsonl"
            self.assertTrue(trace_path.is_file())
            session_log = (logs / "trace-test.log").read_text(encoding="utf-8")
            metadata = (logs / "trace-test.meta").read_text(encoding="utf-8")
            self.assertIn("MIMALLOC_SHOW_STATS=1\n", session_log)
            self.assertIn("ROSEMARY_TRACE_INTERPOSE=1\n", session_log)
            self.assertIn(
                "ROSEMARY_ENVIRON=KEEP_GUEST_SETTING=enabled\nMIMALLOC_SHOW_STATS\n",
                session_log,
            )
            self.assertIn("memory_trace=true\n", metadata)
            self.assertIn("mimalloc_host_stats_requested=true\n", metadata)
            self.assertIn("mimalloc_guest_stats_requested=true\n", metadata)
            self.assertIn("allocator_interpose_trace_requested=true\n", metadata)
            self.assertIn("rosemary_vm_trace_requested=false\n", metadata)
            self.assertIn("guest_mimalloc_show_stats_observed=1\n", metadata)
            self.assertIn("mimalloc_stats_report_observed=1\n", metadata)
            self.assertIn("allocator_interpose_bindings_observed=1\n", metadata)
            self.assertIn("memory_trace_detailed_vmas_requested=false\n", metadata)
            self.assertTrue(arm_file.exists())

    def test_detailed_environment_arms_a_local_mapping_trace(self) -> None:
        with tempfile.TemporaryDirectory(prefix="citric-memory-vma-launch-") as temporary:
            root = Path(temporary)
            scripts, studio, rosemary = self._create_launch_fixture(root)
            logs = root / "logs"
            logs.mkdir()
            detailed_marker = logs / ".memory-trace-detailed-once"
            detailed_marker.touch(mode=0o600)
            environment = self._launch_environment(
                root, studio, rosemary, "trace-vma-test"
            )
            environment["STUDIO_MEMORY_TRACE_INTERVAL"] = "1"
            environment["STUDIO_MEMORY_TRACE"] = "detailed"

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
            self.assertTrue((logs / "trace-vma-test.memory.jsonl").is_file())
            metadata = (logs / "trace-vma-test.meta").read_text(encoding="utf-8")
            self.assertIn("memory_trace_detailed_vmas_requested=true\n", metadata)
            self.assertIn("rosemary_vm_trace_requested=true\n", metadata)
            session_log = (logs / "trace-vma-test.log").read_text(encoding="utf-8")
            self.assertIn("ROSEMARY_TRACE_VM=1\n", session_log)
            trace_metadata = json.loads(
                (logs / "trace-vma-test.memory.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()[0]
            )
            self.assertTrue(
                trace_metadata["privacy"]["records_memory_mapping_paths_or_addresses"]
            )
            # Legacy marker files remain inert and are not consumed.
            self.assertTrue(detailed_marker.exists())

    def test_environment_capture_covers_successive_launches(self) -> None:
        with tempfile.TemporaryDirectory(prefix="citric-memory-persistent-") as temporary:
            root = Path(temporary)
            scripts, studio, rosemary = self._create_launch_fixture(root)
            logs = root / "logs"
            logs.mkdir()
            marker = logs / ".memory-trace-detailed-enabled"
            marker.touch(mode=0o600)
            for name in ("first-start", "play-test"):
                environment = self._launch_environment(root, studio, rosemary, name)
                environment["STUDIO_MEMORY_TRACE"] = "detailed"
                result = subprocess.run(
                    [str(scripts / "run-studio.sh")], cwd=root, env=environment,
                    capture_output=True, text=True, timeout=30, check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue((logs / f"{name}.memory.jsonl").is_file())
                metadata = (logs / f"{name}.meta").read_text()
                self.assertIn("memory_trace=true\n", metadata)
                self.assertRegex(metadata, r"(?m)^rosemary_sha256=[0-9a-f]{64}$")
                self.assertIn("memory_trace_mode=detailed\n", metadata)
                self.assertIn("memory_trace_detailed_vmas_requested=true\n", metadata)
                self.assertTrue(marker.exists())


if __name__ == "__main__":
    unittest.main()
