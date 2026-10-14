from __future__ import annotations

import json
import sys
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gio, Gtk, GLib

from .core import (
    LOGS_DIR,
    ROOT,
    STUDIO_BUNDLE_VERSION,
    build_launch_spec,
    build_rosemary_spec,
    check_studio_update_spec,
    default_config,
    discover_studio_app,
    download_studio_spec,
    install_desktop_entry,
    load_config,
    save_config,
    studio_bundle_version,
)


class CitricWindow(Gtk.ApplicationWindow):
    def __init__(self, application: Gtk.Application) -> None:
        super().__init__(application=application, title="Citric Roblox Studio")
        self.set_default_size(600, 470)
        self.config_error = None
        try:
            self.config = load_config()
        except ValueError as error:
            self.config = default_config()
            self.config_error = str(error)
        self._processes: list[Gio.Subprocess] = []
        self._chooser: Gtk.FileChooserNative | None = None
        self._replacement_dialog: Gtk.Window | None = None
        self._studio_update_version: str | None = None

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        outer.set_margin_top(22)
        outer.set_margin_bottom(20)
        outer.set_margin_start(24)
        outer.set_margin_end(24)
        self.set_child(outer)

        title = Gtk.Label(label="Roblox Studio", xalign=0)
        title.add_css_class("title-1")
        outer.append(title)

        subtitle = Gtk.Label(
            label="Launch Studio through Rosemary or choose a place to open directly.",
            xalign=0,
            wrap=True,
        )
        subtitle.add_css_class("dim-label")
        outer.append(subtitle)

        self.prefix_entry = Gtk.Entry()
        self.prefix_entry.set_text(self.config["prefix"])
        outer.append(self._field_row("Rosemary prefix", self.prefix_entry, self._choose_prefix))

        self.rosemary_entry = Gtk.Entry()
        self.rosemary_entry.set_text(self.config["rosemary_bin"])
        self.rosemary_entry.set_placeholder_text("Detect automatically")
        outer.append(self._field_row("Rosemary executable", self.rosemary_entry, self._choose_rosemary))

        self.studio_entry = Gtk.Entry()
        self.studio_entry.set_text(self.config["studio_app"])
        self.studio_entry.set_placeholder_text("Detect bundle in app/")
        outer.append(self._field_row("Studio bundle", self.studio_entry, self._choose_studio))

        driver_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        driver_label = Gtk.Label(label="SDL driver", xalign=0)
        driver_label.set_size_request(150, -1)
        self.driver_combo = Gtk.ComboBoxText()
        self.driver_combo.append("x11", "X11")
        self.driver_combo.append("wayland", "Wayland (recommended)")
        self.driver_combo.set_active_id(self.config["sdl_driver"])
        driver_row.append(driver_label)
        driver_row.append(self.driver_combo)
        outer.append(driver_row)

        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        launch_button = Gtk.Button(label="Launch Studio")
        launch_button.add_css_class("suggested-action")
        launch_button.connect("clicked", self._launch_studio)
        buttons.append(launch_button)

        place_button = Gtk.Button(label="Open place…")
        place_button.connect("clicked", self._choose_place)
        buttons.append(place_button)
        outer.append(buttons)

        self.build_button = Gtk.Button(label="Download and build Rosemary")
        self.build_button.connect("clicked", self._build_rosemary)
        outer.append(self.build_button)

        self.download_studio_button = Gtk.Button(label="Download and install Roblox Studio")
        self.download_studio_button.connect("clicked", self._download_studio)
        outer.append(self.download_studio_button)

        settings = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        save_button = Gtk.Button(label="Save settings")
        save_button.connect("clicked", self._save_settings)
        settings.append(save_button)

        menu_button = Gtk.Button(label="Add to applications menu")
        menu_button.connect("clicked", self._install_menu_entry)
        settings.append(menu_button)

        logs_button = Gtk.Button(label="Open logs folder")
        logs_button.connect("clicked", self._open_logs)
        settings.append(logs_button)
        outer.append(settings)

        self.status = Gtk.Label(label=self._diagnostic_summary(), xalign=0, wrap=True)
        self.status.add_css_class("dim-label")
        outer.append(self.status)
        self._check_for_studio_update()

    def _field_row(self, title: str, entry: Gtk.Entry, callback) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        label = Gtk.Label(label=title, xalign=0)
        label.set_size_request(150, -1)
        row.append(label)
        entry.set_hexpand(True)
        row.append(entry)
        button = Gtk.Button(label="Choose…")
        button.connect("clicked", callback)
        row.append(button)
        return row

    def _current_config(self) -> dict[str, str]:
        driver = self.driver_combo.get_active_id() or "wayland"
        return {
            **self.config,
            "prefix": self.prefix_entry.get_text().strip(),
            "rosemary_bin": self.rosemary_entry.get_text().strip(),
            "studio_app": self.studio_entry.get_text().strip(),
            "sdl_driver": driver,
        }

    def _save_settings(self, *_args) -> None:
        try:
            self.config = self._current_config()
            saved = save_config(self.config)
            self.status.set_text(f"Settings saved to {saved}")
        except (OSError, ValueError) as error:
            self.status.set_text(str(error))

    def _launch_studio(self, *_args) -> None:
        self._launch(None)

    def _launch(self, place: str | None) -> None:
        try:
            self.config = self._current_config()
            save_config(self.config)
            spec = build_launch_spec(self.config, place)
            launcher = Gio.SubprocessLauncher.new(Gio.SubprocessFlags.NONE)
            for name, value in spec.env.items():
                launcher.setenv(name, value, True)
            process = launcher.spawnv(list(spec.argv))
            self._processes.append(process)
            process.wait_async(None, self._on_process_exit, "launch")
            self.status.set_text("Studio started. This session's log will be saved in logs/.")
        except (OSError, ValueError, GLib.Error) as error:
            self.status.set_text(f"Failed to launch: {error}")

    def _build_rosemary(self, *_args) -> None:
        try:
            spec = build_rosemary_spec(ROOT)
            launcher = Gio.SubprocessLauncher.new(Gio.SubprocessFlags.NONE)
            process = launcher.spawnv(list(spec.argv))
            self._processes.append(process)
            self.build_button.set_sensitive(False)
            process.wait_async(None, self._on_process_exit, "build")
            self.status.set_text("Downloading the pinned Rosemary commit, applying patches and building…")
        except (OSError, GLib.Error) as error:
            self.status.set_text(f"Failed to start the build: {error}")

    def _download_studio(self, *_args) -> None:
        if (
            self._studio_update_version is not None
            and self._version_key(self._studio_update_version) > self._version_key(STUDIO_BUNDLE_VERSION)
        ):
            self.status.set_text(
                f"Roblox Studio {self._studio_update_version} is available. Citric currently installs only the "
                f"validated {STUDIO_BUNDLE_VERSION} build, so this newer version is not installed yet. "
                "Your current Studio bundle has not been changed."
            )
            return
        bundle = ROOT / "app" / "full" / "RobloxStudio.app"
        if studio_bundle_version(bundle) == STUDIO_BUNDLE_VERSION:
            self.studio_entry.set_text(str(bundle))
            try:
                self.config = self._current_config()
                save_config(self.config)
                self.status.set_text(f"Roblox Studio {STUDIO_BUNDLE_VERSION} is already installed and selected.")
            except (OSError, ValueError) as error:
                self.status.set_text(f"Studio is already installed, but settings could not be saved: {error}")
            return
        if bundle.exists() or bundle.is_symlink():
            self._show_studio_replacement_dialog()
            return
        self._start_studio_download(replace=False)

    @staticmethod
    def _version_key(version: str) -> tuple[int, ...]:
        parts = tuple(int(part) for part in version.split("."))
        return parts + (0,) * (4 - len(parts))

    def _check_for_studio_update(self) -> None:
        configured = self.studio_entry.get_text().strip()
        bundle = Path(configured).expanduser() if configured else discover_studio_app(ROOT)
        if bundle is None:
            return
        installed_version = studio_bundle_version(bundle)
        if installed_version is None:
            return
        try:
            spec = check_studio_update_spec(ROOT, installed_version)
            launcher = Gio.SubprocessLauncher.new(
                Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_MERGE
            )
            launcher.set_cwd(str(ROOT))
            process = launcher.spawnv(list(spec.argv))
            self._processes.append(process)
            process.communicate_utf8_async(None, None, self._on_studio_update_check_exit, None)
        except (OSError, GLib.Error):
            # A version check is advisory; it must not prevent launching Studio.
            return

    def _on_studio_update_check_exit(self, process: Gio.Subprocess, result, _user_data) -> None:
        try:
            _success, output, _error_output = process.communicate_utf8_finish(result)
            if not process.get_if_exited() or process.get_exit_status() != 0 or not output:
                return
            result_data = json.loads(output)
            latest_version = result_data.get("latest_version")
            if result_data.get("update_available") is True and isinstance(latest_version, str):
                self._studio_update_version = latest_version
                self.download_studio_button.set_label(f"UPDATE STUDIO NEW VERSION {latest_version}")
        except (GLib.Error, json.JSONDecodeError, AttributeError, TypeError):
            # An unavailable or malformed version response leaves the normal launcher usable.
            pass
        finally:
            if process in self._processes:
                self._processes.remove(process)

    def _show_studio_replacement_dialog(self) -> None:
        dialog = Gtk.Window(title="Replace Roblox Studio bundle")
        dialog.set_transient_for(self)
        dialog.set_modal(True)
        dialog.set_resizable(False)
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.set_margin_top(22)
        content.set_margin_bottom(22)
        content.set_margin_start(24)
        content.set_margin_end(24)
        dialog.set_child(content)
        explanation = Gtk.Label(
            label=(
                f"This downloads the pinned, validated Studio {STUDIO_BUNDLE_VERSION} bundle and replaces "
                "app/full/RobloxStudio.app. Close Studio before continuing."
            ),
            wrap=True,
            xalign=0,
        )
        content.append(explanation)
        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        actions.set_halign(Gtk.Align.END)
        cancel = Gtk.Button(label="Cancel")
        cancel.connect("clicked", self._close_replacement_dialog)
        actions.append(cancel)
        replace_button = Gtk.Button(label="Download and replace")
        replace_button.add_css_class("destructive-action")
        replace_button.connect("clicked", self._confirm_studio_replacement)
        actions.append(replace_button)
        content.append(actions)
        self._replacement_dialog = dialog
        dialog.present()

    def _close_replacement_dialog(self, *_args) -> None:
        if self._replacement_dialog is not None:
            self._replacement_dialog.close()
            self._replacement_dialog = None

    def _confirm_studio_replacement(self, *_args) -> None:
        self._close_replacement_dialog()
        self._start_studio_download(replace=True)

    def _start_studio_download(self, replace: bool) -> None:
        try:
            spec = download_studio_spec(ROOT, replace=replace)
            launcher = Gio.SubprocessLauncher.new(
                Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_MERGE
            )
            launcher.set_cwd(str(ROOT))
            process = launcher.spawnv(list(spec.argv))
            self._processes.append(process)
            self.download_studio_button.set_sensitive(False)
            process.communicate_utf8_async(None, None, self._on_studio_download_exit, None)
            self.status.set_text(
                f"Downloading and verifying the pinned Roblox Studio {STUDIO_BUNDLE_VERSION} bundle…"
            )
        except (OSError, GLib.Error) as error:
            self.status.set_text(f"Failed to start the Studio download: {error}")

    def _on_studio_download_exit(self, process: Gio.Subprocess, result, _user_data) -> None:
        try:
            _success, output, _error_output = process.communicate_utf8_finish(result)
            code = process.get_exit_status() if process.get_if_exited() else "interrupted"
            message = output.strip().splitlines()[-1] if output and output.strip() else ""
            if code == 0:
                bundle = ROOT / "app" / "full" / "RobloxStudio.app"
                self.studio_entry.set_text(str(bundle))
                try:
                    self.config = self._current_config()
                    save_config(self.config)
                    self.status.set_text(message or f"Roblox Studio {STUDIO_BUNDLE_VERSION} is ready to launch.")
                except (OSError, ValueError) as error:
                    self.status.set_text(f"Studio installed, but settings could not be saved: {error}")
            else:
                self.status.set_text(message or f"Studio download failed (exit code {code}).")
        except GLib.Error as error:
            self.status.set_text(f"Could not read the Studio download result: {error}")
        finally:
            self.download_studio_button.set_sensitive(True)
            if process in self._processes:
                self._processes.remove(process)

    def _on_process_exit(self, process: Gio.Subprocess, result, operation) -> None:
        try:
            process.wait_finish(result)
            code = process.get_exit_status() if process.get_if_exited() else "interrupted"
            if operation == "build":
                if code == 0:
                    self.status.set_text("Rosemary built at bin/rosemary. Studio is ready to launch.")
                else:
                    self.status.set_text(f"Rosemary build finished (exit code {code}).")
            else:
                self.status.set_text(f"Studio process finished (exit code {code}).")
        except GLib.Error as error:
            self.status.set_text(f"Could not monitor process exit: {error}")
        finally:
            if operation == "build":
                self.build_button.set_sensitive(True)
            if process in self._processes:
                self._processes.remove(process)

    def _choose_place(self, *_args) -> None:
        chooser = Gtk.FileChooserNative.new(
            "Open place",
            self,
            Gtk.FileChooserAction.OPEN,
            "Open",
            "Cancel",
        )
        file_filter = Gtk.FileFilter()
        file_filter.set_name("Roblox places")
        file_filter.add_pattern("*.rbxl")
        file_filter.add_pattern("*.rbxlx")
        chooser.add_filter(file_filter)
        chooser.connect("response", self._on_place_response)
        self._show_chooser(chooser)

    def _choose_prefix(self, *_args) -> None:
        chooser = Gtk.FileChooserNative.new(
            "Select Rosemary prefix",
            self,
            Gtk.FileChooserAction.SELECT_FOLDER,
            "Select",
            "Cancel",
        )
        chooser.connect("response", self._on_prefix_response)
        self._show_chooser(chooser)

    def _choose_rosemary(self, *_args) -> None:
        chooser = Gtk.FileChooserNative.new(
            "Select Rosemary executable",
            self,
            Gtk.FileChooserAction.OPEN,
            "Select",
            "Cancel",
        )
        chooser.connect("response", self._on_rosemary_response)
        self._show_chooser(chooser)

    def _choose_studio(self, *_args) -> None:
        chooser = Gtk.FileChooserNative.new(
            "Select RobloxStudio.app",
            self,
            Gtk.FileChooserAction.SELECT_FOLDER,
            "Select",
            "Cancel",
        )
        chooser.connect("response", self._on_studio_response)
        self._show_chooser(chooser)

    def _show_chooser(self, chooser: Gtk.FileChooserNative) -> None:
        self._chooser = chooser
        chooser.show()

    def _on_place_response(self, chooser, response) -> None:
        if response == Gtk.ResponseType.ACCEPT:
            file = chooser.get_file()
            path = file.get_path() if file else None
            if path:
                self._launch(path)
        chooser.destroy()
        self._chooser = None

    def _on_prefix_response(self, chooser, response) -> None:
        if response == Gtk.ResponseType.ACCEPT:
            file = chooser.get_file()
            path = file.get_path() if file else None
            if path:
                self.prefix_entry.set_text(path)
        chooser.destroy()
        self._chooser = None

    def _on_rosemary_response(self, chooser, response) -> None:
        if response == Gtk.ResponseType.ACCEPT:
            file = chooser.get_file()
            path = file.get_path() if file else None
            if path:
                self.rosemary_entry.set_text(path)
        chooser.destroy()
        self._chooser = None

    def _on_studio_response(self, chooser, response) -> None:
        if response == Gtk.ResponseType.ACCEPT:
            file = chooser.get_file()
            path = file.get_path() if file else None
            if path:
                self.studio_entry.set_text(path)
        chooser.destroy()
        self._chooser = None

    def _install_menu_entry(self, *_args) -> None:
        try:
            destination = install_desktop_entry()
            self.status.set_text(f"Citric added to the applications menu: {destination}")
        except OSError as error:
            self.status.set_text(f"Failed to install shortcut: {error}")

    def _open_logs(self, *_args) -> None:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        try:
            Gio.AppInfo.launch_default_for_uri(LOGS_DIR.as_uri(), None)
        except GLib.Error as error:
            self.status.set_text(f"Failed to open logs: {error}")

    def _diagnostic_summary(self) -> str:
        from .core import diagnose

        if self.config_error:
            return "Invalid configuration; check the settings and save again: {}".format(self.config_error)
        result = diagnose()
        if result["ready"]:
            return "Ready to launch. Use the fields above to select a different bundle or executable."
        missing = []
        if not result["rosemary_executable"]:
            missing.append("Rosemary has not been built; use the build button")
        if not result["studio_bundle"]:
            missing.append("RobloxStudio.app")
        if not result["launcher_script"]:
            missing.append("launch script")
        return "Setup required: " + ", ".join(missing)


class CitricApplication(Gtk.Application):
    def __init__(self) -> None:
        super().__init__(application_id="org.citric.Launcher", flags=Gio.ApplicationFlags.DEFAULT_FLAGS)

    def do_activate(self) -> None:
        window = self.get_active_window()
        if window is None:
            window = CitricWindow(self)
        window.present()


def run() -> int:
    application = CitricApplication()
    return application.run([sys.argv[0]])


if __name__ == "__main__":
    raise SystemExit(run())
