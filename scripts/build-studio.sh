#!/usr/bin/env bash
set -euo pipefail

CITRIC_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PATCH_DIR="$CITRIC_ROOT/patches"
UPSTREAM_URL_FILE="$PATCH_DIR/upstream-url"
BASE_COMMIT_FILE="$PATCH_DIR/base-commit"
SERIES_FILE="$PATCH_DIR/series"
CACHE_ROOT="${CITRIC_CACHE_ROOT:-${XDG_CACHE_HOME:-$HOME/.cache}/citric}"
CITRIC_TARGET_DIR="${CARGO_TARGET_DIR:-$CACHE_ROOT/target}"
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
        printf 'Uso: %s [--check-only|--build-only]\n' "$0"
        exit 0
        ;;
    *)
        printf 'Argumento desconhecido: %s\n' "$1" >&2
        exit 2
        ;;
esac

if [[ ! -f "$UPSTREAM_URL_FILE" || ! -f "$BASE_COMMIT_FILE" || ! -f "$SERIES_FILE" ]]; then
    printf 'Metadados da série de patches incompletos em %s\n' "$PATCH_DIR" >&2
    exit 2
fi

UPSTREAM_URL="$(tr -d '\r\n' < "$UPSTREAM_URL_FILE")"
UPSTREAM_URL="${CITRIC_ROSEMARY_REPOSITORY:-$UPSTREAM_URL}"
BASE_COMMIT="$(tr -d '\r\n' < "$BASE_COMMIT_FILE")"

if [[ -z "$UPSTREAM_URL" || ! "$BASE_COMMIT" =~ ^[0-9a-f]{40}$ ]]; then
    printf 'URL do upstream ou commit-base inválido.\n' >&2
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
    printf 'O upstream retornou %s, mas Citric exige %s.\n' "$ACTUAL_BASE" "$BASE_COMMIT" >&2
    exit 2
fi

PATCH_COUNT=0
while IFS= read -r PATCH_NAME || [[ -n "$PATCH_NAME" ]]; do
    if [[ -z "$PATCH_NAME" ]]; then
        continue
    fi
    if [[ "$PATCH_NAME" == */* || "$PATCH_NAME" == *".."* || ! "$PATCH_NAME" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*\.patch$ ]]; then
        printf 'Nome de patch inválido na série: %s\n' "$PATCH_NAME" >&2
        exit 2
    fi
    PATCH_PATH="$PATCH_DIR/$PATCH_NAME"
    if [[ ! -f "$PATCH_PATH" ]]; then
        printf 'Patch listado não encontrado: %s\n' "$PATCH_PATH" >&2
        exit 2
    fi
    git -C "$SOURCE_DIR" apply --check "$PATCH_PATH"
    git -C "$SOURCE_DIR" apply "$PATCH_PATH"
    PATCH_COUNT=$((PATCH_COUNT + 1))
done < "$SERIES_FILE"

if (( PATCH_COUNT == 0 )); then
    printf 'A série de patches está vazia.\n' >&2
    exit 2
fi

if (( CHECK_ONLY == 1 )); then
    printf 'Base %s obtida; %s patch(es) aplicados com sucesso.\n' "$BASE_COMMIT" "$PATCH_COUNT"
    exit 0
fi

CARGO_TARGET_DIR="$CITRIC_TARGET_DIR" cargo build --manifest-path "$SOURCE_DIR/Cargo.toml" --locked --release -p rosemary
BUILT_ROSEMARY="$CITRIC_TARGET_DIR/release/rosemary"
if [[ ! -x "$BUILT_ROSEMARY" ]]; then
    printf 'Cargo terminou sem gerar o executável esperado: %s\n' "$BUILT_ROSEMARY" >&2
    exit 1
fi

if (( BUILD_ONLY == 1 )); then
    printf 'Rosemary compilado em %s; o binário local não foi substituído.\n' "$BUILT_ROSEMARY"
    exit 0
fi

mkdir -p "$CITRIC_ROOT/bin"
OUTPUT_TEMP="$(mktemp "$CITRIC_ROOT/bin/.rosemary.XXXXXXXX")"
cp -- "$BUILT_ROSEMARY" "$OUTPUT_TEMP"
chmod 0755 "$OUTPUT_TEMP"
mv -f -- "$OUTPUT_TEMP" "$CITRIC_ROOT/bin/rosemary"
OUTPUT_TEMP=""

printf 'Rosemary compilado e instalado em %s/bin/rosemary\n' "$CITRIC_ROOT"
