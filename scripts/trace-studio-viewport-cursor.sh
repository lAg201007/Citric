#!/usr/bin/env bash
# Trace the mouse event from Qt's Cocoa platform plugin into Qt event delivery.
set -euo pipefail
umask 077

CITRIC_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
TRACE_NAME="viewport-cursor-$(date +%Y%m%dT%H%M%S)-$$"
EVENT_TRACE="$CITRIC_ROOT/logs/$TRACE_NAME.events.log"

mkdir -p "$CITRIC_ROOT/logs"
(set -o noclobber; : > "$EVENT_TRACE")

# These are imports used by the bundled Qt 5 Cocoa plugin and QtGui. Rosemary's
# call tracer reports the receiver/object pointers and return values. Keep the
# list narrow so ordinary UI activity does not turn this into a full input log.
export ROSEMARY_TRACE_CALL='_ZN22QWindowSystemInterface16handleMouseEventINS_15DefaultDeliveryEEEbP7QWindowmRK7QPointFS6_6QFlagsIN2Qt11MouseButtonEES9_N6QEvent4TypeES7_INS8_16KeyboardModifierEENS8_16MouseEventSourceE,_ZN22QWindowSystemInterface16handleMouseEventINS_15DefaultDeliveryEEEbP7QWindowRK7QPointFS6_6QFlagsIN2Qt11MouseButtonEES9_N6QEvent4TypeES7_INS8_16KeyboardModifierEENS8_16MouseEventSourceE,_ZN16QCoreApplication9sendEventEP7QObjectP6QEvent'

# The previous capture established that QNSView keeps receiving mouse moves.
# Record only the right-button boundary here so the next trace stays small.
export ROSEMARY_OBJC_TRACE_LOG="$EVENT_TRACE"
export ROSEMARY_OBJC_TRACE_SELECTORS='rightMouseDown:,rightMouseUp:'

export STUDIO_LOG_NAME="$TRACE_NAME"
printf 'Qt event trace: %s\nCocoa correlation trace: %s\n' \
    "$CITRIC_ROOT/logs/$TRACE_NAME.log" "$EVENT_TRACE"
exec "$CITRIC_ROOT/scripts/run-studio.sh" "$@"
