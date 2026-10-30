#!/usr/bin/env bash
# Capture one user-driven pointer reproduction without enabling memory tracing.
set -euo pipefail
umask 077
CITRIC_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$CITRIC_ROOT/logs"
TRACE_PATH="$CITRIC_ROOT/logs/mouse-input-$(date +%Y%m%dT%H%M%S)-$$.log"
(set -o noclobber; : > "$TRACE_PATH")
export ROSEMARY_INPUT_TRACE=1
export ROSEMARY_EVENT_LOG="$TRACE_PATH"
# Record selected native calls inside each AppKit event's existing trace span.
# Unlike Qt's own message handler, this does not depend on Studio log policy.
export ROSEMARY_OBJC_TRACE_LOG="$TRACE_PATH"
export ROSEMARY_OBJC_TRACE_SELECTORS='mouseMovedImpl:,handleMouseEvent:,isTransparentForUserInput,convertFromScreen:toWindowPoint:andScreenPoint:'
# Guest-side Qt logging distinguishes native tracking callbacks from mouse
# events accepted by the Cocoa platform plugin. Preserve unrelated rules.
export QT_LOGGING_RULES="${QT_LOGGING_RULES:+${QT_LOGGING_RULES};}qt.qpa.input.mouse=true;qt.qpa.window=true"
if [[ -z "${QT_MESSAGE_PATTERN:-}" ]]; then
    QT_MESSAGE_PATTERN='[%{time process}] %{category}: %{message}'
fi
export QT_MESSAGE_PATTERN
if [[ -n "${ROSEMARY_ENVIRON:-}" ]]; then
    ROSEMARY_ENVIRON+=$'\n'
fi
ROSEMARY_ENVIRON+=$'QT_LOGGING_RULES\nQT_MESSAGE_PATTERN'
export ROSEMARY_ENVIRON
printf 'Input trace: %s\n' "$TRACE_PATH"
exec "$CITRIC_ROOT/scripts/citric" launch "$@"
