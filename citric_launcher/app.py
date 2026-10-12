from __future__ import annotations

import sys

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gio, Gtk, GLib

from .core import LOGS_DIR, ROOT, build_launch_spec, build_rosemary_spec, default_config, install_desktop_entry, load_config, save_config


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
            label="Abra o Studio pelo Rosemary ou escolha uma place para iniciar direto nela.",
            xalign=0,
            wrap=True,
        )
        subtitle.add_css_class("dim-label")
        outer.append(subtitle)

        self.prefix_entry = Gtk.Entry()
        self.prefix_entry.set_text(self.config["prefix"])
        outer.append(self._field_row("Prefixo Rosemary", self.prefix_entry, self._choose_prefix))

        self.rosemary_entry = Gtk.Entry()
        self.rosemary_entry.set_text(self.config["rosemary_bin"])
        self.rosemary_entry.set_placeholder_text("Detectar automaticamente")
        outer.append(self._field_row("Executável Rosemary", self.rosemary_entry, self._choose_rosemary))

        self.studio_entry = Gtk.Entry()
        self.studio_entry.set_text(self.config["studio_app"])
        self.studio_entry.set_placeholder_text("Detectar bundle em app/")
        outer.append(self._field_row("Bundle do Studio", self.studio_entry, self._choose_studio))

        driver_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        driver_label = Gtk.Label(label="Driver SDL", xalign=0)
        driver_label.set_size_request(150, -1)
        self.driver_combo = Gtk.ComboBoxText()
        self.driver_combo.append("x11", "X11 (recomendado)")
        self.driver_combo.append("wayland", "Wayland")
        self.driver_combo.set_active_id(self.config["sdl_driver"])
        driver_row.append(driver_label)
        driver_row.append(self.driver_combo)
        outer.append(driver_row)

        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        launch_button = Gtk.Button(label="Abrir Studio")
        launch_button.add_css_class("suggested-action")
        launch_button.connect("clicked", self._launch_studio)
        buttons.append(launch_button)

        place_button = Gtk.Button(label="Abrir place…")
        place_button.connect("clicked", self._choose_place)
        buttons.append(place_button)
        outer.append(buttons)

        self.build_button = Gtk.Button(label="Baixar patches e compilar Rosemary")
        self.build_button.connect("clicked", self._build_rosemary)
        outer.append(self.build_button)

        settings = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        save_button = Gtk.Button(label="Salvar configurações")
        save_button.connect("clicked", self._save_settings)
        settings.append(save_button)

        menu_button = Gtk.Button(label="Adicionar ao menu de aplicativos")
        menu_button.connect("clicked", self._install_menu_entry)
        settings.append(menu_button)

        logs_button = Gtk.Button(label="Abrir pasta de logs")
        logs_button.connect("clicked", self._open_logs)
        settings.append(logs_button)
        outer.append(settings)

        self.status = Gtk.Label(label=self._diagnostic_summary(), xalign=0, wrap=True)
        self.status.add_css_class("dim-label")
        outer.append(self.status)

    def _field_row(self, title: str, entry: Gtk.Entry, callback) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        label = Gtk.Label(label=title, xalign=0)
        label.set_size_request(150, -1)
        row.append(label)
        entry.set_hexpand(True)
        row.append(entry)
        button = Gtk.Button(label="Escolher…")
        button.connect("clicked", callback)
        row.append(button)
        return row

    def _current_config(self) -> dict[str, str]:
        driver = self.driver_combo.get_active_id() or "x11"
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
            self.status.set_text(f"Configurações salvas em {saved}")
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
            self.status.set_text("Studio iniciado. O log desta sessão será salvo em logs/.")
        except (OSError, ValueError, GLib.Error) as error:
            self.status.set_text(f"Falha ao iniciar: {error}")

    def _build_rosemary(self, *_args) -> None:
        try:
            spec = build_rosemary_spec(ROOT)
            launcher = Gio.SubprocessLauncher.new(Gio.SubprocessFlags.NONE)
            process = launcher.spawnv(list(spec.argv))
            self._processes.append(process)
            self.build_button.set_sensitive(False)
            process.wait_async(None, self._on_process_exit, "build")
            self.status.set_text("Baixando o commit Rosemary fixado, aplicando patches e compilando…")
        except (OSError, GLib.Error) as error:
            self.status.set_text(f"Falha ao iniciar o build: {error}")

    def _on_process_exit(self, process: Gio.Subprocess, result, operation) -> None:
        try:
            process.wait_finish(result)
            code = process.get_exit_status() if process.get_if_exited() else "interrompido"
            if operation == "build":
                if code == 0:
                    self.status.set_text("Rosemary compilado em bin/rosemary. O Studio está pronto para abrir.")
                else:
                    self.status.set_text(f"Build do Rosemary terminou (código {code}).")
            else:
                self.status.set_text(f"Processo do Studio terminou (código {code}).")
        except GLib.Error as error:
            self.status.set_text(f"Não consegui observar a saída do processo: {error}")
        finally:
            if operation == "build":
                self.build_button.set_sensitive(True)
            if process in self._processes:
                self._processes.remove(process)

    def _choose_place(self, *_args) -> None:
        chooser = Gtk.FileChooserNative.new(
            "Abrir place",
            self,
            Gtk.FileChooserAction.OPEN,
            "Abrir",
            "Cancelar",
        )
        file_filter = Gtk.FileFilter()
        file_filter.set_name("Places Roblox")
        file_filter.add_pattern("*.rbxl")
        file_filter.add_pattern("*.rbxlx")
        chooser.add_filter(file_filter)
        chooser.connect("response", self._on_place_response)
        self._show_chooser(chooser)

    def _choose_prefix(self, *_args) -> None:
        chooser = Gtk.FileChooserNative.new(
            "Selecionar prefixo Rosemary",
            self,
            Gtk.FileChooserAction.SELECT_FOLDER,
            "Selecionar",
            "Cancelar",
        )
        chooser.connect("response", self._on_prefix_response)
        self._show_chooser(chooser)

    def _choose_rosemary(self, *_args) -> None:
        chooser = Gtk.FileChooserNative.new(
            "Selecionar executável Rosemary",
            self,
            Gtk.FileChooserAction.OPEN,
            "Selecionar",
            "Cancelar",
        )
        chooser.connect("response", self._on_rosemary_response)
        self._show_chooser(chooser)

    def _choose_studio(self, *_args) -> None:
        chooser = Gtk.FileChooserNative.new(
            "Selecionar RobloxStudio.app",
            self,
            Gtk.FileChooserAction.SELECT_FOLDER,
            "Selecionar",
            "Cancelar",
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
            self.status.set_text(f"Citric adicionado ao menu: {destination}")
        except OSError as error:
            self.status.set_text(f"Falha ao instalar atalho: {error}")

    def _open_logs(self, *_args) -> None:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        try:
            Gio.AppInfo.launch_default_for_uri(LOGS_DIR.as_uri(), None)
        except GLib.Error as error:
            self.status.set_text(f"Falha ao abrir logs: {error}")

    def _diagnostic_summary(self) -> str:
        from .core import diagnose

        if self.config_error:
            return "Configuração inválida; confira as opções e salve novamente: {}".format(self.config_error)
        result = diagnose()
        if result["ready"]:
            return "Pronto para iniciar. Use Editar se precisar apontar para outro bundle ou executável."
        missing = []
        if not result["rosemary_executable"]:
            missing.append("Rosemary não compilado; use o botão de build")
        if not result["studio_bundle"]:
            missing.append("RobloxStudio.app")
        if not result["launcher_script"]:
            missing.append("script de launch")
        return "Falta configurar: " + ", ".join(missing)


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
