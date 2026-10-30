#!/usr/bin/env bash
set -u
umask 077
EXPERIMENT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PATCH_MODE=enabled
CITRIC_ROSEMARY_NO_PATCHES="${CITRIC_ROSEMARY_NO_PATCHES:-0}"
case "$CITRIC_ROSEMARY_NO_PATCHES" in
    0) ;;
    1)
        PATCH_MODE=disabled
        ROSEMARY_BIN="$EXPERIMENT_DIR/bin/rosemary-unpatched"
        if [[ ! -x "$ROSEMARY_BIN" ]]; then
            printf 'Unpatched Rosemary not found. Build it with CITRIC_ROSEMARY_NO_PATCHES=1 ./scripts/build-studio.sh, then run again with the same variable.\n' >&2
            exit 127
        fi
        ;;
    *) printf 'CITRIC_ROSEMARY_NO_PATCHES must be 0 or 1.\n' >&2; exit 2 ;;
esac
if [[ "$CITRIC_ROSEMARY_NO_PATCHES" == 0 && -z "${ROSEMARY_BIN:-}" ]]; then
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
    printf 'Rosemary not found. Build it with ./scripts/build-studio.sh or ./scripts/citric build.\n' >&2
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
    sys.exit('No valid Studio bundle found in app/.')
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
        raise ValueError('CFBundleExecutable is not a Studio executable')
    executable = bundle / 'Contents/MacOS' / name
    if not executable.is_file():
        raise ValueError('executable missing from bundle')
except (OSError, ValueError) as error:
    sys.exit(f'Invalid bundle: {bundle}: {error}')
PYVALIDATE
if [[ $? -ne 0 ]]; then exit 2; fi
python3 "$EXPERIMENT_DIR/scripts/patch-color-dialog.py" "$STUDIO_APP" || exit 2
export ROSEMARY_PREFIX="${ROSEMARY_PREFIX:-$HOME/rosemary-studio-prefix}"
export ROSEMARY_PREFIX_HOME=prefix
export ROSEMARY_ROOTFS_CACHE="${ROSEMARY_ROOTFS_CACHE:-$EXPERIMENT_DIR/downloads/darwin-cache}"
export ROSEMARY_PREFIX_SETUP="${ROSEMARY_PREFIX_SETUP:-download}"
export ROSEMARY_EXE="$ROSEMARY_BIN"
STUDIO_SDL_DRIVER="${STUDIO_SDL_DRIVER:-wayland}"
export SDL_VIDEODRIVER="$STUDIO_SDL_DRIVER"
SDL_MOUSE_RELATIVE_SYSTEM_SCALE="${SDL_MOUSE_RELATIVE_SYSTEM_SCALE:-0}"
export SDL_MOUSE_RELATIVE_SYSTEM_SCALE
SOURCE_LC_ALL="${LC_ALL-<unset>}"
SOURCE_LC_NUMERIC="${LC_NUMERIC-<unset>}"
unset LC_ALL
export LC_NUMERIC=C
ROSEMARY_PERF_TRACE="${ROSEMARY_PERF_TRACE:-1}"
export ROSEMARY_PERF_TRACE
PLUGIN_PATCH_RESULT="$(python3 "$EXPERIMENT_DIR/scripts/patch_plugin_compatibility.py" "$ROSEMARY_PREFIX")" || exit 2
LOG_NAME="${STUDIO_LOG_NAME:-run-$(date +%Y%m%dT%H%M%S)-$$}"
if [[ ! "$LOG_NAME" =~ ^[a-zA-Z0-9_.-]+$ ]]; then exit 2; fi
LOG_PATH="$EXPERIMENT_DIR/logs/$LOG_NAME.log"
if [[ -e "$LOG_PATH" ]]; then
    printf 'Log already exists; use a different STUDIO_LOG_NAME: %s\n' "$LOG_PATH" >&2
    exit 2
fi
mkdir -p "$EXPERIMENT_DIR/logs" || exit 1
# Developer-only diagnostics are opt-in for each launcher invocation.
# Legacy marker files intentionally no longer activate a capture.
MEMORY_TRACE_MODE="${STUDIO_MEMORY_TRACE:-0}"
case "$MEMORY_TRACE_MODE" in
    0|1|detailed) ;;
    *) printf 'STUDIO_MEMORY_TRACE must be 0, 1, or detailed.\n' >&2; exit 2 ;;
