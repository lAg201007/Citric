#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
VINEGAR_ROOT="${VINEGAR_ROOT:-$HOME/.var/app/org.vinegarhq.Vinegar/data/vinegar}"
VINEGAR_PREFIX="${VINEGAR_PREFIX:-$VINEGAR_ROOT/prefixes/studio}"
VINEGAR_VERSIONS="${VINEGAR_VERSIONS:-$VINEGAR_ROOT/versions}"
CITRIC_MCP_SCRIPT="${CITRIC_MCP_SCRIPT:-$REPO_ROOT/scripts/run-mcp.sh}"
BACKEND="${ROBLOX_STUDIO_BACKEND:-auto}"
DETECT_SECONDS="${ROBLOX_STUDIO_DETECT_SECONDS:-10}"
DEFAULT_BACKEND="${ROBLOX_STUDIO_DEFAULT_BACKEND:-citric}"

has_process_fragment() {
    local fragment="$1"
    local command_line
    local cmdline_path
    local process_id
    local process_executable
    for cmdline_path in /proc/[0-9]*/cmdline; do
        [[ -r "$cmdline_path" ]] || continue
        process_id="${cmdline_path#/proc/}"
        process_id="${process_id%%/*}"
        process_executable="$(readlink "/proc/$process_id/exe" 2>/dev/null || true)"
        case "$process_executable" in
            */bash|*/dash|*/sh|*/sleep|*/timeout|*/codex|*/codex-linux-sandbox|*/python*|*/awk|*/tr)
                continue
                ;;
        esac
        command_line="$(tr '\0' ' ' < "$cmdline_path" 2>/dev/null || true)"
        if [[ "$command_line" == *"$fragment"* ]]; then
            return 0
        fi
    done
    return 1
}

detect_backend() {
    local vinegar_active=0
    local citric_active=0
    if has_process_fragment "RobloxStudioBeta.exe"; then
        vinegar_active=1
    fi
    if has_process_fragment "$REPO_ROOT/app/full/RobloxStudio.app" || has_process_fragment "rosemary-studio-prefix"; then
        citric_active=1
    fi
    if (( vinegar_active && citric_active )); then
        printf 'Both Vinegar and Citric Studio processes are active; set ROBLOX_STUDIO_BACKEND explicitly.\n' >&2
        exit 3
    fi
    if (( vinegar_active )); then
        printf '%s\n' vinegar
        return
    fi
    if (( citric_active )); then
        printf '%s\n' citric
        return
    fi
    return 1
}

find_latest_vinegar_mcp() {
    local candidate
    local latest=""
    local latest_modified=0
    local modified
    while IFS= read -r -d '' candidate; do
        modified="$(stat -c '%Y' "$candidate")"
        if (( modified >= latest_modified )); then
            latest_modified="$modified"
            latest="$candidate"
        fi
    done < <(find "$VINEGAR_VERSIONS" -type f -name StudioMCP.exe -print0 2>/dev/null)
    [[ -n "$latest" ]] && printf '%s\n' "$latest"
}

find_latest_vinegar_wine() {
    local candidate
    local latest=""
    local latest_modified=0
    local modified
    while IFS= read -r -d '' candidate; do
        modified="$(stat -c '%Y' "$candidate")"
        if (( modified >= latest_modified )); then
            latest_modified="$modified"
            latest="$candidate"
        fi
    done < <(find "$VINEGAR_ROOT" -path '*/bin/wine' -type f -perm -u+x -print0 2>/dev/null)
    [[ -n "$latest" ]] && printf '%s\n' "$latest"
}

run_vinegar() {
    local wine_bin="${WINE_BIN:-$(find_latest_vinegar_wine)}"
    local studio_mcp
    studio_mcp="${VINEGAR_STUDIO_MCP:-$(find_latest_vinegar_mcp)}"
    if [[ -z "$wine_bin" ]]; then
        wine_bin="$(command -v wine || true)"
    fi
    if [[ ! -x "$wine_bin" ]]; then
        printf 'Wine not found; set WINE_BIN to the Vinegar Wine executable.\n' >&2
        exit 127
    fi
    if [[ -z "$studio_mcp" || ! -f "$studio_mcp" ]]; then
        printf 'Vinegar StudioMCP not found under %s.\n' "$VINEGAR_VERSIONS" >&2
        exit 2
    fi
    export WINEPREFIX="$VINEGAR_PREFIX"
    if [[ -z "${WINESERVER:-}" && -x "$(dirname -- "$wine_bin")/wineserver" ]]; then
        export WINESERVER="$(dirname -- "$wine_bin")/wineserver"
    fi
    exec "$wine_bin" "$studio_mcp" "$@"
}

run_citric() {
    if [[ ! -x "$CITRIC_MCP_SCRIPT" ]]; then
        printf 'Citric MCP launcher not found: %s\n' "$CITRIC_MCP_SCRIPT" >&2
        exit 2
    fi
    exec "$CITRIC_MCP_SCRIPT" "$@"
}

case "$BACKEND" in
    auto)
        selected_backend=""
        deadline=$((SECONDS + DETECT_SECONDS))
        while (( SECONDS < deadline )); do
            selected_backend="$(detect_backend || true)"
            [[ -n "$selected_backend" ]] && break
            sleep 0.25
        done
        if [[ -n "$selected_backend" ]]; then
            BACKEND="$selected_backend"
        else
            BACKEND="$DEFAULT_BACKEND"
        fi
        ;;
    vinegar|citric)
        ;;
    *)
        printf 'ROBLOX_STUDIO_BACKEND must be auto, vinegar, or citric.\n' >&2
        exit 2
        ;;
esac

case "$BACKEND" in
    vinegar) run_vinegar "$@" ;;
    citric) run_citric "$@" ;;
esac
