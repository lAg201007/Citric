from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from .core import (
    ROOT,
    build_launch_spec,
    build_rosemary_spec,
    diagnose,
    format_command,
    install_desktop_entry,
    load_config,
    uninstall_desktop_entry,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="citric", description="Launcher local do Roblox Studio pelo Rosemary")
    commands = parser.add_subparsers(dest="command")

    build = commands.add_parser("build", help="baixar a base Rosemary, aplicar patches e compilar")
    build_modes = build.add_mutually_exclusive_group()
    build_modes.add_argument("--check-only", action="store_true", help="validar fetch e patches sem compilar")
    build_modes.add_argument("--build-only", action="store_true", help="compilar sem substituir bin/rosemary")

    launch = commands.add_parser("launch", help="iniciar o Studio")
    launch.add_argument("place", nargs="?", help="arquivo .rbxl ou .rbxlx")
    launch.add_argument("--dry-run", action="store_true", help="mostrar o comando sem iniciar o Studio")

    commands.add_parser("install-desktop", help="adicionar Citric ao menu de aplicativos")
    commands.add_parser("uninstall-desktop", help="remover Citric do menu de aplicativos")
    commands.add_parser("diagnose", help="verificar os arquivos necessários sem abrir o Studio")
    return parser


def run_gui() -> int:
    try:
        import gi

        gi.require_version("Gtk", "4.0")
        from .app import run
    except (ImportError, ValueError) as error:
        print(f"Não consegui carregar a interface GTK 4: {error}", file=sys.stderr)
        return 1
    return run()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        return run_gui()
    if args.command == "diagnose":
        result = diagnose()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ready"] else 1
    if args.command == "install-desktop":
        print(install_desktop_entry())
        return 0
    if args.command == "uninstall-desktop":
        print(uninstall_desktop_entry())
        return 0
    if args.command == "build":
        try:
            spec = build_rosemary_spec(ROOT, args.check_only, args.build_only)
        except FileNotFoundError as error:
            print(error, file=sys.stderr)
            return 1
        return subprocess.run(spec.argv, cwd=ROOT, check=False).returncode
    if args.command == "launch":
        try:
            spec = build_launch_spec(load_config(), args.place)
        except (FileNotFoundError, ValueError) as error:
            print(error, file=sys.stderr)
            return 1
        if args.dry_run:
            print(json.dumps({"command": format_command(spec.argv), "environment": spec.env}, ensure_ascii=False, indent=2))
            return 0
        environment = os.environ.copy()
        environment.update(spec.env)
        return subprocess.run(spec.argv, env=environment, cwd=ROOT, check=False).returncode
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