esac
MEMORY_TRACE_PID=""
MEMORY_TRACE_PATH=""
MEMORY_TRACE_DETAILED_REQUESTED=false
ROSEMARY_VM_TRACE_REQUESTED=false
if [[ "$MEMORY_TRACE_MODE" != "0" ]]; then
    MEMORY_TRACE_PATH="$EXPERIMENT_DIR/logs/$LOG_NAME.memory.jsonl"
    if [[ -e "$MEMORY_TRACE_PATH" ]]; then
        printf 'Memory trace already exists; skipping: %s\n' "$MEMORY_TRACE_PATH" >&2
        MEMORY_TRACE_PATH=""
    else
        MEMORY_TRACE_OPTIONS=()
        ROSEMARY_VM_TRACE_ENV=()
        if [[ "$MEMORY_TRACE_MODE" == "detailed" ]]; then
            MEMORY_TRACE_OPTIONS+=(--detailed-vmas)
            MEMORY_TRACE_DETAILED_REQUESTED=true
            ROSEMARY_VM_TRACE_ENV+=(ROSEMARY_TRACE_VM=1)
            ROSEMARY_VM_TRACE_REQUESTED=true
        elif [[ "${ROSEMARY_TRACE_VM+x}" ]]; then
            ROSEMARY_VM_TRACE_REQUESTED=true
        fi
        python3 "$EXPERIMENT_DIR/scripts/trace-studio-memory.py" \
            --parent-pid "$$" \
            --launch-executable "$ROSEMARY_BIN" \
            --output "$MEMORY_TRACE_PATH" \
            --studio-log "$LOG_PATH" \
            --interval "${STUDIO_MEMORY_TRACE_INTERVAL:-5}" \
            "${MEMORY_TRACE_OPTIONS[@]}" \
            2> "$MEMORY_TRACE_PATH.stderr" &
        MEMORY_TRACE_PID=$!
        for _ in {1..20}; do
            [[ -s "$MEMORY_TRACE_PATH" ]] && break
            sleep 0.1
        done
        if [[ ! -s "$MEMORY_TRACE_PATH" ]]; then
            kill -TERM "$MEMORY_TRACE_PID" 2>/dev/null || true
            wait "$MEMORY_TRACE_PID" 2>/dev/null || true
            printf 'Memory tracer did not start; see %s.stderr\n' "$MEMORY_TRACE_PATH" >&2
            MEMORY_TRACE_PID=""
            MEMORY_TRACE_PATH=""
        fi
    fi
fi
ROSEMARY_OPTIONS=()
if [[ "${STUDIO_OBJC_DEBUG:-0}" == "1" ]]; then
    ROSEMARY_OPTIONS+=(--objc-debug)
fi
if [[ -n "$MEMORY_TRACE_PATH" ]]; then
    MEMORY_TRACE_ENABLED=true
    MIMALLOC_HOST_STATS_REQUESTED=true
    MIMALLOC_GUEST_STATS_REQUESTED=true
    ALLOCATOR_INTERPOSE_TRACE_REQUESTED=true
    MEMORY_TRACE_GUEST_ENVIRON="${ROSEMARY_ENVIRON-}"
    if [[ -n "$MEMORY_TRACE_GUEST_ENVIRON" ]]; then
        MEMORY_TRACE_GUEST_ENVIRON+=$'\n'
    fi
    MEMORY_TRACE_GUEST_ENVIRON+="MIMALLOC_SHOW_STATS"
    RUN_COMMAND=(
        env
        MIMALLOC_SHOW_STATS=1
        ROSEMARY_TRACE_INTERPOSE=1
        "${ROSEMARY_VM_TRACE_ENV[@]}"
        ROSEMARY_ENVIRON="$MEMORY_TRACE_GUEST_ENVIRON"
        "$ROSEMARY_BIN" run
        "${ROSEMARY_OPTIONS[@]}"
        "$STUDIO_APP"
        "$@"
    )
else
    MEMORY_TRACE_ENABLED=false
    MIMALLOC_HOST_STATS_REQUESTED=false
    MIMALLOC_GUEST_STATS_REQUESTED=false
    ALLOCATOR_INTERPOSE_TRACE_REQUESTED=false
    if [[ "${ROSEMARY_TRACE_VM+x}" ]]; then
        ROSEMARY_VM_TRACE_REQUESTED=true
    fi
    RUN_COMMAND=(
        "$ROSEMARY_BIN" run
        "${ROSEMARY_OPTIONS[@]}"
        "$STUDIO_APP"
        "$@"
    )
