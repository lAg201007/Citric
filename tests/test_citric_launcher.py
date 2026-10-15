from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from citric_launcher.core import (
    build_launch_spec,
    build_rosemary_spec,
    config_path,
    desktop_entry,
    desktop_file_path,
    default_config,
    download_studio_spec,
    install_desktop_entry,
    load_config,
    normalize_config,
    save_config,
    uninstall_desktop_entry,
)


class CitricLauncherTests(unittest.TestCase):
    def test_latest_studio_download_spec_passes_latest_and_replacement_flags(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            module = root / "citric_launcher" / "studio_bundle.py"
            module.parent.mkdir()
            module.write_text("", encoding="utf-8")

            spec = download_studio_spec(root, replace=True, latest=True)

            self.assertEqual(spec.argv[1:], (str(module), "--replace", "--latest"))

    def test_build_spec_invokes_patch_build_script_and_supports_check_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / "scripts" / "build-studio.sh"
            script.parent.mkdir()
            script.write_text("#!/bin/sh\n")

            build = build_rosemary_spec(root)
            check = build_rosemary_spec(root, check_only=True)
            build_only = build_rosemary_spec(root, build_only=True)

            self.assertEqual(build.argv, (str(script),))
            self.assertEqual(check.argv, (str(script), "--check-only"))
            self.assertEqual(build_only.argv, (str(script), "--build-only"))
            self.assertEqual(build.env, {})

    def test_config_uses_xdg_and_round_trips_with_private_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            environment = {"HOME": str(home), "XDG_CONFIG_HOME": str(home / "config")}
            destination = config_path(environment)
            config = default_config(environment)
            config["sdl_driver"] = "wayland"

            save_config(config, environment=environment)
            loaded = load_config(environment=environment)

            self.assertEqual(destination, home / "config" / "citric" / "launcher.json")
            self.assertEqual(loaded, config)
            self.assertEqual(destination.stat().st_mode & 0o777, 0o600)

    def test_invalid_sdl_driver_is_rejected(self) -> None:
        config = default_config({"HOME": "/tmp"})
        config["sdl_driver"] = "invalid"
        with self.assertRaises(ValueError):
            normalize_config(config, {"HOME": "/tmp"})

    def test_launch_spec_keeps_place_path_as_one_argument_and_overrides_only_selected_environment(self) -> None:
        with tempfile.TemporaryDirectory(prefix="Citric Space ") as temporary:
            root = Path(temporary)
            script = root / "scripts" / "run-studio.sh"
            script.parent.mkdir()
            script.write_text("#!/bin/sh\n")
            place = root / "Case Place.rbxl"
            place.write_bytes(b"place")
            config = default_config({"HOME": temporary})
            config["prefix"] = str(root / "wine prefix")
            config["sdl_driver"] = "x11"
            config["rosemary_bin"] = "/opt/rosemary/bin/rosemary"
            config["studio_app"] = "/opt/RobloxStudio.app"

            spec = build_launch_spec(config, place, root, {"PATH": "/bin", "HOME": temporary})

            self.assertEqual(spec.argv, (str(script), str(place)))
            self.assertEqual(spec.env["ROSEMARY_PREFIX"], str(root / "wine prefix"))
            self.assertEqual(spec.env["STUDIO_SDL_DRIVER"], "x11")
            self.assertEqual(spec.env["ROSEMARY_BIN"], "/opt/rosemary/bin/rosemary")
            self.assertNotIn("PATH", spec.env)

    def test_desktop_entry_quotes_launcher_paths(self) -> None:
        with tempfile.TemporaryDirectory(prefix="Citric Desktop ") as temporary:
            text = desktop_entry(Path(temporary))
            self.assertIn(f'Exec="{temporary}/scripts/citric"', text)
            self.assertIn("Terminal=false", text)

    def test_desktop_entry_install_and_remove_under_xdg_data_home(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            environment = {"HOME": str(home), "XDG_DATA_HOME": str(home / "data")}
            root = home / "citric"
            destination = install_desktop_entry(root, environment)
            self.assertEqual(destination, desktop_file_path(environment))
            self.assertTrue(destination.is_file())
            self.assertEqual(uninstall_desktop_entry(environment), destination)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
