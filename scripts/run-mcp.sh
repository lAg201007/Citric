#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"

if [[ -z "${ROSEMARY_BIN:-}" ]]; then
    if [[ -x "$REPO_ROOT/bin/rosemary" ]]; then
        ROSEMARY_BIN="$REPO_ROOT/bin/rosemary"
    elif [[ -x "$REPO_ROOT/target/release/rosemary" ]]; then
        ROSEMARY_BIN="$REPO_ROOT/target/release/rosemary"
    else
        ROSEMARY_BIN="$(command -v rosemary || true)"
    fi
fi
if [[ ! -x "$ROSEMARY_BIN" && -x "$HOME/rosemary/target/release/rosemary" ]]; then
    ROSEMARY_BIN="$HOME/rosemary/target/release/rosemary"
fi
if [[ ! -x "$ROSEMARY_BIN" ]]; then
    printf 'Rosemary not found. Build it with ./scripts/build-studio.sh.\n' >&2
    exit 127
fi

if [[ -z "${STUDIO_MCP:-}" ]]; then
    latest_mcp=""
    latest_modified=0
    while IFS= read -r -d '' candidate; do
        modified="$(stat -c '%Y' "$candidate")"
        if (( modified >= latest_modified )); then
            latest_modified="$modified"
            latest_mcp="$candidate"
        fi
    done < <(find "$REPO_ROOT/app" -type f -path '*/Contents/MacOS/StudioMCP' -print0)
    STUDIO_MCP="$latest_mcp"
fi
if [[ -z "$STUDIO_MCP" || ! -f "$STUDIO_MCP" ]]; then
    printf 'StudioMCP not found: %s\n' "$STUDIO_MCP" >&2
    exit 2
fi

export ROSEMARY_BIN
export ROSEMARY_EXE="${ROSEMARY_EXE:-$ROSEMARY_BIN}"
export ROSEMARY_PREFIX="${ROSEMARY_PREFIX:-$HOME/rosemary-studio-prefix}"
export ROSEMARY_PREFIX_HOME="${ROSEMARY_PREFIX_HOME:-prefix}"
export ROSEMARY_ROOTFS_CACHE="${ROSEMARY_ROOTFS_CACHE:-$REPO_ROOT/downloads/darwin-cache}"
export ROSEMARY_PREFIX_SETUP="${ROSEMARY_PREFIX_SETUP:-download}"
export ROSEMARY_SERVER="${ROSEMARY_SERVER:-off}"

exec "$ROSEMARY_BIN" run "$STUDIO_MCP" --stdio "$@"
