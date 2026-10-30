#!/usr/bin/env bash
set -euo pipefail

CITRIC_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PATCH_DIR="$CITRIC_ROOT/patches"
UPSTREAM_URL_FILE="$PATCH_DIR/upstream-url"
BASE_COMMIT_FILE="$PATCH_DIR/base-commit"
SERIES_FILE="$PATCH_DIR/series"
CACHE_ROOT="${CITRIC_CACHE_ROOT:-${XDG_CACHE_HOME:-$HOME/.cache}/citric}"
NO_PATCHES="${CITRIC_ROSEMARY_NO_PATCHES:-0}"
case "$NO_PATCHES" in
    0) OUTPUT_NAME="rosemary" ;;
    1)
        CACHE_ROOT="$CACHE_ROOT/no-patches"
        OUTPUT_NAME="rosemary-unpatched"
        ;;
    *) printf 'CITRIC_ROSEMARY_NO_PATCHES must be 0 or 1.\n' >&2; exit 2 ;;
esac
if [[ "$NO_PATCHES" == 1 && -n "${CARGO_TARGET_DIR:-}" ]]; then
    CITRIC_TARGET_DIR="$CARGO_TARGET_DIR/no-patches"
else
    CITRIC_TARGET_DIR="${CARGO_TARGET_DIR:-$CACHE_ROOT/target}"
fi
CHECK_ONLY=0
BUILD_ONLY=0

case "${1:-}" in
    "")
        ;;
    --check-only)
        CHECK_ONLY=1
        ;;
    --build-only)
        BUILD_ONLY=1
        ;;
    --help|-h)
        printf 'Usage: %s [--check-only|--build-only]\n' "$0"
        printf 'Set CITRIC_ROSEMARY_NO_PATCHES=1 to build the pinned base without patches/series.\n'
        exit 0
        ;;
    *)
        printf 'Unknown argument: %s\n' "$1" >&2
        exit 2
        ;;
esac

if [[ ! -f "$UPSTREAM_URL_FILE" || ! -f "$BASE_COMMIT_FILE" || ! -f "$SERIES_FILE" ]]; then
    printf 'Incomplete patch series metadata in %s\n' "$PATCH_DIR" >&2
    exit 2
fi

UPSTREAM_URL="$(tr -d '\r\n' < "$UPSTREAM_URL_FILE")"
UPSTREAM_URL="${CITRIC_ROSEMARY_REPOSITORY:-$UPSTREAM_URL}"
BASE_COMMIT="$(tr -d '\r\n' < "$BASE_COMMIT_FILE")"

if [[ -z "$UPSTREAM_URL" || ! "$BASE_COMMIT" =~ ^[0-9a-f]{40}$ ]]; then
    printf 'Invalid upstream URL or base commit.\n' >&2
    exit 2
fi

mkdir -p "$CACHE_ROOT" "$CITRIC_TARGET_DIR"
WORK_DIR="$(mktemp -d "$CACHE_ROOT/rosemary-source.XXXXXXXX")"
OUTPUT_TEMP=""

cleanup() {
    rm -rf -- "$WORK_DIR"
    if [[ -n "$OUTPUT_TEMP" ]]; then
        rm -f -- "$OUTPUT_TEMP"
    fi
}
trap cleanup EXIT

SOURCE_DIR="$WORK_DIR/source"
git init --quiet "$SOURCE_DIR"
git -C "$SOURCE_DIR" fetch --quiet --depth=1 --no-tags "$UPSTREAM_URL" "$BASE_COMMIT"
git -C "$SOURCE_DIR" checkout --quiet --detach FETCH_HEAD

ACTUAL_BASE="$(git -C "$SOURCE_DIR" rev-parse HEAD)"
if [[ "$ACTUAL_BASE" != "$BASE_COMMIT" ]]; then
    printf 'Upstream returned %s, but Citric requires %s.\n' "$ACTUAL_BASE" "$BASE_COMMIT" >&2
    exit 2
fi

PATCH_COUNT=0
if [[ "$NO_PATCHES" == 0 ]]; then
    while IFS= read -r PATCH_NAME || [[ -n "$PATCH_NAME" ]]; do
        if [[ -z "$PATCH_NAME" ]]; then
            continue
        fi
        if [[ "$PATCH_NAME" == */* || "$PATCH_NAME" == *".."* || ! "$PATCH_NAME" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*\.patch$ ]]; then
            printf 'Invalid patch name in series: %s\n' "$PATCH_NAME" >&2
            exit 2
        fi
        PATCH_PATH="$PATCH_DIR/$PATCH_NAME"
        if [[ ! -f "$PATCH_PATH" ]]; then
            printf 'Listed patch not found: %s\n' "$PATCH_PATH" >&2
            exit 2
        fi
        git -C "$SOURCE_DIR" apply --check "$PATCH_PATH"
        git -C "$SOURCE_DIR" apply "$PATCH_PATH"
        PATCH_COUNT=$((PATCH_COUNT + 1))
    done < "$SERIES_FILE"
fi

if (( PATCH_COUNT == 0 && NO_PATCHES == 0 )); then
    printf 'The patch series is empty.\n' >&2
    exit 2
fi

if (( CHECK_ONLY == 1 )); then
    if [[ "$NO_PATCHES" == 1 ]]; then
        printf 'Base %s fetched with no Citric patch series applied.\n' "$BASE_COMMIT"
    else
        printf 'Base %s fetched; %s patch(es) applied successfully.\n' "$BASE_COMMIT" "$PATCH_COUNT"
    fi
    exit 0
fi

CARGO_TARGET_DIR="$CITRIC_TARGET_DIR" cargo build --manifest-path "$SOURCE_DIR/Cargo.toml" --locked --release -p rosemary
BUILT_ROSEMARY="$CITRIC_TARGET_DIR/release/rosemary"
if [[ ! -x "$BUILT_ROSEMARY" ]]; then
    printf 'Cargo finished without producing the expected executable: %s\n' "$BUILT_ROSEMARY" >&2
    exit 1
fi

if (( BUILD_ONLY == 1 )); then
    printf 'Rosemary built at %s; the local binary was not replaced.\n' "$BUILT_ROSEMARY"
    exit 0
fi

mkdir -p "$CITRIC_ROOT/bin"
OUTPUT_TEMP="$(mktemp "$CITRIC_ROOT/bin/.$OUTPUT_NAME.XXXXXXXX")"
cp -- "$BUILT_ROSEMARY" "$OUTPUT_TEMP"
chmod 0755 "$OUTPUT_TEMP"
mv -f -- "$OUTPUT_TEMP" "$CITRIC_ROOT/bin/$OUTPUT_NAME"
OUTPUT_TEMP=""

printf 'Rosemary built and installed at %s/bin/%s\n' "$CITRIC_ROOT" "$OUTPUT_NAME"
