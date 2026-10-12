#!/usr/bin/env bash
set -u
umask 077
EXPERIMENT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -z "${ROSEMARY_BIN:-}" ]]; then
    BUNDLED_ROSEMARY="$EXPERIMENT_DIR/bin/rosemary"
    BUILT_ROSEMARY="$EXPERIMENT_DIR/target/release/rosemary"
    if [[ -x "$BUNDLED_ROSEMARY" ]]; then
        ROSEMARY_BIN="$BUNDLED_ROSEMARY"
    elif [[ -x "$BUILT_ROSEMARY" ]]; then
        ROSEMARY_BIN="$BUILT_ROSEMARY"
    else
        ROSEMARY_BIN="$(command -v rosemary || true)"
    fi
fi
if [[ ! -x "$ROSEMARY_BIN" ]]; then
    ROSEMARY_BIN="$HOME/rosemary/target/release/rosemary"
fi
if [[ ! -x "$ROSEMARY_BIN" ]]; then
    printf 'Rosemary não encontrado. Compile com ./scripts/build-studio.sh ou ./scripts/citric build.\n' >&2
    exit 127
fi
if [[ -z "${STUDIO_APP:-}" ]]; then
    STUDIO_APP="$(python3 - "$EXPERIMENT_DIR/app" <<'PYAPP'
import pathlib, plistlib, sys
candidates = []
for plist in pathlib.Path(sys.argv[1]).rglob('Contents/Info.plist'):
    try:
        info = plistlib.loads(plist.read_bytes())
        executable = info.get('CFBundleExecutable', '')
        if executable in ('RobloxStudio', 'RobloxStudioInstaller') and (plist.parent / 'MacOS' / executable).is_file():
            candidates.append((executable != 'RobloxStudio', str(plist.parent.parent)))
    except (OSError, ValueError):
        continue
if not candidates:
    sys.exit('Nenhum bundle Studio válido encontrado em app/.')
print(sorted(candidates)[0][1])
PYAPP
)" || exit 2
fi
python3 - "$STUDIO_APP" <<'PYVALIDATE'
import pathlib, plistlib, sys
bundle = pathlib.Path(sys.argv[1])
try:
    info = plistlib.loads((bundle / 'Contents/Info.plist').read_bytes())
    name = info.get('CFBundleExecutable', '')
    if name not in ('RobloxStudio', 'RobloxStudioInstaller'):
        raise ValueError('CFBundleExecutable não é do Studio')
    executable = bundle / 'Contents/MacOS' / name
    if not executable.is_file():
        raise ValueError('executável ausente no bundle')
except (OSError, ValueError) as error:
    sys.exit(f'Bundle inválido: {bundle}: {error}')
PYVALIDATE
if [[ $? -ne 0 ]]; then exit 2; fi
python3 "$EXPERIMENT_DIR/scripts/patch-color-dialog.py" "$STUDIO_APP" || exit 2
export ROSEMARY_PREFIX="${ROSEMARY_PREFIX:-$HOME/rosemary-studio-prefix}"
export ROSEMARY_PREFIX_HOME=prefix
export ROSEMARY_ROOTFS_CACHE="${ROSEMARY_ROOTFS_CACHE:-$EXPERIMENT_DIR/downloads/darwin-cache}"
export ROSEMARY_PREFIX_SETUP="${ROSEMARY_PREFIX_SETUP:-download}"
export ROSEMARY_EXE="$ROSEMARY_BIN"
STUDIO_SDL_DRIVER="${STUDIO_SDL_DRIVER:-x11}"
export SDL_VIDEODRIVER="$STUDIO_SDL_DRIVER"
SDL_MOUSE_RELATIVE_SYSTEM_SCALE="${SDL_MOUSE_RELATIVE_SYSTEM_SCALE:-0}"
export SDL_MOUSE_RELATIVE_SYSTEM_SCALE
SOURCE_LC_ALL="${LC_ALL-<unset>}"
SOURCE_LC_NUMERIC="${LC_NUMERIC-<unset>}"
unset LC_ALL
export LC_NUMERIC=C
PLUGIN_PATCH_RESULT="$(python3 "$EXPERIMENT_DIR/scripts/patch_blender_animations.py" "$ROSEMARY_PREFIX")" || exit 2
LOG_NAME="${STUDIO_LOG_NAME:-run-$(date +%Y%m%dT%H%M%S)-$$}"
if [[ ! "$LOG_NAME" =~ ^[a-zA-Z0-9_.-]+$ ]]; then exit 2; fi
LOG_PATH="$EXPERIMENT_DIR/logs/$LOG_NAME.log"
if [[ -e "$LOG_PATH" ]]; then
    printf 'Log já existe, use outro STUDIO_LOG_NAME: %s\n' "$LOG_PATH" >&2
    exit 2
fi
mkdir -p "$EXPERIMENT_DIR/logs" || exit 1
ROSEMARY_OPTIONS=()
if [[ "${STUDIO_OBJC_DEBUG:-0}" == "1" ]]; then
    ROSEMARY_OPTIONS+=(--objc-debug)
fi
RUN_COMMAND=("$ROSEMARY_BIN" run "${ROSEMARY_OPTIONS[@]}" "$STUDIO_APP" "$@")
if [[ -n "${STUDIO_TIMEOUT:-}" ]]; then
    RUN_COMMAND=(timeout --signal=TERM --kill-after=10s "$STUDIO_TIMEOUT" "${RUN_COMMAND[@]}")
fi
{
    printf 'date='; date --iso-8601=seconds
    printf 'prefix=%s\napp=%s\nrosemary=%s\n' "$ROSEMARY_PREFIX" "$STUDIO_APP" "$ROSEMARY_BIN"
    printf 'sdl_video_driver=%s\n' "${SDL_VIDEODRIVER:-auto}"
    printf 'locale_source_lc_all=%s\nlocale_source_lc_numeric=%s\n' "$SOURCE_LC_ALL" "$SOURCE_LC_NUMERIC"
    printf 'locale_lc_all=%s\nlocale_lc_numeric=%s\n' "${LC_ALL-<unset>}" "$LC_NUMERIC"
    printf 'plugin_compatibility_patch=%s\n' "$PLUGIN_PATCH_RESULT"
    printf 'command='; printf '%q ' "${RUN_COMMAND[@]}"; printf '\n'
} > "$EXPERIMENT_DIR/logs/$LOG_NAME.meta" || exit 1
ulimit -c 0
printf 'Executando %s\nLog: %s\n' "$STUDIO_APP" "$LOG_PATH"
"${RUN_COMMAND[@]}" > "$LOG_PATH" 2>&1
RUN_EXIT_CODE=$?
POST_PLUGIN_PATCH_RESULT="$(python3 "$EXPERIMENT_DIR/scripts/patch_blender_animations.py" "$ROSEMARY_PREFIX" 2>&1)"
POST_PLUGIN_PATCH_EXIT=$?
printf 'post_exit_plugin_patch_exit=%s\npost_exit_plugin_patch_result=%s\n' \
    "$POST_PLUGIN_PATCH_EXIT" "$POST_PLUGIN_PATCH_RESULT" >> "$EXPERIMENT_DIR/logs/$LOG_NAME.meta"
printf '%s\n' "$RUN_EXIT_CODE" > "$EXPERIMENT_DIR/logs/$LOG_NAME.exit-code"
printf 'Código de saída: %s\n' "$RUN_EXIT_CODE"
exit "$RUN_EXIT_CODE"