fi
if [[ -n "${STUDIO_TIMEOUT:-}" ]]; then
    RUN_COMMAND=(timeout --signal=TERM --kill-after=10s "$STUDIO_TIMEOUT" "${RUN_COMMAND[@]}")
fi
PATCH_MODE=enabled
if [[ "$CITRIC_ROSEMARY_NO_PATCHES" == 1 ]]; then
    PATCH_MODE=disabled
fi
{
    printf 'date='; date --iso-8601=seconds
    printf 'prefix=%s\napp=%s\nrosemary=%s\nrosemary_citric_patches=%s\n' "$ROSEMARY_PREFIX" "$STUDIO_APP" "$ROSEMARY_BIN" "$PATCH_MODE"
    printf 'rosemary_sha256=%s\n' "$(sha256sum -- "$ROSEMARY_BIN" | cut -d ' ' -f 1)"
    printf 'sdl_video_driver=%s\nperf_trace=%s\n' "${SDL_VIDEODRIVER:-auto}" "$ROSEMARY_PERF_TRACE"
    printf 'locale_source_lc_all=%s\nlocale_source_lc_numeric=%s\n' "$SOURCE_LC_ALL" "$SOURCE_LC_NUMERIC"
    printf 'locale_lc_all=%s\nlocale_lc_numeric=%s\n' "${LC_ALL-<unset>}" "$LC_NUMERIC"
    printf 'plugin_compatibility_patch=%s\n' "$PLUGIN_PATCH_RESULT"
    printf 'memory_trace=%s\nmimalloc_host_stats_requested=%s\nmimalloc_guest_stats_requested=%s\nallocator_interpose_trace_requested=%s\n' \
        "$MEMORY_TRACE_ENABLED" "$MIMALLOC_HOST_STATS_REQUESTED" "$MIMALLOC_GUEST_STATS_REQUESTED" "$ALLOCATOR_INTERPOSE_TRACE_REQUESTED"
    printf 'memory_trace_mode=%s\n' "$MEMORY_TRACE_MODE"
    printf 'memory_trace_detailed_vmas_requested=%s\n' "$MEMORY_TRACE_DETAILED_REQUESTED"
    printf 'rosemary_vm_trace_requested=%s\n' "$ROSEMARY_VM_TRACE_REQUESTED"
    printf 'command='; printf '%q ' "${RUN_COMMAND[@]}"; printf '\n'
} > "$EXPERIMENT_DIR/logs/$LOG_NAME.meta" || exit 1
ulimit -c 0
printf 'Running %s\nLog: %s\n' "$STUDIO_APP" "$LOG_PATH"
if [[ -n "$MEMORY_TRACE_PATH" ]]; then
    printf 'Memory trace: %s\n' "$MEMORY_TRACE_PATH"
fi
"${RUN_COMMAND[@]}" > "$LOG_PATH" 2>&1
RUN_EXIT_CODE=$?
if [[ -n "$MEMORY_TRACE_PID" ]]; then
    kill -TERM "$MEMORY_TRACE_PID" 2>/dev/null || true
    wait "$MEMORY_TRACE_PID" 2>/dev/null || true
fi
POST_PLUGIN_PATCH_RESULT="$(python3 "$EXPERIMENT_DIR/scripts/patch_plugin_compatibility.py" "$ROSEMARY_PREFIX" 2>&1)"
POST_PLUGIN_PATCH_EXIT=$?
printf 'post_exit_plugin_patch_exit=%s\npost_exit_plugin_patch_result=%s\n' \
    "$POST_PLUGIN_PATCH_EXIT" "$POST_PLUGIN_PATCH_RESULT" >> "$EXPERIMENT_DIR/logs/$LOG_NAME.meta"
if [[ -n "$MEMORY_TRACE_PATH" ]]; then
    MEMORY_DIAGNOSTIC_SUMMARY="$(python3 "$EXPERIMENT_DIR/scripts/summarize-memory-diagnostics.py" "$LOG_PATH")" || exit 1
    printf '%s\n' "$MEMORY_DIAGNOSTIC_SUMMARY" >> "$EXPERIMENT_DIR/logs/$LOG_NAME.meta"
fi
printf '%s\n' "$RUN_EXIT_CODE" > "$EXPERIMENT_DIR/logs/$LOG_NAME.exit-code"
printf 'Exit code: %s\n' "$RUN_EXIT_CODE"
exit "$RUN_EXIT_CODE"
